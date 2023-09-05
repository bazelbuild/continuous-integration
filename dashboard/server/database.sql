CREATE EXTENSION IF NOT EXISTS citext;

CREATE TABLE json_state
(
    key       TEXT PRIMARY KEY,
    timestamp TIMESTAMPTZ,
    data      JSONB NOT NULL
);

--
-- Table that stores the raw issues data fetched from Github
--
CREATE TABLE github_issue_data
(
    owner        TEXT        NOT NULL,
    repo         TEXT        NOT NULL,
    issue_number INTEGER     NOT NULL,
    timestamp    TIMESTAMPTZ NOT NULL,
    etag         TEXT        NOT NULL,
    data         JSONB       NOT NULL,
    PRIMARY KEY (owner, repo, issue_number)
);

CREATE OR REPLACE FUNCTION tf_regenerate_github_issue()
    RETURNS TRIGGER
    LANGUAGE plpgsql
AS
$$
BEGIN
    IF NEW IS NULL THEN
        DELETE FROM github_issue WHERE owner = OLD.owner AND repo = OLD.repo AND issue_number = OLD.issue_number;
    ELSE
        CALL regenerate_github_issue(NEW.owner, NEW.repo, NEW.issue_number);
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER t_regenerate_github_issue
    AFTER INSERT OR UPDATE OR DELETE
    ON github_issue_data
    FOR EACH ROW
EXECUTE PROCEDURE tf_regenerate_github_issue();

--
-- Table that stores issues generated from github_issue_data automatically by trigger
--
CREATE TABLE github_issue
(
    owner           TEXT        NOT NULL,
    repo            TEXT        NOT NULL,
    issue_number    INTEGER     NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL,
    state           TEXT        NOT NULL,
    is_pull_request BOOL        NOT NULL,
    title           TEXT        NOT NULL,
    body            TEXT        NOT NULL,
    milestone       TEXT        NOT NULL,
    labels          CITEXT[]    NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL,
    updated_at      TIMESTAMPTZ,
    closed_at       TIMESTAMPTZ,
    PRIMARY KEY (owner, repo, issue_number)
);

CREATE UNIQUE INDEX ON github_issue (owner, repo, issue_number);
CREATE INDEX ON github_issue (state);
CREATE INDEX ON github_issue (milestone);
CREATE INDEX ON github_issue USING GIN (labels);
CREATE INDEX ON github_issue (is_pull_request);
CREATE INDEX ON github_issue (created_at);
CREATE INDEX ON github_issue (updated_at);
CREATE INDEX ON github_issue (closed_at);

CREATE OR REPLACE PROCEDURE regenerate_github_issue(target_owner TEXT, target_repo TEXT, target_issue_number INTEGER)
    LANGUAGE plpgsql
AS
$$
BEGIN
    INSERT INTO github_issue(owner,
                             repo,
                             issue_number,
                             timestamp,
                             state,
                             is_pull_request,
                             title,
                             body,
                             milestone,
                             labels,
                             created_at,
                             updated_at,
                             closed_at)
    WITH github_issue_label AS (
        SELECT owner, repo, issue_number, jsonb_array_elements(data -> 'labels') ->> 'name' AS label
        FROM github_issue_data
    ),
         github_issue_labels AS (
             SELECT owner, repo, issue_number, array_agg(label) AS labels
             FROM github_issue_label
             GROUP BY owner, repo, issue_number
         )
    SELECT i.owner,
           i.repo,
           i.issue_number,
           i.timestamp,
           i.data ->> 'state',
           i.data -> 'pull_request' IS NOT NULL,
           COALESCE(i.data ->> 'title', ''),
           COALESCE(i.data ->> 'body', ''),
           COALESCE(TRIM(i.data -> 'milestone' ->> 'title'), ''),
           COALESCE(il.labels, '{}'),
           (data ->> 'created_at')::TIMESTAMPTZ,
           (data ->> 'updated_at')::TIMESTAMPTZ,
           (data ->> 'closed_at')::TIMESTAMPTZ
    FROM github_issue_data i
             LEFT JOIN github_issue_labels il
                       ON i.owner = il.owner AND i.repo = il.repo AND i.issue_number = il.issue_number
    WHERE i.owner = target_owner
      AND i.repo = target_repo
      AND i.issue_number = target_issue_number
    ON CONFLICT (owner, repo, issue_number) DO UPDATE
        SET timestamp       = excluded.timestamp,
            state           = excluded.state,
            is_pull_request = excluded.is_pull_request,
            title           = excluded.title,
            body            = excluded.body,
            milestone       = excluded.milestone,
            labels          = excluded.labels,
            created_at      = excluded.created_at,
            updated_at      = excluded.updated_at,
            closed_at       = excluded.closed_at;
