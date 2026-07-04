![Deploying and Using Config Connector with GKE](_assets/course-banner.png)

# M2 - Applying the ConfigConnector resource (stage 2)

Stage 1 ([[M2-operator-install]]) installed the operator — a small idle bootstrap.
**Stage 2 turns Config Connector on:** you apply a single **ConfigConnector**
resource, and the operator reacts by deploying the actual controllers and the
Google-resource CRDs into a new `cnrm-system` namespace.

```mermaid
flowchart LR
    U["Platform Engineer"] -->|kubectl apply| CC["ConfigConnector<br/>(configconnector.yaml)"]
    CC --> OP["operator<br/>(already running)"]
    OP -->|deploys| WL["controllers in cnrm-system<br/>+ ~200 Google-resource CRDs"]
```

---

## Some important notes

- **One resource flips the switch.** Applying a ConfigConnector object is the whole
  trigger — the operator watches for it and does the rest.
- **The name is fixed.** `metadata.name` **must** be
  `configconnector.core.cnrm.cloud.google.com` (it's a cluster singleton).
- **`mode` is the big decision:** `cluster` (one identity for everything) or
  `namespaced` (per-namespace identity). This shapes what the operator deploys.

---

## Step 1 — choose a mode and write the manifest

### Cluster mode — one Google Service Account for the whole cluster

```yaml
apiVersion: core.cnrm.cloud.google.com/v1beta1
kind: ConfigConnector
metadata:
  # the only accepted name — this is a singleton
  name: configconnector.core.cnrm.cloud.google.com
spec:
  mode: cluster
  googleServiceAccount: "SERVICE_ACCOUNT_NAME@PROJECT_ID.iam.gserviceaccount.com"
  stateIntoSpec: Absent
```

### Namespaced mode — identity is set per namespace instead

```yaml
apiVersion: core.cnrm.cloud.google.com/v1beta1
kind: ConfigConnector
metadata:
  name: configconnector.core.cnrm.cloud.google.com
spec:
  mode: namespaced
  stateIntoSpec: Absent
```

Note there is **no `googleServiceAccount`** here — in namespaced mode you supply the
identity later, per namespace, via a **ConfigConnectorContext** ([[M2-operator-crds]]):

```yaml
apiVersion: core.cnrm.cloud.google.com/v1beta1
kind: ConfigConnectorContext
metadata:
  name: configconnectorcontext.core.cnrm.cloud.google.com
  namespace: NAMESPACE
spec:
  googleServiceAccount: "NAMESPACE_GSA@HOST_PROJECT_ID.iam.gserviceaccount.com"
  stateIntoSpec: Absent
```

## Step 2 — apply the manfiest

```bash
kubectl apply -f configconnector.yaml
```

## Step 3 — verify the controllers came up

The controller Pod can take **several minutes** to start.

```bash
kubectl wait -n cnrm-system \
  --for=condition=Ready pod \
  -l cnrm.cloud.google.com/component=cnrm-controller-manager
# → pod/cnrm-controller-manager-0 condition met
```

---

## What the apply creates

A single `kubectl apply` of the ConfigConnector object doesn't just start some
pods — the operator lays down a whole set of cluster objects and reconciles all of
it for you. Here's the full inventory, grouped by kind of thing.

### The workloads

The visible part — the controllers that do the work. Each is detailed in
[The workloads in detail](#the-workloads-in-detail) below.

| Workload                       | Kind        | Mode                | Role                          |
| ------------------------------ | ----------- | ------------------- | ----------------------------- |
| `cnrm-controller-manager`      | StatefulSet | both                | the reconcilers — core engine |
| `cnrm-webhook-manager`         | Deployment  | both                | admission webhooks            |
| `cnrm-deletiondefender`        | StatefulSet | both                | guards against deletions      |
| `cnrm-resource-stats-recorder` | Deployment  | both                | resource-count metrics        |
| `cnrm-unmanaged-detector`      | StatefulSet | **namespaced only** | drift signal                  |

Expanded from the source (`cmd/*` + `pkg/controller/*`), so the roles are precise.

### The supporting resources

The plumbing the workloads need — created once, rarely thought about again.

| What's created | Detail |
| -------------- | ------ |
| **The `cnrm-system` namespace** | Every workload, ServiceAccount, and Service lives here. It's created by the operator, not by you — you don't `kubectl create namespace` it. |
| **~212 Google-resource CRDs** | The **StorageBucket**, **ComputeAddress**, **PubSubTopic**, … kinds you'll actually author. These are **not** the operator's own 8 management CRDs ([[M2-operator-crds]]) — they arrive *now*, at this apply, not at operator install. |
| **A ServiceAccount per workload** | One per workload above. The controller's KSA is the one **bound to your Google Service Account via Workload Identity** — the link that lets in-cluster pods authenticate as the GSA from your manifest. |
| **Cluster-wide RBAC** | ClusterRoles + ClusterRoleBindings (and a couple of namespaced Roles/RoleBindings) granting each workload the API access it needs — e.g. the controller's permission to watch every managed-resource CRD across all namespaces. |
| **Services** | `cnrm-controller-manager-service`, `cnrm-resource-stats-recorder-service`, and the webhook Service — stable addresses fronting the pods (the first two are the metrics endpoints, see [[M4-monitoring]]). |
| **Webhook configurations** | The cluster-wide **ValidatingWebhookConfiguration** + **MutatingWebhookConfiguration** that route every apply through `cnrm-webhook-manager`. The workload runs the webhook; *these* objects are what wire it into the API server's admission chain. |

---

## The workloads in detail

### `cnrm-controller-manager` — the engine (StatefulSet)

- The **reconciler**: for every managed object, it makes Google Cloud API calls to
  create / update / delete the real resource so it matches the spec.
- It runs in one of two shapes, by mode:
  - **Cluster mode** — one workload, one identity for the whole cluster.
  - **Namespaced mode** — one workload *per* namespace
    (`cnrm-controller-manager-${NAMESPACE}`), each scoped to its namespace with its
    own identity.

### `cnrm-webhook-manager` — admission control (Deployment)

Runs the **validating + mutating admission webhooks** — the gate every apply passes
through. All fail-closed (`FailurePolicy: Fail`).

| Webhook type   | What it does              | Examples                                                                                                         |
| -------------- | ------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| **Validating** | rejects bad applies       | immutable-field changes, unknown fields, IAM resources, per-resource validation, `state-into-spec` annotation    |
| **Mutating**   | fills things in on create | container annotations (project/folder/org), IAM defaults, management-conflict annotation, generic field defaults |

### `cnrm-deletiondefender` — safe deletion (StatefulSet)

- A **finalizer-based safety mechanism** . It holds the
  `deletion-defender` finalizer on managed objects so a delete can't complete until
  it has decided **delete vs. abandon** the underlying cloud resource.
- Its key job: when the **CRD itself is being uninstalled** (i.e. Config Connector is
  being removed), it defaults resources to **abandon** — so uninstalling Config
  Connector does **not** cascade-delete your real Google Cloud resources. Otherwise it
  releases the finalizer and lets the controller delete normally.

### `cnrm-resource-stats-recorder` — metrics (Deployment)

- On an interval (~60s) it walks every managed resource, reads each one's **Ready
  condition**, and aggregates counts per namespace / kind / condition.
- Exposes them as a **Prometheus** metric (`applied_resources_total`). Pure
  observability — see [[M4-monitoring]].

### `cnrm-unmanaged-detector` — drift signal, **namespaced mode only** (StatefulSet)

- Deployed **only in namespaced mode** — it has nothing to do in cluster mode.
- It watches managed resources and, for any resource in a namespace that has **no
  controller manager** (i.e. you forgot the ConfigConnectorContext for that
  namespace), it sets the object's **Ready** condition to **False** with reason
  **Unmanaged** and emits a warning event.
- This is what turns "I applied a resource but nothing happened" into a visible
  signal: *"No controller is managing this resource. Check if a ConfigConnectorContext
  exists for the namespace."*

---

## Cluster vs. namespaced — what differs

Everything in [What the apply creates](#what-the-apply-creates) is shared
cluster-wide **except** the controller and its identity. The mode you chose on the
ConfigConnector spec changes only these:

| Concern | Cluster mode | Namespaced mode |
| ------- | ------------ | --------------- |
| **The controller** | One shared `cnrm-controller-manager` StatefulSet for the whole cluster. | A **dedicated** `cnrm-controller-manager-${NAMESPACE}` StatefulSet per namespace, stood up when you apply that namespace's ConfigConnectorContext. |
| **Identity binding** | One controller ServiceAccount, bound once to the GSA on the ConfigConnector spec. | Bound later and **per-namespace** — each ConfigConnectorContext binds its controller to *that* namespace's GSA ([[M2-operator-crds]]). |
| **`cnrm-unmanaged-detector`** | Not deployed — it has nothing to do. | Deployed (shared) — flags resources in namespaces that have no controller. |

The CRDs, webhook configs, `cnrm-webhook-manager`, `cnrm-deletiondefender`,
`cnrm-resource-stats-recorder`, and the `cnrm-system` namespace are the same in
both modes.