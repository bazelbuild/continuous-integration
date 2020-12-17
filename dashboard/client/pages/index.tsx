import React from "react";
import GithubTeamIssueTable from "../src/GithubTeamIssueTable";
import {
  AppBar,
  Card,
  CardContent,
  CardHeader,
  Container,
  Toolbar,
} from "@material-ui/core";

export default function Home() {
  return (
    <>
      <AppBar position="static">
        <Toolbar variant="dense">
          <img
            src="https://bazel.build/images/bazel-navbar.svg"
            height={28}
            alt="Bazel"
          />
        </Toolbar>
      </AppBar>

      <Container style={{ marginTop: "30px" }}>
        {/*<Grid container>*/}
        {/*<Grid item>*/}
        <Card>
          <CardHeader
            title="Open Issues (by Team)"
            titleTypographyProps={{ variant: "body1" }}
          />
          <CardContent style={{ padding: 0 }}>
            <GithubTeamIssueTable />
          </CardContent>
        </Card>
        {/*</Grid>*/}
        {/*</Grid>*/}
      </Container>
    </>
  );
}
