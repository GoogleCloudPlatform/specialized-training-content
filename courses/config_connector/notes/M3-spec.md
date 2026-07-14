<!-- =====================================================================
  Deploying and Using Config Connector with GKE
  Reference notes for instructors & students
===================================================================== -->

![Deploying and Using Config Connector with GKE](_assets/course-banner.png)

# M3 - Spec and Schemas

The `spec` section is where you define **many, though not all, of the parameters
that configure the object under management**—its settings, the project and
location it lives in, references to other resources, and any secrets it needs.
Some configuration lives elsewhere: identity and KCC's operational controls sit
in `metadata` (see [M3 - Metadata](M3-metadata.md)), and some behavior is left to
Google Cloud's own server-side defaults rather than expressed in `spec` at all.

The notes below cover the fields and patterns you'll use most, and—just as
important—where the schema will catch a mistake for you and where it won't.

---

## Things controlled via `spec`

### 1. `spec.resourceID` sets the Google Cloud name independently of `metadata.name`

The Kubernetes object name and the Google Cloud resource name are separate.
`spec.resourceID` is **optional**; if you omit it, it **defaults to
`metadata.name`**:

```yaml
metadata:
  name: my-topic-object       # the K8s object name
spec:
  resourceID: prod-events     # the actual Pub/Sub topic name in Google Cloud (optional)
```

