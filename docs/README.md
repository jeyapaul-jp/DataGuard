# DataGuard

Config-driven Python CLI for automating data quality checks in ETL pipelines.

## Install

```bash
pip install dataguard

# Optional extras for cloud file connectors
pip install 'dataguard[s3]'       # S3 / s3fs
pip install 'dataguard[azure]'    # Azure Data Lake / adlfs
pip install 'dataguard[gcs]'      # GCS / gcsfs

# Optional connectors
pip install 'dataguard[snowflake]'   # Snowflake
pip install 'dataguard[databricks]'  # Databricks SQL Warehouse
```

## Quickstart

Create a config file `checks.yaml`:

```yaml
connections:
  source:
    type: sql
    url: "postgresql+psycopg2://user:pass@host/db"
  target:
    type: sql
    url: "postgresql+psycopg2://user:pass@host/warehouse"

checks:
  - name: order_row_count
    check_type: row_count
    source:
      connection: source
      query: "SELECT * FROM orders"
    target:
      connection: target
      query: "SELECT * FROM orders_agg"
    threshold_pct: 1.0

  - name: order_duplicates
    check_type: duplicate
    source:
      connection: source
      query: "SELECT * FROM orders"
    key_columns: [order_id]

output:
  type: csv
  path: results/quality_results.csv
```

Run:

```bash
dataGuard run --config checks.yaml
```

## CLI Reference

```
dataGuard run --config <path> [--skip <check_name>]...
```

| Option | Description |
|--------|-------------|
| `--config` | Path to YAML or JSON config file (required) |
| `--skip` | Skip a named check; may be repeated (`--skip c1 --skip c2`) |

**Exit codes:**
- `0` — all checks passed or skipped; no errors
- `1` — one or more checks FAILED or produced an ERROR

## Config File Reference

### Connections

All connections support `${ENV_VAR}` substitution in any string field. Missing variables produce an `ERROR` result for each check that uses that connection.

