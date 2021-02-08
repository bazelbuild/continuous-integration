import React from "react";
import { RepoIcon } from "@primer/octicons-react";
import {
  Breadcrumbs,
  Card,
  CardContent,
  CardHeader,
  Container,
  createStyles,
  Grid,
  Link,
  makeStyles,
  Theme,
  Typography,
} from "@material-ui/core";

import GithubIssueQueryCountTaskResultChart from "../src/GithubIssueQueryCountTaskResultChart";
import GithubTeamTable from "./GithubTeamTable";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    breadcrumbs: {
      marginTop: 16,
      marginBottom: 16,
    },
    container: {},
  })
);

export interface RepoDashboardProps {
  owner: string;
  repo: string;
}

export default function RepoDashboard({ owner, repo }: RepoDashboardProps) {
  const classes = useStyles();

  return (
    <Container maxWidth={false}>
      <Breadcrumbs aria-label="breadcrumb" className={classes.breadcrumbs}>
        <Typography color="textPrimary">
          <RepoIcon />
          <Link style={{ marginLeft: 4 }} href={`https://github.com/${owner}`}>
            {owner}
          </Link>
        </Typography>
        <Typography color="textPrimary">
          <Link href={`https://github.com/${owner}/${repo}`}>{repo}</Link>
        </Typography>
      </Breadcrumbs>
      <Grid container spacing={2} className={classes.container}>
        <Grid item xs={12}>
          <Card>
            <CardHeader
              title="Open Issues"
              titleTypographyProps={{ variant: "body1" }}
            />
            <CardContent style={{ marginTop: -32 }}>
              <GithubTeamTable owner={owner} repo={repo} />
            </CardContent>
          </Card>
        </Grid>
        {owner === "bazelbuild" && repo === "bazel" && (
          <>
            <Grid item xs={12} md={6} xl={4}>
              <Card>
                <CardHeader
                  title="Unreviewed Issues"
                  titleTypographyProps={{ variant: "body1" }}
                />
                <CardContent>
                  <GithubIssueQueryCountTaskResultChart
                    queryIds={["unreviewed"]}
                  />
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6} xl={4}>
              <Card>
                <CardHeader
                  title="Untriaged Issues"
                  titleTypographyProps={{ variant: "body1" }}
                />
                <CardContent>
                  <GithubIssueQueryCountTaskResultChart
                    queryIds={["total-untriaged"]}
                  />
                </CardContent>
              </Card>
            </Grid>
          </>
        )}
      </Grid>
    </Container>
  );
}
