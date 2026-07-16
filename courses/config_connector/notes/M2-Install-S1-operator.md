<!-- =====================================================================
  Deploying and Using Config Connector with GKE
  Reference notes for instructors & students
===================================================================== -->

![Deploying and Using Config Connector with GKE](_assets/course-banner.png)

# M2 - Install stage 1: the operator (and its architecture)

Installing Config Connector is a **two-stage** process, and this note is about
**stage one: installing the operator**—what you apply, what lands in the cluster,
and the small architecture it stands up. The operator is a bootstrap workload that
knows how to install and configure everything else—it does *not* manage any
Google Cloud resources itself.

- **Stage 1 (this note):** apply the operator manifest → a handful of Kubernetes
  resources + 8 management CRDs land in the cluster.
- **Stage 2 ([M2-Install-S2-connector](M2-Install-S2-connector.md)):** you apply a **ConfigConnector**
  resource, and *the operator* reacts by standing up the controllers and the
  Google-resource CRDs.

---

## Key takeaways

- **The operator is a bootstrap, not the engine.** It installs and configures the
  rest of Config Connector; it doesn't reconcile Google Cloud resources. Nothing
  happens to your cloud resources until stage 2.
- **You download a release bundle, not a single file.** The package
  (`release-bundle.tar.gz`) contains **two** operator manifests—one for Standard
  GKE, one for Autopilot.
- **Applying the operator manifest creates a fixed, small set of resources** (listed
  below)—including exactly **8 CRDs**, which are Config Connector's *own*
  management CRDs, **not** the Google-resource CRDs.
- **The operator then sits idle** until you give it a ConfigConnector resource.

---

## Step 1: Download the release bundle

The manifests ship inside a downloadable archive, **`release-bundle.tar.gz`**
([install docs](https://docs.cloud.google.com/config-connector/docs/how-to/install-manually#operator)).
Extracting it gives you two operator manifests under `operator-system/`:

| Cluster type | Manifest to apply |
|--------------|-------------------|
| **Standard** GKE (and most non-Autopilot) | `operator-system/configconnector-operator.yaml` |
| **Autopilot** | `operator-system/autopilot-configconnector-operator.yaml` |

> **Why two?** Autopilot restricts what workloads can request (privileges, resource
> shapes), so its operator manifest is a variant tuned to pass Autopilot's admission
> constraints. Pick the one matching your cluster—applying the wrong one can fail
> to schedule.

## Step 2: Apply the operator manifest

```bash
# Standard GKE
kubectl apply -f operator-system/configconnector-operator.yaml

# Autopilot
kubectl apply -f operator-system/autopilot-configconnector-operator.yaml
```

---

## What the operator manifest actually installs

Applying it creates the following, all in a **new namespace**
`configconnector-operator-system` (verified against the operator's own manifests in
[`operator/config/`](https://github.com/GoogleCloudPlatform/k8s-config-connector/tree/master/operator/config)):

| Resource | Kind | Name |
|----------|------|------|
| The namespace | `Namespace` | `configconnector-operator-system` |
| The operator workload | `StatefulSet` | `configconnector-operator` (1 replica) |
| Its identity | `ServiceAccount` | `configconnector-operator` |
| Its network endpoint | `Service` | `configconnector-operator-service` |
| Cluster-wide permissions | `ClusterRole` ×3 + `ClusterRoleBinding` ×2 | `manager-role`, `cnrm-viewer`, … |
| Management CRDs | `CustomResourceDefinition` ×8 | see [M2-operator-crds](M2-operator-crds.md) |

That's the whole footprint of stage 1—a single-replica controller, its RBAC, a
service, and 8 CRDs. Small on purpose.

> **The 8 CRDs are the operator's management API**, not the cloud-resource catalog.
> They're `ConfigConnector`, `ConfigConnectorContext`, and the six `customize.…`
> tuning CRDs. The ~200 Google-resource CRDs (ComputeAddress, StorageBucket, …) are
> **not** installed here—the operator lays those down in stage 2. Full breakdown
> in [M2-operator-crds](M2-operator-crds.md).

---

## Step 3: What's next

The operator is now running but **idle**. To actually turn Config Connector on, you
create a **ConfigConnector** resource (`configconnector.yaml`) choosing cluster vs.
namespaced mode and the identity, then:

```bash
kubectl apply -f configconnector.yaml
```