#### SQL (SQLAlchemy URL)
```yaml
connections:
  my_db:
    type: sql
    url: "postgresql+psycopg2://user:${DB_PASS}@host/db"
```
Any [SQLAlchemy DBAPI URL](https://docs.sqlalchemy.org/en/20/core/engines.html) is accepted: `sqlite://`, `mssql+pyodbc://`, `oracle+cx_oracle://`, etc.

#### CSV
```yaml
connections:
  my_csv:
    type: csv
    path: "data/source.csv"       # local or cloud URI (s3://, abfs://, gs://)
```

#### Parquet
```yaml
connections:
  my_parquet:
    type: parquet
    path: "data/source.parquet"
```

#### JSON
```yaml
connections:
  my_json:
    type: json
    path: "data/source.json"
```

#### Snowflake
```yaml
connections:
  snow:
    type: snowflake
    account: "myaccount"
    user: "${SNOW_USER}"
    password: "${SNOW_PASSWORD}"   # or use private_key_path + private_key_passphrase
    database: "MY_DB"
    schema: "PUBLIC"
    warehouse: "COMPUTE_WH"
    role: "SYSADMIN"              # optional
```

#### Databricks
```yaml
connections:
  dbrx:
    type: databricks
    server_hostname: "dbc-xxx.azuredatabricks.net"
    http_path: "/sql/1.0/warehouses/abc123"
    access_token: "${DATABRICKS_TOKEN}"
```

### Check Types

All checks share these fields:

| Field | Default | Description |
|-------|---------|-------------|
| `name` | required | Unique identifier for the check |
| `check_type` | required | One of the types below |
| `enabled` | `true` | Set `false` to produce a SKIP record without running |

#### row_count
Compare row counts between source and target.

```yaml
- name: my_check
  check_type: row_count
  source:
    connection: src
    query: "SELECT * FROM orders"
  target:
    connection: tgt
    query: "SELECT * FROM orders_warehouse"
  threshold_pct: 2.0        # FAIL if |delta| exceeds this percentage
```

#### duplicate
Detect duplicate rows by key columns.

```yaml
- name: my_check
  check_type: duplicate
  source:
    connection: src
    query: "SELECT * FROM orders"
  key_columns: [order_id, line_item_id]
  sample_rows: 10           # number of sample duplicate rows to capture (default: 10)
```

#### null_threshold
Check null rate in a column does not exceed a threshold.

```yaml
- name: my_check
  check_type: null_threshold
  source:
    connection: src
    query: "SELECT * FROM orders"
  column: customer_email
  threshold_pct: 5.0        # FAIL if null% exceeds this
  sample_rows: 10
```

#### referential_integrity
Check that source column values all exist in target column (NULL source values are excluded).

```yaml
- name: my_check
  check_type: referential_integrity
  source:
    connection: src
    query: "SELECT * FROM orders"
  source_column: product_id
  target:
    connection: tgt
    query: "SELECT * FROM products"
  target_column: id
  sample_rows: 10
```

#### reconciliation
Aggregate a numeric column in source and target and compare.

```yaml
- name: my_check
  check_type: reconciliation
  source:
    connection: src
    query: "SELECT * FROM orders"
  source_column: amount
  target:
    connection: tgt
    query: "SELECT * FROM orders_warehouse"
  target_column: amount
  aggregate: sum            # sum | count | avg
  threshold_pct: 0.1        # FAIL if |delta%| exceeds this
```

### Output / Results Store

#### CSV file
```yaml
output:
  type: csv
  path: "results/quality.csv"
  overwrite: false          # default: false (append mode)
  output_fields:            # optional: limit which columns are written
    - run_id
    - check_name
    - status
    - timestamp
```

#### JSON file
```yaml
output:
  type: json
  path: "results/quality.json"
  overwrite: false
```

#### Database table
```yaml
output:
  type: database
  connection: results_db    # must reference a connection in the connections block
  table: dg_check_results
  output_fields: [run_id, check_name, status, actual_value, expected_value, delta]
```

**Required output fields:** `run_id`, `check_name`, `status` — these cannot be omitted from `output_fields`.

### Full Result Record Schema

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | UUID string | Shared by all checks in one `dataGuard run` invocation |
| `check_name` | string | Check name from config |
| `check_type` | string | Check type (row_count, duplicate, …) |
| `status` | string | PASS, FAIL, ERROR, SKIP |
| `actual_value` | number/null | Observed value (row count, null %, etc.) |
| `expected_value` | number/null | Expected/threshold value |
| `delta` | number/null | Numeric difference or percentage delta |
| `null_count` | integer/null | Null values encountered (ref integrity, reconciliation) |
| `source_connector_type` | string/null | Connector type for source |
| `target_connector_type` | string/null | Connector type for target |
| `timestamp` | ISO 8601 UTC | When the check was executed |
| `reason` | string/null | Error message for ERROR status |

Sample rows are written to a sidecar file alongside the results file (`<stem>_samples.<ext>` or `<table>_samples` for database output). Sidecar records include `run_id` and `check_name` plus the original data columns.

## Status Semantics

| Status | Meaning |
|--------|---------|
| PASS | Check ran and values are within threshold |
| FAIL | Check ran and threshold was exceeded |
| ERROR | Check could not run (connection failure, missing env var, runtime exception) |
| SKIP | Check was intentionally not run (`enabled: false` or `--skip` flag) |

## Environment Variables

Reference any environment variable in string config fields with `${VAR_NAME}`:

```yaml
connections:
  db:
    type: sql
    url: "postgresql+psycopg2://${DB_USER}:${DB_PASS}@${DB_HOST}/${DB_NAME}"
```

Missing variables do not cause a parse error. Instead, each check that uses that connection produces an `ERROR` result with a message listing the missing variable names.

## Dev Setup

```bash
git clone <repo>
cd dataguard
pip install -e '.[dev]'

# Run unit tests
pytest tests/unit/ -v

# Run all tests (requires pyarrow for Parquet)
pip install pyarrow
pytest tests/ -v

# Lint
ruff check dataguard/
mypy dataguard/
```