END;
$$;


CREATE VIEW github_issue_label AS
SELECT owner, repo, issue_number, unnest(labels) AS label
FROM github_issue;


CREATE VIEW github_label AS
WITH github_label AS (
    SELECT owner, repo, unnest(labels) AS name
    FROM github_issue
)
SELECT owner, repo, name
FROM github_label
GROUP BY owner, repo, name;


CREATE TABLE github_team
(
    owner      TEXT,
    repo       TEXT,
    label      TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    name       TEXT,
    team_owner TEXT,
    more_team_owners  TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    PRIMARY KEY (owner, repo, label)
);


CREATE TABLE github_issue_query
(
    owner      TEXT,
    repo       TEXT,
    id         TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    name       TEXT,
    query      TEXT        NOT NULL,
    PRIMARY KEY (owner, repo, id)
);


CREATE TABLE github_issue_query_count_task
(
    owner      TEXT,
    repo       TEXT,
    query_id   TEXT,
    period     TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (owner, repo, query_id, period)
);


CREATE TABLE github_issue_query_count_task_result
(
    owner     TEXT,
    repo      TEXT,
    query_id  TEXT,
    period    TEXT,
    timestamp TIMESTAMPTZ,
    count     int,
    PRIMARY KEY (owner, repo, query_id, period, timestamp)
);

CREATE TABLE github_team_table
(
    owner           TEXT,
    repo            TEXT,
    id              TEXT,
    created_at      TIMESTAMPTZ NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL,
    name            TEXT        NOT NULL,
    PRIMARY KEY (owner, repo, id)
);

CREATE TABLE github_team_table_header
(
    owner      TEXT,
    repo       TEXT,
    table_id   TEXT,
    id         TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    seq        INT         NOT NULL,
    name       TEXT        NOT NULL,
    query      TEXT        NOT NULL,
    PRIMARY KEY (owner, repo, table_id, id)
);
CREATE UNIQUE INDEX ON github_team_table_header (owner, repo, table_id, id, seq);

CREATE TABLE github_repo
(
    owner                 TEXT,
    repo                  TEXT,
    created_at            TIMESTAMPTZ NOT NULL,
    updated_at            TIMESTAMPTZ NOT NULL,
    action_owner          TEXT DEFAULT NULL,
    is_team_label_enabled BOOL DEFAULT FALSE,
    PRIMARY KEY (owner, repo)
);

CREATE TABLE github_issue_status
(
    owner               TEXT,
    repo                TEXT,
    issue_number        INTEGER     NOT NULL,
    status              TEXT,
    action_owner        TEXT,
    more_action_owners  TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    updated_at          TIMESTAMPTZ NOT NULL,
    expected_respond_at TIMESTAMPTZ,
    last_notified_at    TIMESTAMPTZ,
    next_notify_at      TIMESTAMPTZ,
    checked_at          TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (owner, repo, issue_number)
);
CREATE INDEX ON github_issue_status (status);
CREATE INDEX ON github_issue_status (action_owner);
CREATE INDEX ON github_issue_status USING GIN (more_action_owners);
CREATE INDEX ON github_issue_status (expected_respond_at);
CREATE INDEX ON github_issue_status (next_notify_at);

