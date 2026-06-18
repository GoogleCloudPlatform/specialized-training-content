# Day-2 Update — a change request lands

> **Marketing now wants a `utm_campaign` field on every event, and wants raw
> events kept 30 days longer for a seasonal analysis.**

This is the headline moment of the lab. You'll make two edits in the
`cymbal-clickstream` namespace and re-apply them with the **same `kubectl apply`
verb you used to create the resources**. Config Connector mutates the **existing**
table and bucket **in place** — neither is recreated, and the table's data
survives.

Both edits are already baked into the `*.updated.yaml` files in this directory,
which are full, applyable replacements for the corresponding clickstream
template files. You can either **hand-edit the originals** (to feel the change)
or just **apply this directory**.

---

## Edit 1 — add a nullable column to `BigQueryTable.events`

Append one column to the table's `spec.schema` JSON array. A **`NULLABLE`** column
is an allowed in-place patch: Config Connector ALTERs the existing table, and
existing rows simply get `NULL` for the new column.

**Before** (`templates/streaming-analytics/cymbal-clickstream/30-bigquery.yaml`):

```yaml
  schema: |
    [
      {"name":"event_id","type":"STRING","mode":"REQUIRED"},
      {"name":"event_type","type":"STRING","mode":"REQUIRED"},
      {"name":"event_timestamp","type":"TIMESTAMP","mode":"REQUIRED"},
      {"name":"page_url","type":"STRING","mode":"NULLABLE"},
      {"name":"user_pseudo_id","type":"STRING","mode":"NULLABLE"}
    ]
```

**After** (`day2/30-bigquery.updated.yaml`):

```diff
       {"name":"page_url","type":"STRING","mode":"NULLABLE"},
-      {"name":"user_pseudo_id","type":"STRING","mode":"NULLABLE"}
+      {"name":"user_pseudo_id","type":"STRING","mode":"NULLABLE"},
+      {"name":"utm_campaign","type":"STRING","mode":"NULLABLE"}
     ]
```

> Why this is allowed: BigQuery permits **adding** a `NULLABLE` (or `REPEATED`)
> column to an existing table. Removing a column, or adding a `REQUIRED` one,
> would not be an in-place patch.

---

## Edit 2 — extend retention on `StorageBucket.clickstream-raw`

Change the lifecycle rule's `condition.age` from `30` to `60`. Also a pure
in-place reconfiguration of the **same** bucket.

**Before** (`templates/streaming-analytics/cymbal-clickstream/40-storage.yaml`):

```yaml
  lifecycleRule:
    - action:
        type: "Delete"
      condition:
        age: 30
```

**After** (`day2/40-storage.updated.yaml`):

```diff
   lifecycleRule:
     - action:
         type: "Delete"
       condition:
-        age: 30
+        age: 60
```

---

## Apply

> If you haven't run `prep.sh`, the bucket file here still carries the
> `${CLICKSTREAM_PROJECT_ID}` / `${REGION}` tokens. `prep.sh` already rewrote
> `day2/40-storage.updated.yaml` in place along with the templates, so after the
> normal lab setup this just works.

```bash
kubectl apply -f day2/
```

You'll see `configured` (not `created`) for both objects — proof you patched
existing resources rather than making new ones:

```
bigquerytable.bigquery.cnrm.cloud.google.com/events configured
bigquerydataset.bigquery.cnrm.cloud.google.com/clickstream unchanged
storagebucket.storage.cnrm.cloud.google.com/clickstream-raw configured
```

---

## Verify

**1. Both resources went `Ready` again after the update:**

```bash
kubectl describe bigquerytable/events       -n cymbal-clickstream | sed -n '/Status/,$p'
kubectl describe storagebucket/clickstream-raw -n cymbal-clickstream | sed -n '/Status/,$p'
# or simply:
kubectl wait --for=condition=Ready --timeout=120s -n cymbal-clickstream \
  bigquerytable/events storagebucket/clickstream-raw
```

**2. The live table schema now includes `utm_campaign`:**

```bash
bq show --schema --format=prettyjson "$CLICKSTREAM_PROJECT_ID:clickstream.events"
```

**3. The live bucket lifecycle age is now `60`:**

```bash
gcloud storage buckets describe "gs://${CLICKSTREAM_PROJECT_ID}-clickstream-raw" \
  --format="value(lifecycle.rule)"
```

**4. (The key check) Neither resource was recreated.** The Config Connector
object's `metadata.uid` and creation timestamp are unchanged from before the
update:

```bash
kubectl get bigquerytable/events       -n cymbal-clickstream -o jsonpath='{.metadata.uid} {.metadata.creationTimestamp}{"\n"}'
kubectl get storagebucket/clickstream-raw -n cymbal-clickstream -o jsonpath='{.metadata.uid} {.metadata.creationTimestamp}{"\n"}'
```

(Compare against the values you'd capture before applying — they match. The
resource changed; it was not replaced.)

---

## Optional extension — watch an immutable field reject the patch

*Not part of the happy path.* For contrast, try a change Config Connector
**cannot** apply in place, and watch it fail honestly instead of recreating the
resource.

Edit the dataset's immutable `location` in
`templates/streaming-analytics/cymbal-clickstream/30-bigquery.yaml`:

```diff
 spec:
-  location: "US"
+  location: "EU"
   friendlyName: "Clickstream events"
```

Apply it and inspect the result:

```bash
kubectl apply -f templates/streaming-analytics/cymbal-clickstream/30-bigquery.yaml
kubectl describe bigquerydataset/clickstream -n cymbal-clickstream
```

The object goes to an `UpdateFailed` / non-`Ready` condition with a message about
an immutable field — Config Connector will **not** silently destroy and rebuild
the dataset to satisfy the edit. One mutable change (Edit 1/2) beside one
immutable change is the honest picture of the reconciliation model.

> **Revert** when done so teardown is clean:
> ```bash
> git checkout -- templates/streaming-analytics/cymbal-clickstream/30-bigquery.yaml
> # (re-run prep.sh if the checkout restored any tokens)
> kubectl apply -f templates/streaming-analytics/cymbal-clickstream/30-bigquery.yaml
> ```
