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

CREATE INDEX ON github_issue_data ((data -> 'pull_request'));


CREATE MATERIALIZED VIEW github_issue AS
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
       i.data ->> 'state'                   AS state,
       i.data ->> 'title'                   AS title,
       COALESCE(il.labels, '{}')            AS labels,
       (data ->> 'created_at')::timestamptz AS created_at,
       (data ->> 'closed_at')::timestamptz  AS closed_at
FROM github_issue_data i
         LEFT JOIN github_issue_labels il
                   ON i.owner = il.owner AND i.repo = il.repo AND i.issue_number = il.issue_number
WHERE i.data -> 'pull_request' IS NULL;

CREATE UNIQUE INDEX ON github_issue (owner, repo, issue_number);
CREATE INDEX ON github_issue (state);
CREATE INDEX ON github_issue (labels);


CREATE VIEW github_issue_label AS
SELECT owner, repo, issue_number, unnest(labels) AS label
FROM github_issue;


CREATE MATERIALIZED VIEW github_label AS
WITH github_label_data AS (
    SELECT owner, repo, jsonb_array_elements(data #> '{labels}') AS data
    FROM github_issue_data
),
     _github_label AS (
         SELECT owner,
                repo,
                data ->> 'name'                                               AS name,
                data ->> 'description'                                        AS description,
                row_number() OVER (PARTITION BY owner, repo, data ->> 'name') AS row_number
         FROM github_label_data
     )
SELECT owner, repo, name, description
FROM _github_label
WHERE row_number = 1;

CREATE UNIQUE INDEX ON github_label (owner, repo, name);


CREATE MATERIALIZED VIEW github_label_team AS
SELECT owner, repo, SUBSTR(name, 6) AS name, name as label
FROM github_label
WHERE name LIKE 'team-%';

CREATE UNIQUE INDEX ON github_label_team (owner, repo, label);


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
WHERE giht IS NULL;

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
WHERE gihp IS NULL;


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


CREATE OR REPLACE PROCEDURE refresh_github_issue_materialized_views()
    LANGUAGE plpgsql
AS
$$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY github_issue;
    REFRESH MATERIALIZED VIEW CONCURRENTLY github_label;
    REFRESH MATERIALIZED VIEW CONCURRENTLY github_label_team;
END;
$$;