CREATE TABLE github_user
(
    username TEXT,
    email TEXT NOT NULL,
    PRIMARY KEY (username)
);

--
-- Table that stores the raw issue comments data fetched from Github
--
CREATE TABLE github_issue_comment_data
(
    owner        TEXT        NOT NULL,
    repo         TEXT        NOT NULL,
    issue_number INTEGER     NOT NULL,
    page         INTEGER     NOT NULL,
    timestamp    TIMESTAMPTZ NOT NULL,
    etag         TEXT        NOT NULL,
    data         JSONB       NOT NULL,
    PRIMARY KEY (owner, repo, issue_number, page)
);

--
-- Table that stores the raw builds data fetched from Buildkite
--
CREATE TABLE buildkite_build_data
(
    org          TEXT        NOT NULL,
    pipeline     TEXT        NOT NULL,
    build_number INTEGER     NOT NULL,
    timestamp    TIMESTAMPTZ NOT NULL,
    etag         TEXT        NOT NULL,
    data         JSONB       NOT NULL,
    PRIMARY KEY (org, pipeline, build_number)
);

--
-- Materialized view of buildkite_build_data that each row is a bazelci task.
--
CREATE MATERIALIZED VIEW buildkite_job_mview AS
WITH buildkite_job AS (WITH buildkite_job_data AS (SELECT org,
                                                          pipeline,
                                                          build_number,
                                                          data ->> 'branch'                      AS branch,
                                                          data ->> 'state'                       AS build_state,
                                                          (data ->> 'scheduled_at')::timestamptz AS build_scheduled_at,
                                                          (data ->> 'created_at')::timestamptz   AS build_created_at,
                                                          (data ->> 'started_at')::timestamptz   AS build_started_at,
                                                          (data ->> 'finished_at')::timestamptz  AS build_finished_at,
                                                          JSONB_ARRAY_ELEMENTS(data -> 'jobs')   AS data
                                                   FROM buildkite_build_data)
                       SELECT org,
                              pipeline,
                              build_number,
                              branch,
                              build_state,
                              build_scheduled_at,
                              build_created_at,
                              build_started_at,
                              build_finished_at,
                              EXTRACT(EPOCH FROM build_started_at -
                                                 build_created_at)    AS build_wait_time,
                              EXTRACT(EPOCH FROM build_finished_at -
                                                 build_started_at)    AS build_run_time,
                              data ->> 'id'                           AS job_id,
                              data ->> 'name'                         AS name,
                              COALESCE(SUBSTRING(data ->> 'command' FROM
                                                 '--task=(\S+)'),
                                       SUBSTRING(data ->> 'command' FROM
                                                 '--platform=(\S+)')) AS bazelci_task,
                              data ->> 'state'                        AS state,
                              (data ->> 'scheduled_at')::timestamptz  AS scheduled_at,
                              (data ->> 'created_at')::timestamptz    AS created_at,
                              (data ->> 'started_at')::timestamptz    AS started_at,
                              (data ->> 'finished_at')::timestamptz   AS finished_at
                       FROM buildkite_job_data)
SELECT *,
       EXTRACT(EPOCH FROM (started_at - created_at))  AS wait_time,
       EXTRACT(EPOCH FROM (finished_at - started_at)) AS run_time
FROM buildkite_job
WHERE bazelci_task is NOT NULL;

CREATE UNIQUE INDEX buildkite_job_mview_pkey
    ON buildkite_job_mview (org, pipeline, build_number, bazelci_task);
CREATE INDEX buildkite_job_mview_created_at
    on buildkite_job_mview (created_at);
CREATE INDEX buildkite_job_mview_state
    on buildkite_job_mview (state);
CREATE INDEX buildkite_job_mview_branch
    on buildkite_job_mview (branch);
CREATE INDEX buildkite_job_mview_build_state
    on buildkite_job_mview (build_state);
CREATE INDEX buildkite_job_mview_build_created_at
    on buildkite_job_mview (build_created_at);
