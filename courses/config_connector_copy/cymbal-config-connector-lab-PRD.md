# PRD: Cymbal Landing-Zone Templates with Config Connector

**Deliverable:** Config Connector manifests, a scenario README, and a documented day-2 update. Applied to a GKE cluster with the Config Connector add-on, these manifests stand up three landing zones across three Google Cloud projects and then demonstrate an in-place update.

The student drives the lab by hand:

- Clone the repo and run a one-time token substitution.
- Apply each template — a directory of manifests — and review the cloud resources it creates.
- Perform the day-2 edit.
- Delete the templates.

---

## 1. Background & scenario

Cymbal's **platform engineering team** has adopted Config Connector to replace inconsistent, hand-built ("click-ops") infrastructure. Instead of provisioning each project by hand, they've codified a catalog of **reusable landing-zone templates**. There is one template per application archetype Cymbal repeatedly builds. Application teams onboard by getting a fresh project provisioned from the matching template.

The student plays a member of that platform team. Working from a single GKE cluster, they:

- apply each template into its own namespace, creating resources across three projects, and
- handle a mid-quarter change request.

The teaching point is that one Config Connector control plane fans out to three projects. What makes that happen is the per-namespace project annotation, not the number of applies.

All three templates share a common skeleton:

- enable APIs,
- create a workload identity,
- grant it scoped roles, then
- provision the workload.

They differ only in that last workload layer. The README and file tree should make this shared shape visible side by side.

### 1.1 The three templates and their onboarding teams

