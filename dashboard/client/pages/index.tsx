import React from "react";
import GithubTeamIssueTable from "../src/GithubTeamIssueTable";
import {
  AppBar,
  Card,
  CardContent,
  CardHeader,
  Container,
  Grid,
  Toolbar,
} from "@material-ui/core";
import GithubIssueQueryCountTaskResultChart from "../src/GithubIssueQueryCountTaskResultChart";

export default function Home() {
  return (
    <>
      <AppBar position="sticky">
        <Toolbar variant="dense">
          <img
            src="https://bazel.build/images/bazel-navbar.svg"
            height={28}
            alt="Bazel"
          />
        </Toolbar>
      </AppBar>

      <Container style={{ marginTop: 20, marginBottom: 20 }} maxWidth="lg">
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <Card>
              <CardHeader
                title="Open Issues by Team"
                titleTypographyProps={{ variant: "body1" }}
              />
              <CardContent>
                <GithubTeamIssueTable />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
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
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader
                title="Untriaged Issues"
                titleTypographyProps={{ variant: "body1" }}
              />
              <CardContent>
                <GithubIssueQueryCountTaskResultChart
                  queryIds={[
                    "total-untriaged",
                  ]}
                />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>
    </>
  );
}