Two reasons to set it: (a) your desired Google Cloud name isn't a valid K8s name, or (b)
you want to **acquire an existing** Google Cloud resource—set `resourceID` to its ID
and KCC adopts it instead of creating a new one. It is **immutable** once set
(see #9). This is the `spec` half of the naming story from
[M3 - Metadata](M3-metadata.md).

### 2. The location field's *name* varies by resource—always check

There is no single `location` convention. Region/zone/global is spelled
differently per resource, and guessing wrong is a common authoring error:

| Resource | Field |
|---|---|
| StorageBucket | `spec.location` (defaults to `US`) |
| SQLInstance | `spec.region` |
| RedisInstance | `spec.region` (required) + `spec.locationId` (zone) |
| ComputeInstance | `spec.zone` |

Global vs regional is expressed by the **value** (`location: US` vs `location:
us-central1`) and sometimes by which field exists at all. Whatever it's called,
it's **immutable** (see #9), so pick it carefully the first time.

### 3. Reference another resource with `*Ref`—by `name` or by `external`

Whenever a field points at another Google Cloud resource (a network, a KMS key, a
project), it's a `*Ref` object with two mutually-exclusive ways to fill it in:

```yaml
spec:
  networkRef:
    name: my-network        # a ComputeNetwork object you manage in this cluster
  # --- OR ---
  networkRef:
    external: projects/my-project/global/networks/my-network   # a literal Google Cloud ID
```

- **`name`** (+ optional `namespace`) points at another KCC object. KCC resolves
  it and **waits for it to be ready** before creating yours. Use this when KCC
  manages both.
- **`external`** is the literal Google Cloud identifier (Cloud Asset Inventory format, no
  service domain). Use this to reference something KCC doesn't manage.

Set **one, not both**—the CRD enforces this as a `oneOf`. Ref struct defined in
[`apis/refs/project_reference.go`](https://github.com/GoogleCloudPlatform/k8s-config-connector/blob/master/apis/refs/project_reference.go#L34).

### 4. Tell KCC which project with `spec.projectRef` (or fall back to the namespace)

Same `name`/`external` choice as any ref
([`apis/refs/v1beta1/projectref.go`](https://github.com/GoogleCloudPlatform/k8s-config-connector/blob/master/apis/refs/v1beta1/projectref.go)):

```yaml
spec:
  projectRef:
    external: my-project-id      # or "projects/my-project-id"
    # or: name: my-managed-project
```

> **Gotcha:** not every resource has `spec.projectRef`. Several common ones—
> `StorageBucket`, `PubSubTopic`, `ComputeInstance`, `SQLInstance`—don't expose
> it at all, and instead take their project from the `cnrm.cloud.google.com/project-id`
> annotation. KCC looks for that annotation **on the object first, then on the
> object's namespace**, and finally falls back to the namespace name (see
> [M3 - Metadata](M3-metadata.md)). Resources that *do* expose `projectRef`
> (e.g. `IAMDenyPolicy`, `StorageFolder`, `ComputeNodeGroup`) still honor the
> same annotation fallback when the field is left unset. Either way, if KCC can't
> determine a project from any source, the resource errors with *"cannot find
> project id."*

For non-project parents there are sibling refs: `folderRef` (`external:
folders/123…`) and `organizationRef` (`external: organizations/123…` only —
there is no Organization CRD to name).

### 5. Supply secrets with `valueFrom.secretKeyRef`, never inline plaintext

When a field holds a sensitive value—a database password, an encryption key—you
don't put the literal string in your manifest. Instead you store the secret
in an ordinary Kubernetes `Secret` object, and the `spec` field points at it by
name and key. That way the secret never lives in the resource YAML you commit or
apply.

These fields aren't plain strings; they're a small nested object that names a
Secret and a key within it. The secret value is created and managed separately—it
never appears in the resource manifest. For example, put the password into a
Secret with no YAML at all:

```bash
kubectl create secret generic sql-root-password \
  --from-literal=password='sup3r-s3cret'
```

Then `SQLInstance.spec.rootPassword`
([`apis/sql/v1beta1/instance_types.go`](https://github.com/GoogleCloudPlatform/k8s-config-connector/blob/master/apis/sql/v1beta1/instance_types.go#L490))
points at it — the manifest you commit contains only a reference:

```yaml
apiVersion: sql.cnrm.cloud.google.com/v1beta1
kind: SQLInstance
metadata:
  name: my-db
spec:
  # ...
  rootPassword:
    valueFrom:
      secretKeyRef:
        name: sql-root-password  # which Secret (in the same namespace)
        key: password            # which key inside it
```

The field technically also accepts an inline `value:` (e.g.
`rootPassword.value: sup3r-s3cret`), but that puts the secret right back into the
manifest — so use `valueFrom.secretKeyRef` for anything real. Two rules to
remember: you may set `value` **or** `valueFrom`, never both (KCC errors *"only
one of …value and …valueFrom should be configured"*), and if the referenced
Secret or key is missing you get a **SecretNotFound** error and the resource
won't reconcile.

### 6. Some string fields only accept a fixed set of values (enums)

Newer resources constrain string fields to an allowed list, enforced by the API
server **at apply time**—a wrong value is rejected immediately, before any Google Cloud
call. Example, MetastoreService
([`apis/metastore/v1alpha1/metastoreservice_types.go`](https://github.com/GoogleCloudPlatform/k8s-config-connector/blob/master/apis/metastore/v1alpha1/metastoreservice_types.go#L114)):

The allowed values live in the CRD's OpenAPI schema as an `enum` list. In the
`MetastoreService` CRD, the `spec.tier` field is defined like this
([`...metastoreservices...yaml`](https://github.com/GoogleCloudPlatform/k8s-config-connector/blob/master/config/crds/resources/apiextensions.k8s.io_v1_customresourcedefinition_metastoreservices.metastore.cnrm.cloud.google.com.yaml#L351)):

```yaml
tier:
  description: The tier of the service.
  enum:
  - DEVELOPER
  - ENTERPRISE
  type: string
```

Apply a manifest with `spec.tier: PREMIUM` and the API server rejects it
outright — `Unsupported value: "PREMIUM": supported values: "DEVELOPER",
"ENTERPRISE"`—before KCC ever calls Google Cloud.

### 7. Most fields you omit are defaulted by *Google Cloud*, not by KCC

KCC deliberately does **not** fill in most optional fields — it omits them and
lets the Google API apply its own server-side default
([`validations.md`](https://github.com/GoogleCloudPlatform/k8s-config-connector/blob/master/docs/develop-resources/api-conventions/validations.md)).
So "what happens if I leave this out?" is usually answered by the Google Cloud docs, not
the KCC schema.

The exceptions—where the **schema** fills a value in for you—are rare and
mostly in Storage:

- `StorageBucket.spec.location` defaults to `US`
  ([`storagebucket_types.go`](https://github.com/GoogleCloudPlatform/k8s-config-connector/blob/master/apis/storage/v1beta1/storagebucket_types.go#L62),
  `+kubebuilder:default=US`). Omit it and you get a US multi-region bucket.
- `spec.resourceID` defaults to `metadata.name` (see #1).
- Project defaults from the namespace (see #4).

Practical rule: for an omitted field, the default is Google Cloud's, and you won't see it
in the KCC schema or CRD — check the Google Cloud resource's own documentation to know
what value you'll actually get.

### 8. Format constraints (`pattern`, `maxLength`) are validated at apply time

Where they exist, regex `pattern` and `maxLength` constraints reject bad input
immediately. The most common one students hit is the IAM role format
([`apis/iam/v1beta1/policymember_types.go`](https://github.com/GoogleCloudPlatform/k8s-config-connector/blob/master/apis/iam/v1beta1/policymember_types.go#L44)):

```go
// +kubebuilder:validation:Pattern=^((projects|organizations)/[^/]+/)?roles/[\w_\.]+$
Role string `json:"role"`
```

A malformed `role:` value fails at `kubectl apply`. Numeric bounds
(`Minimum`/`Maximum`) and item counts are essentially unused on Google Cloud resources—so
don't expect numeric range checks in the schema; those, again, come from Google Cloud
at reconcile time.

### 9. Immutable fields make `kubectl apply` *fail*—Google Cloud won't be recreated

Many fields can't change after creation. If you try, a KCC validating webhook
rejects the update with a 403 and a message like:

> `cannot make changes to immutable field(s): [spec.location]; please refer to our troubleshooting doc: …`

([`pkg/webhook/immutable_fields_validator.go`](https://github.com/GoogleCloudPlatform/k8s-config-connector/blob/master/pkg/webhook/immutable_fields_validator.go)).
Your `apply` fails and the resource is left untouched—unlike Terraform, KCC
will **not** silently destroy and recreate the resource. Reliably-immutable
fields to plan around:

- **`spec.resourceID`** – always.
- **`spec.location`** (and `region`/`zone`) – it's part of the Google Cloud URL, so it
  can't move.
- **Parent references** like `projectRef`.

On newer resources these are marked right in the schema (e.g., every
IAMPolicyMember field—`resourceRef`, `member`, `role`, `condition`—is
individually immutable,
[`policymember_types.go`](https://github.com/GoogleCloudPlatform/k8s-config-connector/blob/master/apis/iam/v1beta1/policymember_types.go#L29)).
Design your manifests knowing these are "set once."

### 10. Practical gotchas worth memorizing

- **`member` vs `memberFrom` (don't hardcode identities).** IAM bindings let you
  write a literal `member: "serviceAccount:foo@…"` **or** a `memberFrom` that
  references another resource and pulls its identity from status
  ([`partialpolicy_types.go`](https://github.com/GoogleCloudPlatform/k8s-config-connector/blob/master/apis/iam/v1beta1/partialpolicy_types.go#L57)).
  Prefer `memberFrom` with a `serviceAccountRef` over pasting an email.
- **Deprecated fields still appear in the schema.** You'll see fields you
  shouldn't use, e.g., `StorageBucket.spec.bucketPolicyOnly` (use
  `uniformBucketLevelAccess` instead) and `ComputeInstance…networkIp` (use
  `networkIpRef`). The doc comment / `kubectl explain` will say "DEPRECATED."
- **Re-send full lists.** Kubernetes treats a list of objects as atomic;
  re-applying a partial list (e.g., IAM `bindings`) can drop entries. Always
  apply the complete list you want.
- **`apiVersion` (alpha vs beta) changes what's available.** Newer resources
  land as `v1alpha1` first, and only the newer "direct" ones carry the strong
  apply-time validation and `projectRef`. If a field or a validation you expect
  isn't there, check whether you're on the right version.
- **"Required" is defined by the CRD, not the Go/JSON tag.** Trust `kubectl
  explain <kind>.spec` (or the CRD's `required:` list) for what you must set.

---

## Fast ways to check a schema yourself

```bash
kubectl explain sqlinstance.spec.region          # description, type, required-ness
kubectl explain sqlinstance.spec --recursive     # whole spec tree
kubectl get crd sqlinstances.sql.cnrm.cloud.google.com -o yaml   # enums, patterns, oneOf, defaults
```

---

> [!NOTE]
> **Not all Config Connector resources are built the same way**, and that
> changes how much the schema protects you.
>
> Many resources—`StorageBucket`, `PubSubTopic`, `ComputeInstance`,
> `SQLInstance`, `ContainerCluster`—are older, generated with Terraform/DCL
> providers, and carry **very few** built-in validations. Many wrong values on
> those resources aren't caught at `kubectl apply` time; they fail later at the
> Google Cloud API and show up as an error in `status`. Newer "direct" resources (many
> IAM types, GKEHub, newer Storage subtypes) validate much more at apply time.
> Knowing which you're holding tells you where your mistakes will surface.
