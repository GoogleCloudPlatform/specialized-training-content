<!-- =====================================================================
  Deploying and Using Config Connector with GKE
  Reference notes for instructors & students
===================================================================== -->

![Deploying and Using Config Connector with GKE](_assets/course-banner.png)

# M3 - Status

The `status` section is the half of the object you **read, but never write**.
Where `spec` is your desired state (see [M3 - Spec & Schemas](M3-spec.md)) and
`metadata` can affect location, name, management, etc. (see [M3 - Metadata](M3-metadata.md)),
`status` is the controller's report back to you: whether the resource
reconciled, why it is or isn't, and what values GCP actually assigned to your resource. Config
Connector owns this section entirely — it overwrites it on every reconcile,
so any edit you make there is discarded.

`status` is a Kubernetes **subresource**, which is why `kubectl apply` never
touches it and why your `spec` changes bump `metadata.generation` but a
controller writing `status` does not. Treat it as a read-only dashboard: it's
how you (and any automation) tell whether the GCP world matches your manifest
yet.

The notes below cover the fields you'll actually look at and how to use them.

---

## Things to know about `status`

### 1. The `Ready` condition is the one signal that matters most

Every Config Connector resource reports a `status.conditions` list, and the condition with
`type: Ready` is the source of truth for "did this work?" Each condition carries
`type`, `status` (`True` / `False` / `Unknown`), a one-word CamelCase `reason`,
a human `message`, and a `lastTransitionTime`
([`pkg/apis/k8s/v1alpha1/condition_types.go`](https://github.com/GoogleCloudPlatform/k8s-config-connector/blob/master/pkg/apis/k8s/v1alpha1/condition_types.go#L31)).

```yaml
status:
  conditions:
  - type: Ready
    status: "True"
    reason: UpToDate
    message: The resource is up to date.
    lastTransitionTime: "2026-07-03T18:20:11Z"
```

The `reason` tells you *which* state you're in — the common ones
([`docs/designs/reconcile-status.md`](https://github.com/GoogleCloudPlatform/k8s-config-connector/blob/master/docs/designs/reconcile-status.md)):

| `status` | `reason` | Meaning |
|---|---|---|
| `True` | `UpToDate` | Reconciled; GCP matches your `spec`. |
| `False` | `Updating` | A change is in flight (GCP call running). |
| `False` | `UpdateFailure` | The GCP call failed — read `message` for why. |
| `False` | `DependencyNotReady` | A referenced resource isn't ready yet. |

The `message` is where the actual GCP error text lands — it's the first thing to
read when a resource is stuck.

### 2. `observedGeneration` tells you if status is *current*

A stale `status` is a trap: a resource can show `Ready: True` from a *previous*
reconcile while your latest `spec` change hasn't been applied yet.
`status.observedGeneration` is how you tell the difference — it's the
`metadata.generation` the controller last acted on
([`apigeeenvgroup_types.go`](https://github.com/GoogleCloudPlatform/k8s-config-connector/blob/master/apis/apigee/v1beta1/apigeeenvgroup_types.go#L45)).

The rule: **`status.observedGeneration == metadata.generation` means the status
reflects your current spec.** If `observedGeneration` is behind, the controller
hasn't caught up — don't trust `Ready` yet. This is the correct thing to gate
automation on, not `Ready` alone.

```bash
kubectl get sqlinstance my-db \
  -o jsonpath='{.metadata.generation} vs {.status.observedGeneration}'
```

### 3. `observedState` gives you the values GCP actually assigned

Output-only fields — server-generated IDs, IP addresses, timestamps, computed
endpoints — don't belong in `spec` (you didn't ask for them), so Config Connector surfaces
them under `status.observedState`. This is where you read back what GCP decided:

```yaml
status:
  observedState:
    createdAt: "1719874811000"
    state: ACTIVE
```

This is the clean way to **consume a resource's real attributes** — e.g. an
allocated IP or a generated connection name — rather than guessing them. Not
every resource populates it; older Terraform/DCL-based resources often expose
such fields directly under `status` instead of a nested `observedState`.

### 4. `status.externalRef` is the durable link to the GCP resource

For newer "direct" resources, `status.externalRef` holds the fully-qualified GCP
identifier Config Connector uses to find, update, and delete the resource — it's assigned when
the object is first created or acquired. You don't set it, but it's worth knowing
it exists: it's how Config Connector remembers *which* GCP resource this object owns, which
matters for acquisition and for understanding drift. If you're debugging whether
two objects point at the same GCP resource, this is the field to compare.

### 5. `kubectl get` already surfaces the important bits

You rarely need to dig into the YAML. KCC defines printer columns that pull
straight from the `Ready` condition
([sqlinstance CRD](https://github.com/GoogleCloudPlatform/k8s-config-connector/blob/master/config/crds/resources/apiextensions.k8s.io_v1_customresourcedefinition_sqlinstances.sql.cnrm.cloud.google.com.yaml#L29)),
so a plain `get` tells you the state at a glance:

```bash
$ kubectl get sqlinstance
NAME    AGE   READY   STATUS       STATUS AGE
my-db   5m    True    UpToDate     4m
```

- **READY** = `status.conditions[Ready].status`
- **STATUS** = its `reason`
- **STATUS AGE** = its `lastTransitionTime`

For anything deeper, `kubectl describe` prints the full condition list including
the `message`, and `kubectl wait` can block on it directly:

```bash
kubectl wait --for=condition=Ready sqlinstance/my-db --timeout=600s
```

---

## Practical strategies

- **Read `message` first when stuck** — the GCP error text lives there; the
  `reason` only categorizes it.
- **`kubectl wait --for=condition=Ready`** is the scriptable way to block until a
  resource is done, instead of polling YAML.
