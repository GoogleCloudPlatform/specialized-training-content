<!-- =====================================================================
  Deploying and Using Config Connector with GKE
  Reference notes for instructors & students
===================================================================== -->

![Deploying and Using Config Connector with GKE](_assets/course-banner.png)

# M3 - Metadata

Every Config Connector (KCC) resource is a standard Kubernetes object, so it has
the usual top-level fields: `apiVersion`, `kind`, `metadata`, `spec` (and
`status` at runtime). A surprising amount of KCC behavior is driven not by
`spec` but by **annotations and labels inside `metadata`**.

Most of the annotation/label names below are taken from the KCC source of truth,
[`pkg/k8s/constants.go`](https://github.com/GoogleCloudPlatform/k8s-config-connector/blob/master/pkg/k8s/constants.go)
(where they are built through `FormatAnnotation("...")`). A few live elsewhere—notably the management-conflict prevention policy, defined as a hardcoded string
literal in
[`pkg/managementconflict/annotations.go`](https://github.com/GoogleCloudPlatform/k8s-config-connector/blob/master/pkg/managementconflict/annotations.go).

---

## Things controlled via `metadata`

### 1. Google Cloud resource identity – which cloud resource this maps to

**By default, `metadata.name` *is* the Google Cloud resource's name.** If you set nothing
else, KCC uses the object's Kubernetes name as the ID (or `name`) of the Google Cloud
resource it creates. In the simplest case the two are the same string:

```yaml
metadata:
  name: my-database      # ← also becomes the Firestore database's ID in Google Cloud
```

**When `metadata.name` can't be the Google Cloud name.** Kubernetes object names are
restricted—lowercase RFC-1123 (letters, digits, `-`, `.`), max 253 chars.
Many Google Cloud resources allow names that violate those rules: uppercase letters,
underscores, spaces, characters, or simply names longer than K8s permits. When
the desired Google Cloud name isn't a legal K8s name, you can't express it through
`metadata.name` at all.

**Best practice—decouple the two names.** Rather than forcing the K8s object
name to match Google Cloud, give the object a clean K8s-friendly `metadata.name` and
specify the real Google Cloud identifier separately. Decoupling also lets you **acquire
(adopt)** a pre-existing Google Cloud resource: point a new K8s object at an ID that
already exists, and KCC manages it instead of creating a new one.

**Two mechanisms—and which one to use.** The identifier lives in two possible
places, and this is the historical progression:

- **Original: the `cnrm.cloud.google.com/resource-id` annotation** (in
  `metadata`). This was the first mechanism and still works.
- **Preferred today: the `spec.resourceID` field.** KCC now reads
  `spec.resourceID` and, when unset, falls back to `metadata.name`—see the
  canonical fallback at
  [`pkg/resourceoverrides/privateca_capool.go:97`](https://github.com/GoogleCloudPlatform/k8s-config-connector/blob/master/pkg/resourceoverrides/privateca_capool.go#L97)
  (`spec.resourceID` if present, else `r.GetName()`). The generated API docs
  state it uniformly: *"Optional. Used for creation and acquisition. When unset,
  the value of `metadata.name` is used as the default. Immutable."*

```yaml
metadata:
  name: my-database                 # clean K8s name
spec:
  resourceID: "My_Actual_Google_Cloud_Name"  # the real Google Cloud identifier (preferred field)
```

> **Immutable:** once the resource is created, `spec.resourceID` (and the
> annotation) can't be changed—it identifies a specific Google Cloud resource for the
> object's lifetime. Prefer `spec.resourceID` for new manifests; treat the
> annotation as legacy.

### 2. Labels – Kubernetes metadata that may also reach Google Cloud

`metadata.labels` behave a little differently in KCC than on a typical Kubernetes
object, because a label can live in **two places**: on the Kubernetes object, and
(often) on the Google Cloud resource itself. It's worth knowing which is which.

#### Standard Kubernetes labels

Any label you put in `metadata.labels` works exactly as it does for any
Kubernetes object—it's available for `kubectl` selection, grouping, and
tooling, regardless of what Google Cloud does with it.

```yaml
metadata:
  name: my-bucket
  labels:
    team: platform
    env: prod
```

```bash
kubectl get storagebucket -l team=platform
```

#### Labels that become labels on the Google Cloud resource

For most labelable resources, KCC **copies `metadata.labels` onto the actual Google Cloud
resource's labels**. So the `team: platform` above shows up as a label on the
Cloud Storage bucket in Google Cloud, not just on the K8s object. The propagation runs
through
[`NewGCPLabelsFromK8sLabels`](https://github.com/GoogleCloudPlatform/k8s-config-connector/blob/master/pkg/label/label.go#L44).

Two things happen during that copy:

- **Prefixed labels are stripped.** Any label key containing a `/`—the
  KRM-style `prefix/name` form, such as `cnrm.cloud.google.com/…` or
  `app.kubernetes.io/name`—is **not** sent to Google Cloud
  ([`removeLabelsWithKRMPrefix`](https://github.com/GoogleCloudPlatform/k8s-config-connector/blob/master/pkg/label/label.go#L56)).
  Only plain keys (`team`, `env`) propagate. This is intentional: those prefixed
  labels are Kubernetes-domain metadata that Google Cloud has no use for.
- **KCC adds its own management label.** Every Google Cloud resource KCC manages gets
  `managed-by-cnrm: "true"` stamped on it
  ([`pkg/label/const.go`](https://github.com/GoogleCloudPlatform/k8s-config-connector/blob/master/pkg/label/const.go#L17)).
  You'll see it on the cloud resource even if you set no labels of your own—it's
  how you can tell in the Google Cloud console which resources are under Config
  Connector's control.

#### Labels Config Connector puts on the *Kubernetes* object

Separately, every KCC custom resource is stamped with `cnrm.cloud.google.com/…`
labels that describe the resource type itself—for example, on a StorageBucket:

```yaml
metadata:
  labels:
    cnrm.cloud.google.com/managed-by-kcc: "true"
    cnrm.cloud.google.com/stability-level: stable
    cnrm.cloud.google.com/system: "true"
```

These live **only on the K8s object** (they come from the CRD definition, not
from you) and, being prefixed, are exactly the labels the propagation step above
strips—so they never reach Google Cloud.

#### Not every Google Cloud resource can carry labels

A crucial caveat: **many Google Cloud resources have no labels field at all.** IAM
bindings, Pub/Sub *schemas*, and various hierarchy/project-level resources simply
don't support labels in their API. For those, `metadata.labels` still works as
normal Kubernetes metadata—you can select on it with `kubectl`—but KCC has
nowhere to put it on the Google Cloud side, so it's **silently not propagated**. There's
no error; the labels just stay Kubernetes-only.

> Whether a given resource propagates labels depends on the underlying Google Cloud API,
> not on Config Connector. If you need a label to appear on the cloud resource,
> confirm that resource type actually supports labels—don't assume
> `metadata.labels` always reaches Google Cloud.

### 3. Project / folder / org placement – the container hierarchy

The `ContainerAnnotations` in KCC: `project-id`, `folder-id`,
`organization-id`. A resource is placed into a Google Cloud container via annotation
instead of a `projectRef`.

```yaml
metadata:
  annotations:
    cnrm.cloud.google.com/project-id: "my-google-cloud-project"
    # or cnrm.cloud.google.com/folder-id / organization-id
```

### 4. Deletion behavior—what happens on `kubectl delete`

`cnrm.cloud.google.com/deletion-policy` with values `abandon` or `delete`.
`abandon` removes the Kubernetes object but leaves the Google Cloud resource intact.

```yaml
metadata:
  annotations:
    cnrm.cloud.google.com/deletion-policy: "abandon"
```

### 5. Reconcile frequency—how often KCC re-syncs with Google Cloud

`cnrm.cloud.google.com/reconcile-interval-in-seconds`. Set to `0` to disable
periodic drift correction for a resource.

```yaml
metadata:
  annotations:
    cnrm.cloud.google.com/reconcile-interval-in-seconds: "0"
```

### 6. Management-conflict prevention—who "owns" the resource

`cnrm.cloud.google.com/management-conflict-prevention-policy` (`none` /
`resource`). Uses leasing to stop two KCC instances from fighting over the same
Google Cloud resource. Unlike the other annotations here, this one is *not* defined in
`pkg/k8s/constants.go`; it is a hardcoded string literal (`FullyQualifiedAnnotation`)
in
[`pkg/managementconflict/annotations.go`](https://github.com/GoogleCloudPlatform/k8s-config-connector/blob/master/pkg/managementconflict/annotations.go).

```yaml
metadata:
  annotations:
    cnrm.cloud.google.com/management-conflict-prevention-policy: "resource"
```

### 7. Deletion protection—guarding against accidental destruction

The `cnrm.cloud.google.com/deletion-defender` finalizer, plus resource-specific
guards like `cnrm.cloud.google.com/delete-contents-on-destroy` (e.g., BigQuery
datasets—whether to delete non-empty contents) and `disable-on-destroy`.

```yaml
metadata:
  annotations:
    cnrm.cloud.google.com/delete-contents-on-destroy: "false"
```

### 8. Update semantics for specific resources—allowing disruptive updates

Resource-specific annotations like
`cnrm.cloud.google.com/allow-stopping-for-update` (Compute instances—permit
KCC to stop a VM to apply a field change) and `ignore-warnings`.

```yaml
metadata:
  annotations:
    cnrm.cloud.google.com/allow-stopping-for-update: "true"
```
