CREATE TABLE json_state
(
    key       TEXT PRIMARY KEY,
    timestamp TIMESTAMPTZ,
    data      JSONB NOT NULL
);

--
-- Table that store the raw issues data fetched from Github
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
-- Table that stored issues generated from github_issue_data automatically by trigger
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
    labels          TEXT[]      NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL,
    updated_at      TIMESTAMPTZ,
    closed_at       TIMESTAMPTZ,
    PRIMARY KEY (owner, repo, issue_number)
);

CREATE UNIQUE INDEX ON github_issue (owner, repo, issue_number);
CREATE INDEX ON github_issue (state);
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


CREATE TABLE github_issue_team
(
    owner      TEXT,
    repo       TEXT,
    label      TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    name       TEXT,
    team_owner TEXT,
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