| Template | Namespace | Why a fresh project |
|---|---|---|
| **streaming-analytics** | `cymbal-clickstream` | Marketing's website-event capture is one analyst's hand-built BigQuery tables and a stray function — undocumented and cost-entangled with another team's project. The mandate: a real clickstream pipeline in its own project, abandoning the old setup. |
| **web-service-with-database** | `cymbal-portal` | A new customer self-service portal. Its own project gives blast-radius isolation (a portal bug can't reach unrelated data) and lets the app team own its database without filing tickets against a shared project. |
| **build-and-artifact** | `cymbal-buildplatform` | Container images and build artifacts are scattered across teams' personal projects with inconsistent permissions. Security wants one locked-down project with a single CI identity and an audited registry. |

State the general rationale once for students — a fresh project gives:

- a clean blast radius,
- its own IAM boundary, and
- separate billing and quota.

Config Connector then makes that per-project baseline reproducible instead of a snowflake.

---

## 2. Goals / non-goals

**Goals**

- One control plane fans out to **three** projects via the per-namespace annotation.
- Each template is a coherent, realistic landing zone — not a grab-bag of resources.
- A **day-2 in-place update** mutates an existing resource without recreating it.
- The shared template skeleton is visually obvious in the file tree.
- Teach the reconciliation model: desired state in YAML, change = edit + re-apply.

**Non-goals**

- Installing the Config Connector add-on (assumed pre-installed; see §3).
- Production-grade networking, private IP, HA, or backups.
- Real workloads on the resources (no Pods using the database, no event producers).
- Cross-project resource references (deferred — the simpler Plan A, not the cross-tier plan).

---

## 3. Environment & assumptions

Lab provisioning handles the cluster and the Config Connector installation. The agent does **not** generate them. State these prerequisites in the README as assumptions:

- A GKE Standard cluster with the **Config Connector add-on installed and healthy**.
- **Cluster mode** — one controller identity for the whole cluster.
- That controller's Google service account holds `roles/owner` on **all three** managed projects.
- Three managed projects with **arbitrary IDs** (e.g. `qwiklabs-gcp-01-a1b2c3d4e5f6`), created during lab setup.
- Three namespaces (`cymbal-clickstream`, `cymbal-portal`, `cymbal-buildplatform`) **already exist**, each annotated with `cnrm.cloud.google.com/project-id` for its project.

### 3.1 Project-ID handling and substitution

Manifests must be portable across arbitrary project IDs — never hardcode them.

A few manifests still need a literal project ID:

- `IAMPolicyMember`s whose `resourceRef` points at the `Project`.
- Globally-unique bucket names.

These use substitution tokens: `${CLICKSTREAM_PROJECT_ID}`, `${PORTAL_PROJECT_ID}`, `${BUILD_PROJECT_ID}`, and `${REGION}` (default `us-central1`).

Committed manifests stay raw, with tokens intact. Substitution happens once, in `prep.sh` (§7.1), which rewrites the token files **in place** so every later `kubectl apply` uses plain, ready manifests. The student exports the project IDs, then runs the script:

```bash
export CLICKSTREAM_PROJECT_ID=... PORTAL_PROJECT_ID=... BUILD_PROJECT_ID=... REGION=us-central1
# inside prep.sh — rewrite the only files that carry tokens (IAM, buckets, and
# the day2 storage update), in place. Iterate newline-delimited, NOT with
# `grep -lZ | xargs -0`: BSD grep (macOS) does NOT NUL-separate the -l file
# list, so the -0 pipeline silently processes zero files there. Restrict
# envsubst to our tokens so any stray `$` is left untouched.
TOKENS='${CLICKSTREAM_PROJECT_ID} ${PORTAL_PROJECT_ID} ${BUILD_PROJECT_ID} ${REGION}'
grep -rl '\${' templates/ day2/ | while IFS= read -r f; do
  envsubst "$TOKENS" < "$f" > "$f.tmp" && mv "$f.tmp" "$f"
done
```

After `prep.sh` runs the tokens are consumed; no later step touches `envsubst`. (Re-cloning or `git checkout -- templates/ day2/` restores the tokens to start over.)

### 3.2 Version validation (important)

Config Connector CRD `apiVersion`s and field names drift between releases. Don't trust any value in this PRD verbatim. **Validate every kind and field against the [current CRDs](https://github.com/GoogleCloudPlatform/k8s-config-connector/tree/master/config/crds/resources).** Treat a field named here as the intent; the live CRD is the source of truth for exact spelling.

### 3.3 Build findings (validated against the live CRDs)

The first build of these artifacts validated every kind/field against the live
Config Connector reference. Results, so the next author doesn't repeat the work:

- **Confirmed accurate as written:** all `apiVersion`s are `v1beta1`; the three
  annotation spellings (§4); `spec.schema` as stringified JSON; `lifecycleRule`
  shape; `versioning.enabled` nesting; `uniformBucketLevelAccess` as a direct
  bool; `SQLUser.type: CLOUD_IAM_SERVICE_ACCOUNT` with no password.
- **Corrections folded into the spec below (were inaccurate in earlier drafts):**
  - Project-scoped IAM `resourceRef.external` needs the **`projects/` prefix** —
    `external: "projects/${…_PROJECT_ID}"`, not bare `${…_PROJECT_ID}` (§4, §6).
  - `SQLInstance` has **no** instance-level `deletionProtection` field — only
    `spec.settings.deletionProtectionEnabled` exists (§6.2, §8).
  - The IAM-SA `SQLUser` username is the SA email with the
    **`.gserviceaccount.com` suffix stripped** (`<sa>@<project>.iam`), set via
    `spec.resourceID`; CC does not derive it (§6.2).
  - `prep.sh`'s substitution loop must not rely on `grep -lZ | xargs -0` — BSD
    grep (macOS) doesn't NUL-separate the `-l` list, so it silently no-ops there
    (§3.1).

---

## 4. Naming & manifest conventions

- `metadata.name`: descriptive of purpose (e.g. `clickstream-events`, `portal-app`, `ci-runner`).
- Buckets need globally-unique cloud names, so set `spec.resourceID` with a project-ID token (e.g. `${CLICKSTREAM_PROJECT_ID}-clickstream-raw`). The `metadata.name` stays simple.
- Every object carries two labels for filtering and side-by-side comparison:
  - `cymbal.dev/template: <streaming-analytics|web-service-with-database|build-and-artifact>`
  - `cymbal.dev/tenant: <clickstream|portal|buildplatform>`
- Every object sets a **reconciliation interval of 60 seconds** via the `cnrm.cloud.google.com/reconcile-interval-in-seconds: "60"` annotation, so Config Connector re-reconciles desired vs. actual state every minute. (Validate the exact annotation spelling against the live CRD docs per §3.2.)
- `IAMPolicyMember` members use `memberFrom.serviceAccountRef` (the `IAMServiceAccount` object by name), not a hardcoded email — so no project ID leaks into the member string.
- All IAM bindings are **project-scoped** (`resourceRef: {kind: Project, external: "projects/${…_PROJECT_ID}"}` — note the required `projects/` prefix), for lab simplicity.
- File numbering encodes the shared skeleton: `00-services`, `10-iam`, then workload files `20-…`, `30-…`, `40-…`. It's for human readability — Config Connector reconciles eventually and retries, so strict ordering isn't required for correctness.

---

## 5. Deliverables & directory layout

Generate exactly this tree:

```
cymbal-landing-zones/
  README.md                         # scenario doc (see §1, §6, §8) + the full student walkthrough (§7)
  prep.sh                           # one-time token substitution (see §7.1)
  templates/
    streaming-analytics/cymbal-clickstream/
      00-services.yaml              # OPTIONAL/unused (see §7.2): enable APIs via serviceusage Service
      10-iam.yaml                   # IAMServiceAccount + IAMPolicyMembers
      20-pubsub.yaml                # PubSubTopic + PubSubSubscription
      30-bigquery.yaml              # BigQueryDataset + BigQueryTable
      40-storage.yaml               # StorageBucket (raw archive, lifecycle rule)
    web-service-with-database/cymbal-portal/
      00-services.yaml              # OPTIONAL
      10-iam.yaml                   # IAMServiceAccount + IAMPolicyMembers
      20-sql.yaml                   # SQLInstance + SQLDatabase + SQLUser (IAM auth, no password)
      30-storage.yaml               # StorageBucket (uploads)
    build-and-artifact/cymbal-buildplatform/
      00-services.yaml              # OPTIONAL
      10-iam.yaml                   # IAMServiceAccount + IAMPolicyMembers
      20-artifactregistry.yaml      # ArtifactRegistryRepository (DOCKER)
      30-pubsub.yaml                # PubSubTopic (build events)
      40-storage.yaml               # StorageBucket (build artifacts, versioned)
  day2/
    README.md                       # the change request narrative + exact edits + apply/verify steps
    30-bigquery.updated.yaml        # post-change BigQueryTable (adds utm_campaign)
    40-storage.updated.yaml         # post-change StorageBucket (lifecycle 30 -> 60 days)
```

The `day2/*.updated.yaml` files are full, applyable replacements for the corresponding clickstream files, so a student can either hand-edit the originals or `kubectl apply -f day2/`. The `day2/README.md` must show the before/after diff inline.

---

## 6. Template resource specifications

For all resources: omit the project field (inherited from the namespace annotation); apply the labels from §4; validate fields per §3.2.

### 6.1 streaming-analytics → namespace `cymbal-clickstream`

- **IAMServiceAccount** `clickstream-ingest` — `spec.displayName: "Clickstream ingest pipeline"`.
- **IAMPolicyMembers** — member `memberFrom.serviceAccountRef: {name: clickstream-ingest}`; all project-scoped via `resourceRef: {kind: Project, external: "projects/${CLICKSTREAM_PROJECT_ID}"}`:
  - `roles/pubsub.publisher`
  - `roles/bigquery.dataEditor`
  - `roles/bigquery.jobUser`
  - `roles/storage.objectAdmin`
- **PubSubTopic** `clickstream-events` — minimal spec; optionally `messageRetentionDuration: "86400s"`.
- **PubSubSubscription** `clickstream-events-sub`
  - `spec.topicRef: {name: clickstream-events}`
  - `ackDeadlineSeconds: 20`
  - `messageRetentionDuration: "86400s"`
- **BigQueryDataset** `clickstream`
  - `spec.location: "${REGION}"` (or `US`)
  - `friendlyName: "Clickstream events"`
  - `description: "Raw website clickstream events"`
- **BigQueryTable** `events` — *the resource the day-2 update mutates.*
  - `spec.datasetRef: {name: clickstream}`
  - `friendlyName: "events"`
  - `spec.schema`: a **stringified JSON array** of column definitions; initial schema below.
  - *Optional:* `timePartitioning: {type: "DAY", field: "event_timestamp"}` for realism.
  ```json
  [
    {"name":"event_id","type":"STRING","mode":"REQUIRED"},
    {"name":"event_type","type":"STRING","mode":"REQUIRED"},
    {"name":"event_timestamp","type":"TIMESTAMP","mode":"REQUIRED"},
    {"name":"page_url","type":"STRING","mode":"NULLABLE"},
    {"name":"user_pseudo_id","type":"STRING","mode":"NULLABLE"}
  ]
  ```
- **StorageBucket** `clickstream-raw` — *day-2 changes the lifecycle age (30 → 60).*
  - `spec.resourceID: "${CLICKSTREAM_PROJECT_ID}-clickstream-raw"`
  - `location: "${REGION}"`
  - `uniformBucketLevelAccess: true`
  - `publicAccessPrevention: "enforced"`
  - `lifecycleRule`: `action: {type: "Delete"}`, `condition: {age: 30}`

### 6.2 web-service-with-database → namespace `cymbal-portal`

- **IAMServiceAccount** `portal-app` — `displayName: "Portal application"`.
- **IAMPolicyMembers** — member `memberFrom.serviceAccountRef: {name: portal-app}`; all project-scoped via `resourceRef: {kind: Project, external: "projects/${PORTAL_PROJECT_ID}"}`:
  - `roles/cloudsql.client` — connect through the Cloud SQL Auth Proxy.
  - `roles/cloudsql.instanceUser` — the login privilege for IAM database auth.
  - `roles/storage.objectAdmin`
- **SQLInstance** `portal-db` — *takes ~5–10 min to go `Ready`; pace the lab around this (an honest illustration of eventual consistency).*
  - `spec.databaseVersion: "POSTGRES_15"`
  - `region: "${REGION}"`
  - `settings.databaseFlags`: a **list** of `{name, value}` — set `{name: "cloudsql.iam_authentication", value: "on"}` (enables IAM database auth). Not a map.
  - `settings: {tier: "db-custom-1-3840", availabilityType: "ZONAL", deletionProtectionEnabled: false, backupConfiguration: {enabled: false}}`
  - Note: SQLInstance has **no** instance-level `deletionProtection` field — `settings.deletionProtectionEnabled: false` above is the only one.
  - *Alternative (faster/cheaper):* MySQL 8.0 with `tier: db-f1-micro`. Default to Postgres; mention this in a comment.
- **SQLDatabase** `portal` — `spec.instanceRef: {name: portal-db}`.
- **SQLUser** `portal-app` — *IAM service-account user; no password anywhere.*
  - `spec.instanceRef: {name: portal-db}`
  - `spec.type: "CLOUD_IAM_SERVICE_ACCOUNT"`
  - `spec.resourceID: "portal-app@${PORTAL_PROJECT_ID}.iam"` — the SA email with the **`.gserviceaccount.com` suffix stripped** (a Cloud SQL requirement for IAM-SA users). CC does **not** derive this; set it explicitly. Omit `spec.password`.
- **StorageBucket** `portal-uploads`
  - `spec.resourceID: "${PORTAL_PROJECT_ID}-portal-uploads"`
  - `location: "${REGION}"`
  - `uniformBucketLevelAccess: true`
  - `publicAccessPrevention: "enforced"`
  - `versioning: {enabled: true}`

### 6.3 build-and-artifact → namespace `cymbal-buildplatform`

- **IAMServiceAccount** `ci-runner` — `displayName: "CI build runner"`.
- **IAMPolicyMembers** — member `memberFrom.serviceAccountRef: {name: ci-runner}`; all project-scoped via `resourceRef: {kind: Project, external: "projects/${BUILD_PROJECT_ID}"}`:
  - `roles/artifactregistry.writer`
  - `roles/storage.admin`
  - `roles/pubsub.publisher`
- **ArtifactRegistryRepository** `cymbal-images`
  - `spec.format: "DOCKER"`
  - `location: "${REGION}"`
  - `description: "Cymbal container images"`
- **PubSubTopic** `build-events` — minimal spec.
- **StorageBucket** `build-artifacts`
  - `spec.resourceID: "${BUILD_PROJECT_ID}-build-artifacts"`
  - `location: "${REGION}"`
  - `uniformBucketLevelAccess: true`
  - `publicAccessPrevention: "enforced"`
  - `versioning: {enabled: true}`

---

## 7. Student walkthrough

The student runs every `kubectl apply` and `kubectl delete` by hand — that is the point of the lab. The repo ships only manifests, a README, and the `day2/` files. The README lays out this sequence, with literal commands and a "review what you just made" checkpoint after each apply:

1. **Clone** the repo and `cd` into it.
2. **Run `prep.sh`** once. Export `CLICKSTREAM_PROJECT_ID`, `PORTAL_PROJECT_ID`, `BUILD_PROJECT_ID`, and `REGION` (default `us-central1`), then run `./prep.sh` to substitute the project-ID tokens (§7.1).
3. **Apply template 1** — `kubectl apply -f templates/streaming-analytics/cymbal-clickstream/`. Review: `kubectl get`/`describe` until `Ready`, then confirm the resources in the project via `gcloud`/console (§9).
4. **Apply template 2** (`cymbal-portal`) and review. The SQL instance takes ~5–10 min to go `Ready` (see §6.2).
5. **Apply template 3** (`cymbal-buildplatform`) and review.
6. **Cross-project review** — confirm resources now exist across all three projects from this one cluster (the fan-out teaching point).
7. **Day-2 operation** — edit + re-apply per §9, then review the mutated table and bucket.
8. **Delete the templates** — `kubectl delete -f …` each directory, in any order. Confirm the cloud resources are gone (§8). Leave the namespaces and the CC add-on in place.

### 7.1 `prep.sh`
`prep.sh` is the only script in the lab. It runs once, after cloning, and substitutes the project-ID tokens in place (§3.1) — that is its entire job.

The portal database uses **IAM database authentication** (§6.2): the `portal-app` service account authenticates by identity, so no DB password is ever generated, stored, or committed. The README should call this out as the modern, password-free pattern — workload identity instead of a shared secret.

### 7.2 API enablement
Assume the required APIs (`pubsub`, `bigquery`, `storage`, `sqladmin`, `artifactregistry`) are already enabled on all three projects by lab provisioning. The student does not enable them.

The agent should still generate a `00-services.yaml` (`serviceusage` `Service` resources) per template, **left commented/unused**. It documents the Config-Connector-managed alternative for authors who want it — note it requires the CC identity to hold `roles/serviceusage.serviceUsageAdmin`.

---

## 8. Deletion / lifecycle policy

Deleting a Kubernetes object must delete its underlying GCP resource. Use **default deletion behavior** — no `cnrm.cloud.google.com/deletion-policy: abandon` annotation anywhere. The manifest owns the resource; the YAML is the source of truth.

No resource is deletion-protected. In particular, set `settings.deletionProtectionEnabled: false` on the SQL instance, so iteration and teardown are never blocked. (There is no instance-level `deletionProtection` field on the SQLInstance CRD — `settings.deletionProtectionEnabled` is the only one.)

This is safe because the lab projects are ephemeral and torn down wholesale at the end — there is no orphaned-resource risk. State this decision in the README.

---

## 9. Day-2 update (the required update operation)

Both edits are in the `cymbal-clickstream` namespace, re-applied with `kubectl apply` — the same verb used to create.

**Framing** (put in `day2/README.md`): *"Marketing now wants a `utm_campaign` field on every event, and wants raw events kept 30 days longer for a seasonal analysis."*

**Edit 1 — add a nullable column to `BigQueryTable.events`.** Append to the `spec.schema` JSON:
```json
{"name":"utm_campaign","type":"STRING","mode":"NULLABLE"}
```
A `NULLABLE` column is an allowed in-place patch. Config Connector mutates the **existing** table; the table and its data survive. This is the headline moment — the resource changes, it is not recreated.

**Edit 2 — extend retention on `StorageBucket.clickstream-raw`.** Change the lifecycle `condition.age` from `30` to `60`. Also in-place.

`day2/README.md` must include:

- the narrative,
- the before/after diff for both edits,
- the apply command (`kubectl apply -f day2/`), and
- verification: re-inspect the live table schema and bucket lifecycle via `gcloud`/console, and `kubectl describe` to show each resource went `Ready` after the update.

**Optional extension (mark as optional, not part of the happy path):** have students attempt a *disallowed* change — e.g. editing `BigQueryDataset.location` — and watch Config Connector fail to patch an immutable field in place. One mutable change beside one immutable change teaches reconciliation honestly.

---

## 10. Acceptance checklist

This is a checklist for the **lab author** to verify the generated artifacts by hand. Walk through it after the agent produces the deliverables. The artifacts are complete when:

- [ ] Every manifest passes `kubectl apply --dry-run=server` against a cluster with the CC add-on (after token substitution).
- [ ] After applying all three templates, every Config Connector object across the three namespaces reaches `Ready: True` (`kubectl wait --for=condition=Ready --timeout=900s …`; the SQL instance is the long pole).
- [ ] The resources are visible in each project via `gcloud` (buckets, BigQuery datasets/tables, Pub/Sub topics, Artifact Registry repos, SQL instances) — confirming the cross-project fan-out from one cluster.
- [ ] Applying `day2/` mutates the existing BigQuery table schema (now includes `utm_campaign`) and the bucket lifecycle age (now `60`) **without** recreating either resource (`metadata.uid` / creation timestamp unchanged).
- [ ] The three template directories visibly share the `00/10/20…` skeleton and differ only in the workload files.
- [ ] No project IDs or other environment-specific values are hardcoded in committed manifests.
- [ ] Every manifest carries the `cnrm.cloud.google.com/reconcile-interval-in-seconds: "60"` annotation.
- [ ] `README.md` documents the scenario (§1), the assumptions (§3), the deletion policy (§8), the hands-on walkthrough (§7) with literal commands, and the day-2 change.

---

## 11. Reference

- Config Connector overview: https://docs.cloud.google.com/config-connector/docs/overview
- Supported resource reference (authoritative for kinds/fields/apiVersions): https://docs.cloud.google.com/config-connector/docs/reference/resources
- Namespaces and projects: https://docs.cloud.google.com/config-connector/docs/concepts/namespaces-and-projects
