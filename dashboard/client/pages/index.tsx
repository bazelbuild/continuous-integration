import React from "react";
import GithubTeamIssueTable from "../src/GithubTeamIssueTable";
import {
  AppBar,
  Container,
  createMuiTheme,
  Paper,
  ThemeProvider,
  Toolbar,
} from "@material-ui/core";

let theme = createMuiTheme({
  palette: {
    primary: {
      main: "#368039",
    },
  },
});

export default function Home() {
  return (
    <ThemeProvider theme={theme}>
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
        <Paper>
          <GithubTeamIssueTable />
        </Paper>
      </Container>
    </ThemeProvider>
  );
}
