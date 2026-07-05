![Deploying and Using Config Connector with GKE](_assets/course-banner.png)

# M2 - Install stage 2: the ConfigConnector resource (and its architecture)

---

## Overview

Stage 1 ([M2-Install-S1-operator](M2-Install-S1-operator.md)) installed the operator — a small idle
bootstrap. **Stage 2 turns Config Connector on:** you apply a **ConfigConnector**
resource (and, in namespaced mode, a **ConfigConnectorContext** per namespace), the
operator reacts by deploying the actual controllers and the Google-resource CRDs
into a new `cnrm-system` namespace, and you wire up the Google Cloud identity the
controllers authenticate as.

This note has two parts:

- **[Part A — Installation procedure](#part-a--installation-procedure)** — the ordered steps to run, in dependency order.
- **[Part B — What it creates & how it works](#part-b--what-it-creates--how-it-works)** — the architecture the procedure produces, for reference.
- 
A few things to fix in your head before the steps:

- **One resource flips the switch.** Applying a ConfigConnector object is the whole
  trigger — the operator watches for it and does the rest.
- **The name is fixed.** `metadata.name` **must** be
  `configconnector.core.cnrm.cloud.google.com` (it's a cluster singleton).
- **`mode` is the big decision:** `cluster` (one identity for everything) or
  `namespaced` (per-namespace identity). This shapes what the operator deploys and
  how many identities you wire up. The full contrast is in
  [Cluster vs. namespaced — what differs](#cluster-vs-namespaced--what-differs).
- **Identity comes before actuation.** The controllers can't touch Google Cloud
  until a GSA and a Workload Identity binding exist — so the procedure below sets up
  identity *before* it counts on the controllers doing any work.

---

## Part A — Installation procedure

The steps are in **dependency order** — follow them top to bottom. Cluster mode uses
steps 1, 3, 4, 5, 7; namespaced mode uses all of them. Each step is deliberately
thin; the "why" for each lives in [Part B](#part-b--what-it-creates--how-it-works),
linked inline.

### Step 1 — choose a mode and write the ConfigConnector manifest

**Cluster mode** — one Google Service Account for the whole cluster:

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

**Namespaced mode** — no `googleServiceAccount` here; identity is supplied per
namespace later (step 6):

```yaml
apiVersion: core.cnrm.cloud.google.com/v1beta1
kind: ConfigConnector
metadata:
  name: configconnector.core.cnrm.cloud.google.com
spec:
  mode: namespaced
  stateIntoSpec: Absent
```

### Step 2 — create and annotate the resource namespaces (namespaced mode)

In namespaced mode, resources live in ordinary Kubernetes namespaces you create —
one per team/tenant. Each needs a **project annotation** telling Config Connector
which Google Cloud project its resources belong to:

```bash
kubectl create namespace team-a
kubectl annotate namespace team-a \
  cnrm.cloud.google.com/project-id=my-team-a-project
```

There are analogous `folder-id` / `organization-id` annotations for folder- and
org-scoped resources. See [Identity & Workload Identity](#identity--workload-identity)
for how the annotation feeds the reconcile.

### Step 3 — create the GSA(s) and grant roles

The GSA is the identity Config Connector authenticates as when it calls Google
Cloud, so it needs whatever roles the resources you'll manage require:

```bash
gcloud iam service-accounts create cnrm-team-a \
  --project my-team-a-project

gcloud projects add-iam-policy-binding my-team-a-project \
  --member "serviceAccount:cnrm-team-a@my-team-a-project.iam.gserviceaccount.com" \
  --role "roles/storage.admin"
```

One GSA cluster-wide (cluster mode) or one per namespace (namespaced mode). Why a
GSA at all, and not a bare KSA, is in
[Identity & Workload Identity](#identity--workload-identity).

### Step 4 — bind the KSA to the GSA (Workload Identity)

Grant the controller's KSA the `roles/iam.workloadIdentityUser` role **on the GSA**:

```bash
gcloud iam service-accounts add-iam-policy-binding \
  cnrm-team-a@my-team-a-project.iam.gserviceaccount.com \
  --role "roles/iam.workloadIdentityUser" \
  --member "serviceAccount:HOST_PROJECT.svc.id.goog[cnrm-system/cnrm-controller-manager-team-a]"
```

The member string names the KSA via the cluster's workload identity pool
(`HOST_PROJECT.svc.id.goog[namespace/ksa-name]`). In cluster mode the KSA is
`cnrm-system/cnrm-controller-manager`. The KSA itself is created *for* you by the
operator — see [Identity & Workload Identity](#identity--workload-identity) for the
full chain and why this is impersonation, not direct resource access.

### Step 5 — apply the ConfigConnector resource

```bash
kubectl apply -f configconnector.yaml
```

This is the trigger: the operator stands up the controllers, CRDs, and supporting
resources — the full inventory is in [What the apply creates](#what-the-apply-creates).

### Step 6 — create and apply a ConfigConnectorContext per namespace (namespaced mode)

In namespaced mode, applying the ConfigConnector alone doesn't give any namespace a
controller. You create one **ConfigConnectorContext** (CCC) in each namespace you
want active — that's what makes the operator stand up that namespace's dedicated
controller and bind it to the namespace's GSA:

```yaml
apiVersion: core.cnrm.cloud.google.com/v1beta1
kind: ConfigConnectorContext
metadata:
  # the only accepted name — one CCC per namespace
  name: configconnectorcontext.core.cnrm.cloud.google.com
  namespace: team-a
spec:
  googleServiceAccount: "cnrm-team-a@my-team-a-project.iam.gserviceaccount.com"
  requestProjectPolicy: RESOURCE_PROJECT
  stateIntoSpec: Absent
```

```bash
kubectl apply -f configconnectorcontext-team-a.yaml
```

Repeat per namespace. What the CCC's spec fields mean and what it triggers is in
[The ConfigConnectorContext](#the-configconnectorcontext-namespaced-mode).

### Step 7 — verify the controllers came up

The controller Pod can take **several minutes** to start.

```bash
kubectl wait -n cnrm-system \
  --for=condition=Ready pod \
  -l cnrm.cloud.google.com/component=cnrm-controller-manager
# → pod/cnrm-controller-manager-0 condition met
```

In namespaced mode, check for the per-namespace controller
(`cnrm-controller-manager-team-a`) instead.

---

## Part B — What it creates & how it works

Everything in Part A produces the runtime architecture below. This part is
reference — read the piece you need, in any order.

### What the apply creates

A single `kubectl apply` of the ConfigConnector object doesn't just start some
pods — the operator lays down a whole set of cluster objects and reconciles all of
it for you. Here's the full inventory, grouped by kind of thing.

#### The workloads

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

#### The supporting resources

The plumbing the workloads need — created once, rarely thought about again.

| What's created | Detail |
| -------------- | ------ |
| **The `cnrm-system` namespace** | Every workload, ServiceAccount, and Service lives here. It's created by the operator, not by you — you don't `kubectl create namespace` it. |
| **~212 Google-resource CRDs** | The **StorageBucket**, **ComputeAddress**, **PubSubTopic**, … kinds you'll actually author. These are **not** the operator's own 8 management CRDs ([M2-operator-crds](M2-operator-crds.md)) — they arrive *now*, at this apply, not at operator install. |
| **A ServiceAccount per workload** | One per workload above. The controller's KSA is the one **bound to your Google Service Account via Workload Identity** — the link that lets in-cluster pods authenticate as the GSA from your manifest. |
| **Cluster-wide RBAC** | ClusterRoles + ClusterRoleBindings (and a couple of namespaced Roles/RoleBindings) granting each workload the API access it needs — e.g. the controller's permission to watch every managed-resource CRD across all namespaces. |
| **Services** | `cnrm-controller-manager-service`, `cnrm-resource-stats-recorder-service`, and the webhook Service — stable addresses fronting the pods (the first two are the metrics endpoints, see [M4-monitoring](M4-monitoring.md)). |
| **Webhook configurations** | The cluster-wide **ValidatingWebhookConfiguration** + **MutatingWebhookConfiguration** that route every apply through `cnrm-webhook-manager`. The workload runs the webhook; *these* objects are what wire it into the API server's admission chain. |

### The workloads in detail

#### `cnrm-controller-manager` — the engine (StatefulSet)

- The **reconciler**: for every managed object, it makes Google Cloud API calls to
  create / update / delete the real resource so it matches the spec.
- It runs in one of two shapes, by mode:
  - **Cluster mode** — one workload, one identity for the whole cluster.
  - **Namespaced mode** — one workload *per* namespace, each scoped to its
    namespace with its own identity. The StatefulSet is named
    `cnrm-controller-manager-<id>` and its Service `cnrm-manager-<id>`, where
    `<id>` is a stable, randomly generated per-namespace identifier (persisted in
    the `namespace-id` ConfigMap in `configconnector-operator-system`) — the
    namespace's ServiceAccount, by contrast, is named literally
    `cnrm-controller-manager-<namespace>`.

#### `cnrm-webhook-manager` — admission control (Deployment)

Runs the **validating + mutating admission webhooks** — the gate every apply passes
through. All fail-closed (`FailurePolicy: Fail`).

| Webhook type   | What it does              | Examples                                                                                                         |
| -------------- | ------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| **Validating** | rejects bad applies       | immutable-field changes, unknown fields, IAM resources, per-resource validation, `state-into-spec` annotation    |
| **Mutating**   | fills things in on create | container annotations (project/folder/org), IAM defaults, management-conflict annotation |

#### `cnrm-deletiondefender` — safe deletion (StatefulSet)

- A **finalizer-based safety mechanism** . It holds the
  `deletion-defender` finalizer on managed objects so a delete can't complete until
  it has decided **delete vs. abandon** the underlying cloud resource.
- Its key job: when the **CRD itself is being uninstalled** (i.e. Config Connector is
  being removed), it defaults resources to **abandon** — so uninstalling Config
  Connector does **not** cascade-delete your real Google Cloud resources. Otherwise it
  releases the finalizer and lets the controller delete normally.

#### `cnrm-resource-stats-recorder` — metrics (Deployment)

- On an interval (~60s) it walks every managed resource, reads each one's **Ready
  condition**, and aggregates counts per namespace / kind / condition.
- Exposes them as a **Prometheus** metric (`applied_resources_total`). Pure
  observability — see [M4-monitoring](M4-monitoring.md).

#### `cnrm-unmanaged-detector` — drift signal, **namespaced mode only** (StatefulSet)

- Deployed **only in namespaced mode** — it has nothing to do in cluster mode.
- It watches managed resources and, for any resource in a namespace that has **no
  controller manager** (i.e. you forgot the ConfigConnectorContext for that
  namespace), it sets the object's **Ready** condition to **False** with reason
  **Unmanaged** and emits a warning event.
- This is what turns "I applied a resource but nothing happened" into a visible
  signal: *"No controller is managing this resource. Check if a ConfigConnectorContext
  exists for the namespace."*

### The ConfigConnectorContext (namespaced mode)

The CCC ([Step 6](#step-6--create-and-apply-a-configconnectorcontext-per-namespace-namespaced-mode))
is how namespaced mode supplies **identity per namespace**. It's a cluster-managed
CRD from the operator ([M2-operator-crds](M2-operator-crds.md)); one per namespace,
with a fixed name.

**What applying it triggers:** the operator stands up a dedicated
`cnrm-controller-manager-${NAMESPACE}` StatefulSet for that namespace, creates its
KSA, and stamps the Workload Identity annotation for the GSA you named — so the
namespace's resources reconcile under *that* namespace's identity.

Key `spec` fields (from `configconnectorcontext_types.go`):

- **`googleServiceAccount`** *(required)* — the GSA this namespace's resources
  authenticate as.
- **`requestProjectPolicy`** — which project gates/pays for the API calls:
  `SERVICE_ACCOUNT_PROJECT` (default), `RESOURCE_PROJECT`, or `BILLING_PROJECT`.
- **`billingProject`** — the project to bill, when `requestProjectPolicy` is
  `BILLING_PROJECT`.
- **`stateIntoSpec`** / **`actuationMode`** — same meaning as on ConfigConnector;
  set here, the **namespaced value wins** over the cluster-wide one.

> **A namespace without a CCC gets no controller.** That's the exact condition
> `cnrm-unmanaged-detector` flags — resources sit **Unmanaged** until you apply the
> CCC.

### Identity & Workload Identity

Applying the ConfigConnector stands up the controllers, but they can't touch Google
Cloud until they can **authenticate as a Google identity**. The mechanism is
**Workload Identity**: a Kubernetes ServiceAccount (KSA) is allowed to *impersonate*
a Google Service Account (GSA), so pods running under that KSA get the GSA's
permissions with no exported key.

The binding is a four-link chain — all four must line up or the controller's API
calls fail with permission errors:

```
controller Pod  →  runs as KSA  →  (workloadIdentityUser binding)  →  GSA  →  holds project roles
   (operator)      (operator)              (admin, step 4)         (admin, step 3)
```

- **The KSA and its WI annotation are automatic.** You don't create the controller's
  KSA — the operator does, and it stamps the annotation
  (`iam.gke.io/gcp-service-account: <GSA email>`) onto it, derived from the
  `googleServiceAccount` you gave. Cluster mode: one KSA `cnrm-controller-manager`.
  Namespaced mode: one `cnrm-controller-manager-${NAMESPACE}` per CCC. Both in
  `cnrm-system`.
- **The GSA, its roles, and the WI policy binding are yours** — steps 3 and 4.
- **The project annotation** on each namespace (step 2) is a separate axis: it tells
  the controller *which project* to create resources in, independent of *which
  identity* it authenticates as.

> **Config Connector uses the impersonation pattern, not direct resource access.**
> GKE now supports a newer Workload Identity style — *direct resource access* — where
> you skip the GSA and grant roles straight to the KSA principal
> (`principal://iam.googleapis.com/projects/…/subject/ns/cnrm-system/…`). Config
> Connector does **not** use that. It uses the **original GSA-impersonation** model:
> a real GSA holds the roles, and the KSA is bound to it via
> `roles/iam.workloadIdentityUser`. This is baked into the operator — it stamps the
> `iam.gke.io/gcp-service-account` annotation onto the controller KSA
> (`operator/pkg/k8s/constants.go`), which is precisely the impersonation-path
> annotation. There is no option to point a controller at a bare `principal://` KSA
> binding; you always go through a GSA.

### Cluster vs. namespaced — what differs

Everything in [What the apply creates](#what-the-apply-creates) is shared
cluster-wide **except** the controller and its identity. The mode you chose on the
ConfigConnector spec changes only these:

| Concern | Cluster mode | Namespaced mode |
| ------- | ------------ | --------------- |
| **The controller** | One shared `cnrm-controller-manager` StatefulSet for the whole cluster. | A **dedicated** `cnrm-controller-manager-${NAMESPACE}` StatefulSet per namespace, stood up when you apply that namespace's ConfigConnectorContext. |
| **Identity binding** | One controller ServiceAccount, bound once to the GSA on the ConfigConnector spec. | Bound later and **per-namespace** — each ConfigConnectorContext binds its controller to *that* namespace's GSA ([M2-operator-crds](M2-operator-crds.md)). |
| **`cnrm-unmanaged-detector`** | Not deployed — it has nothing to do. | Deployed (shared) — flags resources in namespaces that have no controller. |

The CRDs, webhook configs, `cnrm-webhook-manager`, `cnrm-deletiondefender`,
`cnrm-resource-stats-recorder`, and the `cnrm-system` namespace are the same in
both modes.
