<!-- =====================================================================
  Deploying and Using Config Connector with GKE
  Reference notes for instructors & students
===================================================================== -->

![Deploying and Using Config Connector with GKE](_assets/course-banner.png)

# M2 - The operator's own CRDs

Installing the **Config Connector operator** adds exactly **8 CRDs** to the
cluster. These are the operator's *management* CRDs—the knobs you use to install,
configure, and tune Config Connector itself.

> **Not to be confused with** the couple hundred Google-resource CRDs
> (ComputeAddress, StorageBucket, …)—roughly **~212** on a typical GKE add-on
> install (mostly stable + beta; most alpha resources aren't shipped there). Those
> are **not** installed by the operator; the operator lays them down *later*, when
> you apply a **ConfigConnector** resource and it stands up the controllers. This
> note is only about the 8 that arrive with the operator.

All 8 live in two API groups and are defined under
[`operator/config/crd/bases/`](https://github.com/GoogleCloudPlatform/k8s-config-connector/tree/master/operator/config/crd/bases):

- **`core.cnrm.cloud.google.com`** — the two install-config CRDs.
- **`customize.core.cnrm.cloud.google.com`** — the six tuning/customization CRDs.

---

## The 8 at a glance

| CRD | Group | Scope | Purpose |
|-----|-------|:-----:|---------|
| **ConfigConnector** | core | Cluster | Cluster-wide install config |
| **ConfigConnectorContext** | core | Namespaced | Per-namespace install config (namespaced mode) |
| **ControllerResource** | customize | Cluster | CPU/memory/replicas for cluster-mode controllers |
| **ControllerReconciler** | customize | Cluster | Reconciler tuning (rate limits) for cluster-mode controller |
| **NamespacedControllerResource** | customize | Namespaced | ControllerResource, scoped to one namespace's controller |
| **NamespacedControllerReconciler** | customize | Namespaced | ControllerReconciler, scoped to one namespace's controller |
| **ValidatingWebhookConfigurationCustomization** | customize | Cluster | Tune the validating admission webhooks |
| **MutatingWebhookConfigurationCustomization** | customize | Cluster | Tune the mutating admission webhooks |

> **Reading the scope column:** *Cluster*-scoped objects have no namespace and are
> effectively cluster singletons; *Namespaced* ones live in—and act on—a single
> namespace. This split mirrors Config Connector's two run modes (see
> **ConfigConnector** below).

---

## Install-config CRDs (`core` group)

### ConfigConnector – the cluster-wide install config

- **Scope:** Cluster. **Singleton** – the only accepted name is
  `configconnector.core.cnrm.cloud.google.com`.
- **What it does:** you apply exactly one of these to turn Config Connector on and
  choose how it runs. Applying it is what makes the operator deploy the controllers
  (and the Google-resource CRDs).

Key `spec` fields:

- **`mode`** – `cluster` or `namespaced`. **Defaults to `namespaced`.**
- **`googleServiceAccount`** – the GSA to authenticate with, via Workload Identity.
  **Cluster mode only.**
- **`actuationMode`** – `Reconciling` (default) or `Paused`.


### ConfigConnectorContext – the per-namespace install config

- **Scope:** Namespaced. **Singleton per namespace**—the only accepted name is
  `configconnectorcontext.core.cnrm.cloud.google.com`.
- **Used only in `namespaced` mode.** You create one in each namespace you want
  Config Connector active in.
- **What it triggers:** applying one makes the operator **stand up a dedicated
  controller manager for that namespace**. Per namespace you get a
  ServiceAccount named `cnrm-controller-manager-<namespace>` (the literal
  namespace), plus a StatefulSet `cnrm-controller-manager-<id>` and a Service
  `cnrm-manager-<id>`, where `<id>` is a stable, randomly generated per-namespace
  identifier the operator persists in the `namespace-id` ConfigMap in the
  `configconnector-operator-system` namespace. (The `<id>`, not the namespace
  name, is what appears in the StatefulSet/Service names — and note the Service
  drops `controller-` from its prefix.)

Key `spec` fields:

- **`googleServiceAccount`** *(required)* – the GSA this namespace's resources
  authenticate as.
- **`requestProjectPolicy`** – which project pays for / gates the API calls:
  `SERVICE_ACCOUNT_PROJECT` (default), `RESOURCE_PROJECT`, or `BILLING_PROJECT`.
- **`billingProject`** – the project to bill, when `requestProjectPolicy` is
  `BILLING_PROJECT`.
- **`actuationMode`** / **`stateIntoSpec`** – same meaning as on ConfigConnector;
  when set here, the **namespaced value wins** over the cluster-wide one.

---

## Customization CRDs (`customize` group)

These are all optional. You apply them only when the defaults don't fit—they tune
the workloads the operator already deployed. They come in **cluster-mode** and
**namespaced-mode** pairs that mirror the two run modes.

### ControllerResource – size the cluster-mode controllers

- **Scope:** Cluster.
- **What it does:** override **CPU / memory** (and, for the webhook, **replica
  count**) of the cluster-mode controller workloads.

Key `spec` fields:

- **`containers[]`** – per-container resource overrides. The container `name` must
  be one of: `manager`, `webhook`, `deletiondefender`, `prom-to-sd`, `recorder`,
  `unmanageddetector`. Each takes standard `resources.limits` / `resources.requests`.
- **`replicas`** – desired replica count; **only takes effect for
  `cnrm-webhook-manager`.**

> **When you'd use it:** the `manager` pod is getting OOMKilled while reconciling
> thousands of resources, so you bump its memory limit.
>
> **On `replicas`:** rarely needed. The webhook manager already ships with a
> HorizontalPodAutoscaler (min 2, max 20, scaling on 70% CPU/memory), so it grows
> under load on its own. Setting `replicas` here doesn't pin a fixed count—the
> operator uses it to raise the HPA's **minReplicas** (the floor). You'd do that to
> guarantee more warm replicas for HA, not to "add capacity"—the HPA handles
> capacity. There's no published webhooks/sec-per-replica figure; scaling is driven
> by CPU/memory utilization, not request rate.

### ControllerReconciler – tune the cluster-mode reconciler

- **Scope:** Cluster. **Singleton** – must be named `cnrm-controller-manager`.
- **What it does:** tune reconciler behavior for the cluster-mode controller.

Key `spec` fields:

- **`rateLimit`** – the token-bucket rate limit on the reconciler's Kubernetes
  client: **`qps`** and **`burst`**. Default is qps 20, burst 30.

> **When you'd use it:** you're hitting Google Cloud API quota (or overwhelming the
> API server) during large reconciles, so you *lower* qps/burst to throttle the
> controller—or *raise* them to speed up reconciliation on a cluster with quota
> headroom to spare.

### NamespacedControllerResource – same, per namespace

- **Scope:** Namespaced.
- **What it does:** identical to **ControllerResource**, but scoped to a single
  namespace's controller (the `cnrm-controller-manager-${NAMESPACE}` from
  ConfigConnectorContext). Use it in namespaced mode to size one namespace's
  controller independently.

