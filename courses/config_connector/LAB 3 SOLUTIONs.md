# Solution Manifests — Creating, Acquiring, and Deleting Resources With Config Connector

Complete, applyable manifests and commands for every task. These are the reference
answers. For most tasks the lab instructions give students goals and links, not these
YAMLs — but a few (Task 6c's inline experiments, Task 8's two topics) provide the
manifests in-line, in which case the YAML here matches the instructions verbatim.

**Naming convention.** Kubernetes object names are RFC-1123 (lowercase, hyphens).
Where a Google Cloud resource name uses characters illegal in a K8s name (e.g. the
underscore in a BigQuery dataset id) or otherwise differs, the real cloud name goes
in **`spec.resourceID`** and `metadata.name` stays a legal K8s identifier.

**Two environment values appear as tokens.** `${REGION}` (the lab region) in
`spec.location` / `spec.region`, and `${HOST_PROJECT_ID}` in the one Task 3
project-override annotation. **If you copy a manifest, hand-replace those tokens.**
There is no script — in the lab the student types the values shown in the
instructions. Everything else is project-scoped and token-free.

**Namespace.** The manifests below don't set `metadata.namespace`. In Task 1 the
student sets `managed` as the default namespace
(`kubectl config set-context --current --namespace=managed`), so objects land there
and commands need no `-n managed`. The `managed` namespace is annotated with
`cnrm.cloud.google.com/project-id` → the managed project, so the project is inherited
and never hardcoded in `spec` (except Task 3's deliberate host-project override).

**Validation:** `apiVersion`s and field names below were checked against the CRDs in
`k8s-config-connector/config/crds/resources`. Re-validate at build time — versions
drift.

---

## Task 2 — First resource: a minimal Pub/Sub topic

`first-topic.yaml`

```yaml
apiVersion: pubsub.cnrm.cloud.google.com/v1beta1
kind: PubSubTopic
metadata:
  name: first-topic             # project-scoped name → this IS the cloud topic name
```

Teaching point: a topic name only has to be unique *within the project*, and
`first-topic` is already a valid RFC-1123 name, so `metadata.name` is the cloud name
directly — no `spec.resourceID`, no token. (A globally-named resource like a Storage
bucket, or a name with illegal characters, would need `spec.resourceID`; that is
exactly the naming limitation Task 2 calls out.)
Verify: `gcloud pubsub topics list --project "$MANAGED_PROJECT_ID"` and
**Console → Pub/Sub → Topics**.

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

### 6a — Immutable field the docs FLAG (refused in place)

A **throwaway** PubSubSubscription whose `enableMessageOrdering` is marked `Immutable.`
in the reference docs. It references `first-topic` from Task 2, so run this while that
topic exists.

`ordering-demo.yaml` — steps 1, create and let it go `Ready`:

```yaml
apiVersion: pubsub.cnrm.cloud.google.com/v1beta1
kind: PubSubSubscription
metadata:
  name: ordering-demo
spec:
  topicRef:
    name: first-topic            # required reference; first-topic is from Task 2
  enableMessageOrdering: true     # IMMUTABLE (flagged "Immutable." in the docs)
```

Step 2, change `enableMessageOrdering: true` → `false` and re-apply. The apiserver
accepts the edit, but the **reconcile fails** — read the failure out of `status`:

```bash
kubectl describe pubsubsubscription/ordering-demo
# status.conditions: Ready flips to False with a reason/message naming the
# immutable field that cannot be changed in place.

# The precise "has my last edit been processed?" signal:
kubectl get pubsubsubscription/ordering-demo \
  -o jsonpath='gen={.metadata.generation} observed={.status.observedGeneration}{"\n"}'
# generation/observedGeneration may match while Ready stays False — the edit was
# processed and rejected.
```

The only correct remedy for an immutable field is delete + recreate:

```bash
kubectl delete pubsubsubscription/ordering-demo
# enableMessageOrdering is already false in the manifest, then:
kubectl apply -f ordering-demo.yaml
kubectl wait --for=condition=Ready pubsubsubscription/ordering-demo --timeout=120s
kubectl delete pubsubsubscription/ordering-demo   # clean up the throwaway
```

> **Note on the flip direction.** `true` → `false` is the change to test. If a given
> KCC/provider version happens to tolerate that flip and just goes `Ready`, reverse
> it (create with `false`, change to `true`) — that direction is reliably rejected.
> Verify at build time.

### 6b — Immutable field the docs DON'T flag (still refused)

A **throwaway** BigQueryDataset. `spec.location` is **not** prefixed `Immutable.` in
the reference docs, but a dataset cannot be relocated, so changing it is refused all
the same — proving the `Immutable.` label is documentation, not a guarantee of
completeness.

`dataset-demo.yaml` — create and let it go `Ready`:

```yaml
apiVersion: bigquery.cnrm.cloud.google.com/v1beta1
kind: BigQueryDataset
metadata:
  name: dataset-demo
spec:
  resourceID: dataset_demo       # underscore-legal cloud id (illegal in metadata.name)
  location: ${REGION}            # immutable in the BigQuery API, though UNMARKED in CC docs
```

Change `spec.location` to a different region (e.g. `EU`), re-apply, and read `status`:

```bash
kubectl apply -f dataset-demo.yaml
kubectl describe bigquerydataset/dataset-demo
# Ready flips to False — same delete-and-recreate situation as 6a, with NO
# "Immutable." label to warn you in advance.

kubectl delete bigquerydataset/dataset-demo      # clean up the throwaway
```

> **Why this dataset, not `lab-dataset`.** Use a fresh throwaway in the managed
> project — `lab-dataset` (Task 3) lives in the host project and the rest of the lab
> depends on it.

### 6c — A field the cloud API supports but the CRD doesn't

The CRD `spec` is a **closed allow-list** and a **subset** of the cloud API. Cloud
Storage supports a hierarchical-namespace option (`hierarchicalNamespace`), but the
`StorageBucket` CRD doesn't expose it. The apiserver rejects it at apply time — before
the controller runs — exactly as it rejects a field that doesn't exist at all.

```bash
# Real-but-unsurfaced field → rejected as unknown:
kubectl apply -f - <<EOF
apiVersion: storage.cnrm.cloud.google.com/v1beta1
kind: StorageBucket
metadata:
  name: ${MANAGED_PROJECT_ID}-hns-demo     # bucket names are GLOBAL — prefix with project id
spec:
  location: ${REGION}
  hierarchicalNamespace:                    # valid in GCS, NOT in this CRD
    enabled: true
EOF

# A made-up field fails identically — the apiserver can't tell the difference:
kubectl apply -f - <<EOF
apiVersion: storage.cnrm.cloud.google.com/v1beta1
kind: StorageBucket
metadata:
  name: ${MANAGED_PROJECT_ID}-typo-demo
spec:
  location: ${REGION}
  notARealField: oops
EOF
# No bucket is created in either case — neither object passes admission.
```

> Heredocs here are **unquoted** (`<<EOF`, not `<<'EOF'`) so `${MANAGED_PROJECT_ID}`
> and `${REGION}` expand. Bucket names must be globally unique.

Output-only fields (the third "unsettable" category, mentioned in the summary but not
a separate step): CC populates them under `status` and you never set them. Inspect
them on any resource that's up, e.g.:

```bash
# Look for "Output only." fields in the docs (creationTime, etag, selfLink, …):
kubectl get bigquerydataset/lab-dataset -o yaml | sed -n '/^status:/,$p'
```

Teaching point: three layers of "you can't set this." **Immutable** (rejected on
change at *reconcile* → read `status.conditions`; remedy is recreate — flagged
`Immutable.` in 6a, unflagged in 6b). **Output-only** (under `status`, never in
`spec`). **Not in the CRD** (real-but-unsurfaced *or* made-up → rejected at *apply* by
the structural schema). The durable diagnostic skill: `status.conditions` is the
controller's feedback channel, and `observedGeneration == metadata.generation` tells
you the controller has processed your latest edit (even when it then rejects it).

---

## Task 7 — Acquire the pre-existing dataset

The dataset `legacy_dataset` was created out of band during setup (by Terraform, NOT
Config Connector) and is **not** managed by Config Connector. Apply a manifest whose
identity matches it; Config Connector acquires rather than creates.

> **`metadata.name` / `spec.resourceID` for acquisition.** `legacy_dataset` contains
> an underscore, so it can't be the `metadata.name` — use an RFC-1123 object name and
> put the real id in `spec.resourceID`. (For resources with a **server-generated id**,
> `spec.resourceID` is likewise the acquire mechanism: set it to the existing id and
> let `metadata.name` be any K8s label.) Acquisition = identity match.

`acquire.yaml`

```yaml
apiVersion: bigquery.cnrm.cloud.google.com/v1beta1
kind: BigQueryDataset
metadata:
  name: legacy-dataset          # RFC-1123 object name (hyphen)
spec:
  resourceID: legacy_dataset    # matches the existing cloud dataset id exactly
  # Mirror the real resource's location so the first reconcile is a no-op.
  location: ${REGION}
```

Verify:

```bash
# BEFORE: exists in cloud (managed project), not in the cluster
bq show "${MANAGED_PROJECT_ID}:legacy_dataset"
kubectl get bigquerydataset/legacy-dataset   # not found

kubectl apply -f acquire.yaml                            # verb: created (the K8s object)

# AFTER: now managed, and the cloud resource was NOT recreated
kubectl wait --for=condition=Ready bigquerydataset/legacy-dataset --timeout=120s
bq show "${MANAGED_PROJECT_ID}:legacy_dataset"           # same creation time, intact
```

Teaching point: acquisition = identity match (`metadata.name`, or `spec.resourceID`
for server-generated / illegal-name ids). If the manifest's field values differ from
the live resource, the first reconcile *changes* the live resource to match — so an
acquire manifest should mirror current reality.

---

## Task 8 — Deletion policies

### 8a — Default (cloud resource IS deleted)

`delete-default.yaml`

```yaml
apiVersion: pubsub.cnrm.cloud.google.com/v1beta1
kind: PubSubTopic
metadata:
  name: delete-me
```

```bash
kubectl apply -f delete-default.yaml
kubectl wait --for=condition=Ready pubsubtopic/delete-me --timeout=120s

kubectl delete -f delete-default.yaml
gcloud pubsub topics list --project "$MANAGED_PROJECT_ID"   # delete-me is GONE
```

### 8b — Abandon (cloud resource SURVIVES)

`abandon.yaml`

```yaml
apiVersion: pubsub.cnrm.cloud.google.com/v1beta1
kind: PubSubTopic
metadata:
  name: keep-me
  annotations:
    cnrm.cloud.google.com/deletion-policy: abandon
```

```bash
kubectl apply -f abandon.yaml
kubectl wait --for=condition=Ready pubsubtopic/keep-me --timeout=120s

kubectl delete -f abandon.yaml                              # removes K8s object only
gcloud pubsub topics list --project "$MANAGED_PROJECT_ID"   # keep-me STILL EXISTS
```

Teaching point: `abandon` = remove from management without deleting the cloud
resource. Default = delete both. (`keep-me` is now an unmanaged resource — a perfect
candidate to re-acquire à la Task 7.)

---

## Wrap-up / teardown

```bash
# Delete the remaining managed objects (default policy also deletes the cloud
# resources). The abandoned keep-me topic from Task 8 survives unless removed by hand.
kubectl delete bigquerydataset --all
kubectl delete computeaddress,computesubnetwork,computenetwork --all
kubectl delete pubsubtopic --all
# keep-me (abandoned) still exists in the cloud:
gcloud pubsub topics delete keep-me --project "$MANAGED_PROJECT_ID"   # if cleanup desired
```

---

> **Build-time validation checklist**
> - [ ] Every manifest passes `kubectl apply --dry-run=server` (tokens typed in).
> - [ ] Task 3: dataset appears in the HOST project and is NOT in the managed project.
> - [ ] Task 3: editing + re-applying propagates within seconds (30s interval).
> - [ ] Task 4: subnet shows `DependencyNotReady` before the network is `Ready`.
> - [ ] Task 4: `kubectl get -o yaml` shows the resolved `networkRef`/`subnetworkRef` and `status` values.
> - [ ] Task 5: an out-of-band `bq update` to a managed field is reverted within the interval (or on re-apply).
> - [ ] Task 6a: changing `enableMessageOrdering` produces a visible immutable-field condition in `status.conditions` (test the flip direction — see 6a note).
> - [ ] Task 6b: changing `BigQueryDataset.location` is refused even though it carries no `Immutable.` label.
> - [ ] Task 6c: `hierarchicalNamespace` (and a made-up field) are rejected at apply with "unknown field"; no bucket is created.
> - [ ] Task 6: `observedGeneration`/`generation` and output-only `status` fields are inspectable as documented.
> - [ ] Task 7: `bq show` creation timestamp is identical before and after acquire.
> - [ ] Task 8b: the abandoned topic survives `kubectl delete`.
