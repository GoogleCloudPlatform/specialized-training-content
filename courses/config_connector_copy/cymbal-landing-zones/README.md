# Cymbal Landing Zones with Config Connector

Stand up three reusable **landing zones** across three Google Cloud projects from a
**single GKE cluster** — using nothing but Kubernetes manifests and `kubectl`.
Then perform a **day-2 in-place update** and watch Config Connector reconcile the
change without recreating anything.

---

## 1. Scenario

Cymbal's **platform engineering team** is done with click-ops. Instead of
hand-building each new project, they've codified a catalog of **landing-zone
templates** — one per application archetype they repeatedly build. When an
application team needs infrastructure, the platform team provisions them a fresh
project from the matching template.

You play a member of that platform team. From one GKE cluster running the
**Config Connector** add-on, you'll apply three templates into three namespaces,
each wired to a different project, and then handle a mid-quarter change request.

The teaching point: **one Config Connector control plane fans out to three
projects.** What makes that happen isn't three clusters or three installs — it's
a single annotation on each namespace (`cnrm.cloud.google.com/project-id`) that
tells Config Connector which project a namespace's resources belong to.

### The three templates

| Template | Namespace | Onboarding team — why a fresh project |
|---|---|---|
| **streaming-analytics** | `cymbal-clickstream` | Marketing's website-event capture is one analyst's hand-built BigQuery tables and a stray function — undocumented and cost-entangled with another team. The mandate: a real clickstream pipeline in its own project. |
| **web-service-with-database** | `cymbal-portal` | A new customer self-service portal. Its own project gives blast-radius isolation (a portal bug can't reach unrelated data) and lets the app team own its database without filing tickets. |
| **build-and-artifact** | `cymbal-buildplatform` | Container images are scattered across teams' personal projects with inconsistent permissions. Security wants one locked-down project with a single CI identity and an audited registry. |

A fresh project per team is the pattern because it gives:

- **a clean blast radius** — a failure or compromise is contained,
- **its own IAM boundary** — permissions don't leak across teams, and
- **separate billing and quota** — costs and limits are attributable.

Config Connector makes that per-project baseline **reproducible** — desired state
in YAML — instead of a hand-built snowflake.

### The shared skeleton

All three templates share the same shape; they differ only in the workload layer.
The file numbering makes this visible side by side:

```
00-services      enable APIs            (OPTIONAL / unused — see §7.2)
10-iam           workload identity + scoped roles
20-… 30-… 40-…   the workload           ← the only part that differs
```

```
templates/
  streaming-analytics/cymbal-clickstream/      web-service-with-database/cymbal-portal/   build-and-artifact/cymbal-buildplatform/
    00-services.yaml                              00-services.yaml                           00-services.yaml
    10-iam.yaml                                   10-iam.yaml                                10-iam.yaml
    20-pubsub.yaml         ┐                       20-sql.yaml          ┐                      20-artifactregistry.yaml ┐
    30-bigquery.yaml       │ workload              30-storage.yaml      │ workload             30-pubsub.yaml           │ workload
    40-storage.yaml        ┘                                            ┘                      40-storage.yaml          ┘
```

---

## 2. Assumptions / prerequisites

Lab provisioning has already done all of the following. You do **not** create or
install any of it:

- A **GKE Standard cluster** with the **Config Connector add-on installed and
  healthy**.
- **Cluster mode** — one controller identity for the whole cluster. That
  controller's Google service account holds `roles/owner` on **all three**
  managed projects.
- **Three managed projects** with arbitrary IDs (e.g.
  `qwiklabs-gcp-01-a1b2c3d4e5f6`), created during setup.
- **Three namespaces** — `cymbal-clickstream`, `cymbal-portal`,
  `cymbal-buildplatform` — already created, each annotated with
  `cnrm.cloud.google.com/project-id` pointing at its project. This annotation is
  the entire fan-out mechanism.
- The required APIs (`pubsub`, `bigquery`, `storage`, `sqladmin`,
  `artifactregistry`) are already **enabled** on all three projects (see §7.2).

> Confirm the add-on is healthy before you start:
> ```bash
> kubectl get pods -n cnrm-system
> kubectl get namespaces cymbal-clickstream cymbal-portal cymbal-buildplatform
> kubectl get namespace cymbal-clickstream -o jsonpath='{.metadata.annotations.cnrm\.cloud\.google\.com/project-id}{"\n"}'
> ```

### Conventions used in every manifest

- **No hardcoded project IDs.** Manifests inherit the project from the namespace
  annotation. The few values that genuinely need a literal project ID
  (project-scoped IAM bindings, globally-unique bucket names, the IAM DB user)
  use substitution tokens, resolved once by `prep.sh` (§3).
- **Two labels** on every object, for filtering and side-by-side comparison:
  - `cymbal.dev/template: <streaming-analytics|web-service-with-database|build-and-artifact>`
  - `cymbal.dev/tenant: <clickstream|portal|buildplatform>`
- **A 60-second reconcile interval** on every object via
  `cnrm.cloud.google.com/reconcile-interval-in-seconds: "60"`, so Config
  Connector re-checks desired vs. actual state every minute.
- **IAM members reference the service-account object** (`memberFrom.serviceAccountRef`),
  never a hardcoded email — so no project ID leaks into the member string.
- **All IAM bindings are project-scoped** (`resourceRef: {kind: Project, external:
  projects/<id>}`), for lab simplicity.

---

## 3. Deletion / lifecycle policy

**Deleting a Kubernetes object deletes its underlying Google Cloud resource.**
These manifests use Config Connector's **default deletion behavior** — there is
no `cnrm.cloud.google.com/deletion-policy: abandon` annotation anywhere. The
YAML is the single source of truth: the manifest owns the resource.

Nothing is deletion-protected. The SQL instance explicitly sets
`deletionProtectionEnabled: false` so iteration and teardown are never blocked.

This is safe **because the lab projects are ephemeral** and torn down wholesale
at the end — there is no orphaned-resource risk. Do not copy this policy into a
production setup where data must survive a stray `kubectl delete`.

---

## 4. The walkthrough

You run every `kubectl apply` and `kubectl delete` by hand — that's the point of
the lab. After each apply there's a **"review what you just made"** checkpoint.

> **Region note:** the default `REGION` is `us-central1`. The BigQuery dataset is
> intentionally created in the `US` **multi-region** (BigQuery's conventional
> default), independent of `REGION`.

### Step 1 — Clone and enter the repo

```bash
git clone <this-repo-url>
cd cymbal-landing-zones
```

### Step 2 — Run `prep.sh` once (token substitution)

Export the three project IDs (and optionally `REGION`), then run the script. It
rewrites the project-ID / region tokens **in place** so every later
`kubectl apply` uses plain, ready manifests.

```bash
export CLICKSTREAM_PROJECT_ID=qwiklabs-gcp-01-...   \
       PORTAL_PROJECT_ID=qwiklabs-gcp-02-...        \
       BUILD_PROJECT_ID=qwiklabs-gcp-03-...         \
       REGION=us-central1
./prep.sh
```

After this, the tokens are consumed; no later step touches `envsubst`. To start
over, re-clone or run `git checkout -- templates/ day2/` to restore the tokens.

> **Optional — server-side dry run.** With the cluster reachable you can validate
> every manifest before applying for real:
> ```bash
> kubectl apply --dry-run=server -f templates/streaming-analytics/cymbal-clickstream/
> ```

### Step 3 — Apply template 1: streaming-analytics

```bash
kubectl apply -f templates/streaming-analytics/cymbal-clickstream/
```

**Review** — wait for everything to reconcile, then confirm in the cloud:

```bash
# Watch the Config Connector objects reach Ready
kubectl get gcp -n cymbal-clickstream
kubectl wait --for=condition=Ready --timeout=300s -n cymbal-clickstream \
  iamserviceaccount/clickstream-ingest \
  pubsubtopic/clickstream-events \
  bigquerydataset/clickstream \
  bigquerytable/events \
  storagebucket/clickstream-raw

# Confirm the real resources exist in the clickstream project
gcloud pubsub topics list             --project "$CLICKSTREAM_PROJECT_ID"
gcloud pubsub subscriptions list      --project "$CLICKSTREAM_PROJECT_ID"
bq ls --project_id "$CLICKSTREAM_PROJECT_ID" clickstream
bq show --schema "$CLICKSTREAM_PROJECT_ID:clickstream.events"
gcloud storage buckets list --project "$CLICKSTREAM_PROJECT_ID"
```

> If an object isn't `Ready`, `kubectl describe <kind>/<name> -n cymbal-clickstream`
> shows the reconcile status and any error message in the events/conditions.

### Step 4 — Apply template 2: web-service-with-database

```bash
kubectl apply -f templates/web-service-with-database/cymbal-portal/
```

> **The SQL instance takes ~5–10 minutes to go `Ready`.** This is an honest
> illustration of eventual consistency — Config Connector keeps reconciling until
> Cloud SQL finishes provisioning. Kick off **Step 5** while you wait, then come
> back.

**Review:**

```bash
kubectl get gcp -n cymbal-portal
kubectl wait --for=condition=Ready --timeout=900s -n cymbal-portal \
  sqlinstance/portal-db sqldatabase/portal sqluser/portal-app \
  storagebucket/portal-uploads

gcloud sql instances list      --project "$PORTAL_PROJECT_ID"
gcloud sql databases list      --instance portal-db --project "$PORTAL_PROJECT_ID"
gcloud sql users list          --instance portal-db --project "$PORTAL_PROJECT_ID"
gcloud storage buckets list    --project "$PORTAL_PROJECT_ID"
```

> **Password-free by design.** The `portal-app` database user is an **IAM
> service-account user** (`type: CLOUD_IAM_SERVICE_ACCOUNT`). The service account
> authenticates by identity via IAM database auth — **no database password is
> ever generated, stored, or committed.** This is the modern pattern: workload
> identity instead of a shared secret.

### Step 5 — Apply template 3: build-and-artifact

```bash
kubectl apply -f templates/build-and-artifact/cymbal-buildplatform/
```

**Review:**

```bash
kubectl get gcp -n cymbal-buildplatform
kubectl wait --for=condition=Ready --timeout=300s -n cymbal-buildplatform \
  artifactregistryrepository/cymbal-images \
  pubsubtopic/build-events \
  storagebucket/build-artifacts

gcloud artifacts repositories list --project "$BUILD_PROJECT_ID"
gcloud pubsub topics list          --project "$BUILD_PROJECT_ID"
gcloud storage buckets list        --project "$BUILD_PROJECT_ID"
```

### Step 6 — Cross-project review (the fan-out payoff)

You applied from **one cluster** but the resources landed in **three projects**.
Confirm it directly:

```bash
for ns in cymbal-clickstream cymbal-portal cymbal-buildplatform; do
  echo "== $ns =="
  kubectl get namespace "$ns" \
    -o jsonpath='  project-id: {.metadata.annotations.cnrm\.cloud\.google\.com/project-id}{"\n"}'
  kubectl get gcp -n "$ns"
done
```

Each namespace's resources resolved to a different project — driven purely by the
`cnrm.cloud.google.com/project-id` annotation, not by anything in the manifests.

### Step 7 — Day-2 operation

A change request comes in mid-quarter. See **[`day2/README.md`](day2/README.md)**
for the narrative, the before/after diff, and the apply/verify steps. In short:

```bash
kubectl apply -f day2/
```

This adds a `utm_campaign` column to the BigQuery table and extends the
clickstream bucket's retention from 30 to 60 days — **both in place**, without
recreating either resource.

### Step 8 — Tear down

Delete the templates (any order). Because of the default deletion policy, the
underlying Google Cloud resources are deleted too.

```bash
kubectl delete -f templates/streaming-analytics/cymbal-clickstream/
kubectl delete -f templates/web-service-with-database/cymbal-portal/
kubectl delete -f templates/build-and-artifact/cymbal-buildplatform/
```

**Confirm the cloud resources are gone** (re-run the `gcloud`/`bq` listing
commands from Steps 3–5 — they should come back empty). Leave the namespaces and
the Config Connector add-on in place.

> If a `kubectl delete` hangs, `kubectl describe` the object — a stuck delete is
> usually a dependency still in use or a finalizer waiting on the cloud API.

---

## 5. How the reconciliation model works (the mental model)

- **The YAML is desired state.** Config Connector continuously compares it to the
  actual Google Cloud resource and drives reality toward the manifest — on apply,
  on the 60-second interval, and whenever something drifts.
- **A change is just an edit + re-apply.** The same `kubectl apply` verb that
  *creates* a resource also *updates* it. There's no separate "update" command.
- **Some fields are mutable in place; some aren't.** Adding a nullable BigQuery
  column or changing a bucket lifecycle age is an in-place patch. Changing an
  immutable field (e.g. a dataset's `location`) cannot be patched — Config
  Connector will report the error rather than silently recreate. The day-2
  optional extension lets you see this firsthand.

---

## 6. File map

```
cymbal-landing-zones/
  README.md                         ← you are here
  prep.sh                           ← one-time token substitution
  templates/
    streaming-analytics/cymbal-clickstream/
      00-services.yaml              # OPTIONAL/unused: enable APIs (§7.2)
      10-iam.yaml                   # IAMServiceAccount + IAMPolicyMembers
      20-pubsub.yaml                # PubSubTopic + PubSubSubscription
      30-bigquery.yaml              # BigQueryDataset + BigQueryTable  ← day-2 target
      40-storage.yaml               # StorageBucket (raw archive)      ← day-2 target
    web-service-with-database/cymbal-portal/
      00-services.yaml              # OPTIONAL/unused
      10-iam.yaml                   # IAMServiceAccount + IAMPolicyMembers
      20-sql.yaml                   # SQLInstance + SQLDatabase + SQLUser (IAM auth)
      30-storage.yaml               # StorageBucket (uploads, versioned)
    build-and-artifact/cymbal-buildplatform/
      00-services.yaml              # OPTIONAL/unused
      10-iam.yaml                   # IAMServiceAccount + IAMPolicyMembers
      20-artifactregistry.yaml      # ArtifactRegistryRepository (DOCKER)
      30-pubsub.yaml                # PubSubTopic (build events)
      40-storage.yaml               # StorageBucket (artifacts, versioned)
  day2/
    README.md                       # change request + exact edits + verify
    30-bigquery.updated.yaml        # post-change table (adds utm_campaign)
    40-storage.updated.yaml         # post-change bucket (lifecycle 30 → 60 days)
```

---

## 7. Notes

### 7.1 `prep.sh`
The only script in the lab. It runs once, after cloning, and substitutes the
project-ID / region tokens in place — that's its entire job. No password is ever
generated by the lab; the portal database uses IAM database authentication (§
Step 4).

### 7.2 API enablement
The required APIs are assumed already enabled by lab provisioning — you don't
enable them. Each template still ships a `00-services.yaml`, **left commented
out**, documenting the Config-Connector-managed alternative (have CC own API
enablement as `serviceusage` `Service` resources). Using it requires the CC
controller identity to additionally hold `roles/serviceusage.serviceUsageAdmin`.
Note: query those objects with `kubectl get gcpservice` — the short name
`service` collides with the Kubernetes core Service kind.

---

## 8. Reference

- Config Connector overview — https://cloud.google.com/config-connector/docs/overview
- Resource reference (authoritative for kinds/fields/apiVersions) — https://cloud.google.com/config-connector/docs/reference/resources
- Namespaces and projects — https://cloud.google.com/config-connector/docs/concepts/namespaces-and-projects
