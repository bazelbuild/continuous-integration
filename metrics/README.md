# Bazel CI Metrics Service

## SQL Setup

Run the following commands to initialize an empty database `metrics`:

NOTE: Double check that the following commands match the output of `git grep "CREATE TABLE"`.

```sql
USE metrics;

CREATE TABLE build_success (org VARCHAR(255), pipeline VARCHAR(255), build INT, linux VARCHAR(255), macos VARCHAR(255), windows VARCHAR(255), rbe VARCHAR(255), PRIMARY KEY(org, pipeline, build));
CREATE TABLE builds_per_change (org VARCHAR(255), pipeline VARCHAR(255), changelist INT, builds INT, PRIMARY KEY(org, pipeline, changelist));
CREATE TABLE critical_path (org VARCHAR(255), pipeline VARCHAR(255), build INT, wait_time_seconds FLOAT, run_time_seconds FLOAT, longest_task_name VARCHAR(255), longest_task_time_seconds FLOAT, result VARCHAR(255), PRIMARY KEY(org, pipeline, build));
CREATE TABLE flakiness (org VARCHAR(255), pipeline VARCHAR(255), build INT, target VARCHAR(255), passed_count INT, failed_count INT, PRIMARY KEY(org, pipeline, build, target));
CREATE TABLE mac_performance (org VARCHAR(255), pipeline VARCHAR(255), build INT, wait_time_seconds FLOAT, run_time_seconds FLOAT, skipped BOOL, PRIMARY KEY(org, pipeline, build));
CREATE TABLE pipeline_performance (org VARCHAR(255), pipeline VARCHAR(255), build INT, job VARCHAR(255), creation_time DATETIME, wait_time_seconds FLOAT, run_time_seconds FLOAT, skipped_tasks VARCHAR(255), PRIMARY KEY(org, pipeline, build, job));
CREATE TABLE platform_load (timestamp DATETIME, org VARCHAR(255), platform VARCHAR(255), waiting_jobs INT, running_jobs INT, PRIMARY KEY(org, timestamp, platform));
CREATE TABLE platform_significance (org VARCHAR(255), pipeline VARCHAR(255), total_builds INT, passing_builds INT, canceled_builds INT, setup_failed INT, linux_failures INT, macos_failures INT, windows_failures INT, rbe_failures INT, multi_platform_failures INT, PRIMARY KEY(org, pipeline));
CREATE TABLE platform_usage (org VARCHAR(255), pipeline VARCHAR(255), build INT, platform VARCHAR(255), usage_seconds FLOAT, PRIMARY KEY(org, pipeline, build, platform));
CREATE TABLE release_downloads (release_name VARCHAR(255), artifact VARCHAR(255), downloads INT, PRIMARY KEY(release_name, artifact));
CREATE TABLE worker_availability (timestamp DATETIME, org VARCHAR(255), platform VARCHAR(255), idle_count INT, busy_count INT, PRIMARY KEY(timestamp, org, platform));
```

## Dependencies

You need to install the following dependencies in order to build the service:

```bash
get github.com/buildkite/go-buildkite/buildkite
go get github.com/google/go-github/github
go get golang.org/x/oauth2
go get github.com/go-sql-driver/mysql
go get cloud.google.com/go/datastore
```

## Service Deployment

- `gcloud app deploy metrics/app.yaml --stop-previous-version`
- `gcloud app logs tail -s default`

## Running the service locally

The following steps allow you to run the service locally:

1. Ask an EngProd team member for access to a GCP service account.
2. Download the credentials for the service account (json file).
3. Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point at the credentials: `export GOOGLE_APPLICATION_CREDENTIALS="path/to/file.json"`
4. Download the [Cloud SQL-Proxy](https://cloud.google.com/sql/docs/mysql/sql-proxy).
5. Start the proxy via `./cloud_sql_proxy -instances="bazel-untrusted:europe-west1:metrics"=tcp:3306`
6. Run the app via `go run metrics/main.go metrics/settings.go --test=true`. The `test`parameter means that all metrics are collected immediately, and all results are published to stdout instead of being written to Cloud SQL.
