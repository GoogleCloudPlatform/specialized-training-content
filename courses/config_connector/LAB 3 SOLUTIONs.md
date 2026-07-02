# Solution Manifests — Creating, Acquiring, and Deleting Resources With Config Connector

---

## Task 2 — First resource: a minimal Pub/Sub topic

apiVersion: pubsub.cnrm.cloud.google.com/v1beta1
kind: PubSubTopic
metadata:
  name: first-topic             # project-scoped name → this IS the cloud topic name

---

## Task 3 — Labels, reconcile interval, explicit (host) project

`lab-dataset.yaml`

```yaml
apiVersion: bigquery.cnrm.cloud.google.com/v1beta1
kind: BigQueryDataset
metadata:
  name: lab-dataset             # RFC-1123 K8s object name (hyphen)
  annotations:
    # Re-reconcile desired vs. actual every 30s (short, so the reconcile/drift
    # tests in this task and Task 5 are quick to observe).
    cnrm.cloud.google.com/reconcile-interval-in-seconds: "30"
    # Explicit per-object project designation. OVERRIDES the namespace annotation,
    # which points at the managed project. Here we point at the HOST project, so
    # the dataset is created in a DIFFERENT project than every other resource —
    # making the override observable. Hand-replace the token when copying.
    cnrm.cloud.google.com/project-id: ${HOST_PROJECT_ID}
  labels:
    # GCP resource labels. Config Connector PROPAGATES metadata.labels to the
    # underlying Google Cloud resource (and also adds managed-by-cnrm: true).
    team: platform
    purpose: lab
spec:
  resourceID: lab_dataset       # real cloud dataset id (underscore — illegal in metadata.name)
  location: ${REGION}
  description: Managed by Config Connector   # drifted/restored in Task 5
```

Teaching points:
- **Object name vs. cloud name.** `metadata.name` is `lab-dataset` (hyphen, legal
  K8s name); the real BigQuery dataset id is `lab_dataset` (underscore), carried in
  `spec.resourceID`. The instructions must include a note explaining this mismatch.
- **Labels.** For this kind, **`metadata.labels`** is what lands on GCP — confirm
  with `bq show --format=prettyjson "$HOST_PROJECT_ID:lab_dataset"`, where you'll see
  `team`, `purpose`, **and** the system-added `managed-by-cnrm: true`. (A few newer
  kinds expose `spec.labels` instead — check the kind's schema.)
- **Project override.** The object annotation beats the namespace annotation, so the
  dataset lands in the HOST project. Prove it: it exists in `$HOST_PROJECT_ID` and is
  **not found** in `$MANAGED_PROJECT_ID`. (Precedence: object annotation >
  `spec.projectRef` where supported > namespace annotation.)

Reconciliation test (apply → reconcile → verify), e.g. add a label and re-apply:

```bash
# After editing lab-dataset.yaml (e.g. add label env: dev), apply and watch the
# controller reconcile your OWN change:
kubectl apply -f lab-dataset.yaml
kubectl get bigquerydataset/lab-dataset \
  -o jsonpath='gen={.metadata.generation} observed={.status.observedGeneration}{"\n"}'
# When observedGeneration == generation, the reconcile of your latest edit is done.
bq show --format=prettyjson "$HOST_PROJECT_ID:lab_dataset"   # new label is present
```

---

## Task 4 — Resource references (a network chain)

`network.yaml`

```yaml
apiVersion: compute.cnrm.cloud.google.com/v1beta1
kind: ComputeNetwork
metadata:
  name: lab-network
  annotations:
    # Short interval so dependents re-check quickly and the chain comes up fast
    # (default is 600s). Applied to all three resources.
    cnrm.cloud.google.com/reconcile-interval-in-seconds: "20"
spec:
  autoCreateSubnetworks: false
  routingMode: REGIONAL
---
apiVersion: compute.cnrm.cloud.google.com/v1beta1
kind: ComputeSubnetwork
metadata:
  name: lab-subnet
  annotations:
    cnrm.cloud.google.com/reconcile-interval-in-seconds: "20"
spec:
  region: ${REGION}
  ipCidrRange: 10.10.0.0/24
  # Required reference to the network above. The subnet reconciles only after the
  # network is Ready (shows DependencyNotReady until then).
  networkRef:
    name: lab-network
---
apiVersion: compute.cnrm.cloud.google.com/v1beta1
kind: ComputeAddress
metadata:
  name: lab-internal-ip
  annotations:
    cnrm.cloud.google.com/reconcile-interval-in-seconds: "20"
spec:
  location: ${REGION}
  addressType: INTERNAL          # NOTE: addressType is IMMUTABLE — reused in Task 6
  # Reference the subnet for the internal address allocation.
  subnetworkRef:
    name: lab-subnet
```

Watch the dependency chain resolve with a SINGLE command (not repeated get):

```bash
# Option A — block until each is Ready, in dependency order:
kubectl wait --for=condition=Ready \
  computenetwork/lab-network computesubnetwork/lab-subnet computeaddress/lab-internal-ip \
  --timeout=300s

# Option B — watch the transitions live (see DependencyNotReady flip to Ready):
kubectl get computenetwork,computesubnetwork,computeaddress -w
```

See what the references resolved to:

```bash
kubectl get computesubnetwork/lab-subnet -o yaml   # spec.networkRef + status.selfLink, etc.
kubectl get computeaddress/lab-internal-ip \
  -o jsonpath='{.spec.subnetworkRef}{"\n"}{.status.address}{"\n"}'  # what it points at + allocated IP
```

Teaching point: `*Ref.name` references a managed object in the same namespace, and
Config Connector derives the dependency order automatically (apply all three at
once). `DependencyNotReady` is a normal transient state, not an error.
`*Ref.external` (Task 7) references something *not* managed by Config Connector.

---

## Task 5 — Drift reconciliation (the control loop in action)

No new manifest — this task acts on `lab-dataset` from Task 3 (which carries the 30s
reconcile interval and lives in the **host** project). The point is to change the
resource *behind Config Connector's back* and watch it get reverted. (Task 3 already
showed reconciliation of *your own* applied change; this is the drift half.)

```bash
# 1. Confirm the manifest's value is live (lab-dataset is in the HOST project).
bq show --format=prettyjson "$HOST_PROJECT_ID:lab_dataset" | grep -E 'friendlyName|description'

# 2. Drift it directly in Google Cloud (no kubectl involved).
bq update --description "drifted out of band" "$HOST_PROJECT_ID:lab_dataset"
bq show --format=prettyjson "$HOST_PROJECT_ID:lab_dataset"   # drift is visible NOW

# 3a. Wait out the reconcile interval (<= 30s) and re-check — OR —
# 3b. Force an immediate reconcile by re-applying the manifest:
kubectl apply -f lab-dataset.yaml

# 4. Confirm Config Connector reverted the managed field to the manifest.
bq show --format=prettyjson "$HOST_PROJECT_ID:lab_dataset"   # description is back

# Watch the object reconcile:
kubectl get bigquerydataset/lab-dataset -w
```

Teaching point: reconciliation is a **continuous control loop**, not a one-shot
apply. The manifest is the source of truth; out-of-band edits to *managed* fields are
temporary. Reconciliation fires on three triggers — **apply**, the **reconcile
interval**, and **controller restart** — and the interval is the upper bound on how
long drift can persist.

---

## Task 6 — Fields you can't change (or set at all)

Three throwaway experiments, each failing at a different layer. All objects land in
the default `managed` namespace (managed project).

