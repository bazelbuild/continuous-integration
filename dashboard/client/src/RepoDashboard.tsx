import React, { useState } from "react";
import dynamic from "next/dynamic";
import { ThemeProvider } from "@mui/material/styles";
import { DateTime } from "luxon";
import theme from "./theme";
import { GithubRepo, useGithubRepo } from "./data/GithubRepo";
import {
  Breadcrumbs,
  Card,
  CardContent,
  CardHeader,
  Container,
  Drawer,
  FormControl,
  Grid,
  Link,
  List,
  ListItem,
  ListItemText,
  MenuItem,
  Select,
  Toolbar,
  Typography,
} from "@mui/material";

const DynamicGithubTeamTable = dynamic(() => import("./GithubTeamTable"));

const DynamicGithubIssueQueryCountTaskResultChart = dynamic(
  () => import("../src/GithubIssueQueryCountTaskResultChart")
);

const appBarHeight = 52;
const drawerWidth = 256;

function RepoListItem(repo: GithubRepo) {
  const name = `${repo.owner}/${repo.repo}`;
  const link = `/${name}`;
  return (
    <ListItem key={name} dense={true}>
      <ListItemText>
        <Link href={link}>{name}</Link>
      </ListItemText>
    </ListItem>
  );
}

function RepoList() {
  const { data, loading, error } = useGithubRepo();

  if (loading) {
    return <div />;
  }

  if (error) {
    return <p>Error</p>;
  }
  return <List>{data.map((repo) => RepoListItem(repo))}</List>;
}

function maxDays() {
  return Math.ceil(
    Math.abs(DateTime.fromISO("2020-12-17").diffNow("day").days)
  );
}

function GithubIssueQueryResultCard({
  title,
  queryIds,
}: {
  title: string;
  queryIds: Array<string>;
}) {
  const [days, setDays] = useState(30);
  return (
    <Card>
      <CardHeader
        title={title}
        titleTypographyProps={{ variant: "body1" }}
        action={
          <FormControl fullWidth>
            <Select
              id="select"
              value={days}
              autoWidth
              onChange={(event) => setDays(event.target.value as number)}
            >
              <MenuItem value={30}>past month</MenuItem>
              <MenuItem value={90}>past 3 months</MenuItem>
              <MenuItem value={180}>past 6 months</MenuItem>
              <MenuItem value={360}>past 12 months</MenuItem>
              <MenuItem value={720}>past 24 months</MenuItem>
              <MenuItem value={maxDays()}>all</MenuItem>
            </Select>
          </FormControl>
        }
      />
      <CardContent>
        <DynamicGithubIssueQueryCountTaskResultChart
          days={days}
          queryIds={queryIds}
        />
      </CardContent>
    </Card>
  );
}

export interface RepoDashboardProps {
  owner: string;
  repo: string;
}

export default function RepoDashboard({ owner, repo }: RepoDashboardProps) {
  return (
    <ThemeProvider theme={theme}>
      <Drawer variant={"permanent"}>
        <Toolbar style={{ width: drawerWidth, marginTop: appBarHeight }}>
          <RepoList />
        </Toolbar>
      </Drawer>

      <main
        style={{
          backgroundColor: "rgb(250, 250, 250)",
          paddingLeft: drawerWidth,
        }}
      >
        <Container maxWidth={false}>
          <Breadcrumbs aria-label="breadcrumb" className="mt-4 mb-4">
            <Typography color="textPrimary">
              <Link
                style={{ marginLeft: 4 }}
                href={`https://github.com/${owner}`}
              >
                {owner}
              </Link>
            </Typography>
            <Typography color="textPrimary">
              <Link href={`https://github.com/${owner}/${repo}`}>{repo}</Link>
            </Typography>
          </Breadcrumbs>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <DynamicGithubTeamTable owner={owner} repo={repo} />
            </Grid>
            {owner === "bazelbuild" && repo === "bazel" && (
              <>
                <Grid item xs={12} md={6} xl={4}>
                  <GithubIssueQueryResultCard
                    title="Unreviewed Issues"
                    queryIds={["unreviewed"]}
                  />
                </Grid>
                <Grid item xs={12} md={6} xl={4}>
                  <GithubIssueQueryResultCard
                    title="Untriaged Issues"
                    queryIds={["total-untriaged"]}
                  />
                </Grid>
              </>
            )}
          </Grid>
        </Container>
      </main>
    </ThemeProvider>
  );
}
