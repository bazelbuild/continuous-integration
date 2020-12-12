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

CREATE OR REPLACE FUNCTION tf_snapshot_github_issue_data()
    RETURNS TRIGGER
    LANGUAGE plpgsql
AS
$$
BEGIN
    INSERT INTO github_issue_data_snapshot (owner, repo, issue_number, timestamp, data)
    VALUES (NEW.owner, NEW.repo, NEW.issue_number, NEW.timestamp, NEW.data);

    RETURN NEW;
END;
$$;

CREATE TRIGGER t_snapshot_github_issue_data
    AFTER INSERT OR UPDATE
    ON github_issue_data
    FOR EACH ROW
EXECUTE PROCEDURE tf_snapshot_github_issue_data();

--
-- Table that store the snapshots of issues data fetched from Github
--
CREATE TABLE github_issue_data_snapshot
(
    owner        TEXT        NOT NULL,
    repo         TEXT        NOT NULL,
    issue_number INTEGER     NOT NULL,
    timestamp    TIMESTAMPTZ NOT NULL,
    data         JSONB       NOT NULL,
    PRIMARY KEY (owner, repo, issue_number, timestamp)
);

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
    closed_at       TIMESTAMPTZ,
    PRIMARY KEY (owner, repo, issue_number)
);

CREATE UNIQUE INDEX ON github_issue (owner, repo, issue_number);
CREATE INDEX ON github_issue (state);
CREATE INDEX ON github_issue (labels);
CREATE INDEX ON github_issue (is_pull_request);

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

CREATE VIEW github_label_team AS
SELECT owner, repo, SUBSTR(name, 6) AS name, name as label
FROM github_label
WHERE name LIKE 'team-%';


CREATE VIEW github_label_team_issue AS
SELECT glt.owner, glt.repo, glt.label, il.issue_number
FROM github_label_team glt
         LEFT JOIN github_issue_label il ON glt.owner = il.owner AND glt.repo = il.repo AND glt.label = il.label;


CREATE VIEW github_issue_no_type AS
WITH github_issue_has_type AS (
    SELECT owner, repo, issue_number
    FROM github_issue_label
    WHERE label LIKE 'type: %'
    GROUP BY owner, repo, issue_number
)
SELECT gi.*
FROM github_issue gi
         LEFT JOIN github_issue_has_type giht
                   ON gi.owner = giht.owner AND gi.repo = giht.repo AND gi.issue_number = giht.issue_number
WHERE NOT gi.is_pull_request
  AND giht IS NULL;

CREATE VIEW github_issue_no_priority AS
WITH github_issue_has_priority AS (
    SELECT owner, repo, issue_number
    FROM github_issue_label
    WHERE label LIKE 'P_'
    GROUP BY owner, repo, issue_number
)
SELECT gi.*
FROM github_issue gi
         LEFT JOIN github_issue_has_priority gihp
                   ON gi.owner = gihp.owner AND gi.repo = gihp.repo AND gi.issue_number = gihp.issue_number
WHERE NOT gi.is_pull_request
  AND gihp IS NULL;


CREATE VIEW github_label_team_issue_status AS
WITH github_label_team_issue_open AS (
    SELECT gi.owner,
           gi.repo,
           COALESCE(glti.label, '(none)')                                              AS team,
           COUNT(*) FILTER (WHERE gi.state = 'open')                                   AS open,
           COUNT(*) FILTER (WHERE gi.state = 'open' AND 'P0' = ANY (gi.labels))        AS open_p0,
           COUNT(*) FILTER (WHERE gi.state = 'open' AND 'P1' = ANY (gi.labels))        AS open_p1,
           COUNT(*) FILTER (WHERE gi.state = 'open' AND 'P2' = ANY (gi.labels))        AS open_p2,
           COUNT(*) FILTER (WHERE gi.state = 'open' AND 'P3' = ANY (gi.labels))        AS open_p3,
           COUNT(*) FILTER (WHERE gi.state = 'open' AND 'P4' = ANY (gi.labels))        AS open_p4,
           COUNT(*) FILTER (WHERE gi.state = 'open' AND 'untriaged' = ANY (gi.labels)) AS untriaged
    FROM github_issue gi
             LEFT JOIN github_label_team_issue glti
                       ON gi.owner = glti.owner AND gi.repo = glti.repo AND gi.issue_number = glti.issue_number
    WHERE NOT gi.is_pull_request
    GROUP BY gi.owner, gi.repo, glti.label
),
     github_label_team_issue_open_no_type AS (
         SELECT glti.owner, glti.repo, glti.label AS team, COUNT(gint) AS no_type
         FROM github_issue_no_type gint
                  LEFT JOIN github_label_team_issue glti ON gint.owner = glti.owner AND gint.repo = glti.repo AND
                                                            gint.issue_number = glti.issue_number
         WHERE gint.state = 'open'
         GROUP BY glti.owner, glti.repo, glti.label
     ),
     github_label_team_issue_open_no_priority AS (
         SELECT glti.owner, glti.repo, glti.label AS team, COUNT(ginp) AS no_priority
         FROM github_issue_no_priority ginp
                  LEFT JOIN github_label_team_issue glti ON ginp.owner = glti.owner AND ginp.repo = glti.repo AND
                                                            ginp.issue_number = glti.issue_number
         WHERE ginp.state = 'open'
         GROUP BY glti.owner, glti.repo, glti.label
     )
SELECT gltio.*, COALESCE(gltiont.no_type, 0) as no_type, COALESCE(gltionp.no_priority, 0) as no_priority
FROM github_label_team_issue_open gltio
         LEFT JOIN github_label_team_issue_open_no_type gltiont
                   ON gltio.owner = gltiont.owner AND gltio.repo = gltiont.repo AND gltio.team = gltiont.team
         LEFT JOIN github_label_team_issue_open_no_priority gltionp
                   ON gltio.owner = gltionp.owner AND gltio.repo = gltionp.repo AND gltio.team = gltionp.team;