> **When you'd use it:** in namespaced mode, one team's namespace manages far more
> resources than the others—you give *that* namespace's controller more
> CPU/memory without inflating every other namespace's controller.

### NamespacedControllerReconciler – same, per namespace

- **Scope:** Namespaced. Must be named `cnrm-controller-manager`.
- **What it does:** the namespaced-mode counterpart to **ControllerReconciler** –
  `rateLimit` (`qps` / `burst`) tuning for one namespace's controller.

> **When you'd use it:** one namespace's project keeps hitting API quota during
> reconciles—you throttle just that namespace's controller, leaving the others at
> full speed.

---

## Webhook customization CRDs (`customize` group)

Config Connector installs admission webhooks (validating + mutating) that enforce
and default resource fields. These two CRDs let you adjust the operator-managed
webhook configurations without editing them directly (the operator would just
revert manual edits).

### ValidatingWebhookConfigurationCustomization

- **Scope:** Cluster.
- **What it does:** override settings on the **validating** admission webhooks.

Key `spec` fields:

- **`webhooks[]`** – per-webhook overrides, selected by `name`. Valid names include
  `deny-immutable-field-updates`, `deny-unknown-fields`, `iam-validation`,
  `resource-validation`, `abandon-on-uninstall`, and others.
- **`timeoutSeconds`** – customize the webhook timeout, **1–30s** (Kubernetes
  default is 10s).

> **When you'd use it:** `kubectl apply` intermittently fails with webhook timeout
> errors under load—you raise `timeoutSeconds` on the validating webhook to give
> it more headroom.

### MutatingWebhookConfigurationCustomization

- **Scope:** Cluster.
- **What it does:** exactly the same, for the **mutating** admission webhooks
  (the defaulters — e.g. `generic-defaulter`, `iam-defaulter`,
  `container-annotation-handler`, `management-conflict-annotation-defaulter`).
- Same `webhooks[]` / `timeoutSeconds` shape as the validating version—the two
  share one underlying schema.

> **When you'd use it:** the mutating (defaulter) webhook is timing out and blocking
> applies — you raise its `timeoutSeconds`, the same fix as above but for the
> mutating side.

---

## Cluster vs. namespaced—how the pairs line up

The customization CRDs come in mirrored pairs; which one you use depends on the
`mode` you chose on **ConfigConnector**.

| Concern | Cluster mode | Namespaced mode |
|---------|--------------|-----------------|
| Install / identity | ConfigConnector | ConfigConnector + a ConfigConnectorContext per namespace |
| Controller sizing | ControllerResource | NamespacedControllerResource |
| Reconciler tuning | ControllerReconciler | NamespacedControllerReconciler |
| Webhook tuning | Validating/Mutating…Customization | *(same — webhooks are cluster-wide)* |

> The webhook-customization CRDs have no namespaced counterpart because the
> admission webhooks are a single cluster-wide set regardless of run mode.
