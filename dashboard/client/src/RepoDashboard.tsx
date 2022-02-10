import React, { useState } from "react";
import { RepoIcon } from "@primer/octicons-react";
import dynamic from "next/dynamic";
import {
  Breadcrumbs,
  Card,
  CardContent,
  CardHeader,
  Container,
  createStyles,
  Drawer,
  Grid,
  Hidden,
  Link,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ThemeProvider,
  makeStyles,
  Theme,
  Toolbar,
  Typography,
  FormControl,
  MenuItem,
  Select,
} from "@material-ui/core";
import NextLink from "next/link";
import { DateTime } from "luxon";

import theme from "./theme";
import { GithubRepo, useGithubRepo } from "./data/GithubRepo";

const DynamicGithubTeamTable = dynamic(() => import("./GithubTeamTable"));

const DynamicGithubIssueQueryCountTaskResultChart = dynamic(
  () => import("../src/GithubIssueQueryCountTaskResultChart")
);

const appBarHeight = 52;
const drawerWidth = 256;

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    breadcrumbs: {
      marginTop: 16,
      marginBottom: 16,
    },
    drawer: {},
    container: {},
    toolbar: {
      width: drawerWidth,
      paddingTop: appBarHeight,
    },
    main: {
      backgroundColor: 'rgb(250, 250, 250)',
      [theme.breakpoints.up("md")]: {
        paddingLeft: drawerWidth,
      },
    },
  })
);

function RepoListItem(repo: GithubRepo) {
  const name = `${repo.owner}/${repo.repo}`;
  const link = `/${name}`;
  return (
    <ListItem key={name} dense={true}>
      <ListItemIcon style={{ minWidth: 20 }}>
        <RepoIcon />
      </ListItemIcon>
      <ListItemText>
        <NextLink href={link}>
          <Link href={link}>{name}</Link>
        </NextLink>
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
  return Math.ceil(Math.abs(DateTime.fromISO("2020-12-17").diffNow("day").days));
}

function GithubIssueQueryResultCard({title, queryIds}: {title: string, queryIds: Array<string>}) {
  const [days, setDays] = useState(30)
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
  )
}

export interface RepoDashboardProps {
  owner: string;
  repo: string;
}

export default function RepoDashboard({ owner, repo }: RepoDashboardProps) {
  const classes = useStyles();

  React.useEffect(() => {
    const jssStyles = document.querySelector("#jss-server-side");
    if (jssStyles) {
      jssStyles.parentElement!!.removeChild(jssStyles);
    }
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <Hidden smDown implementation="css">
        <Drawer variant={"permanent"} className={classes.drawer}>
          <Toolbar className={classes.toolbar}>
            <RepoList />
          </Toolbar>
        </Drawer>
      </Hidden>

      <main className={classes.main}>
        <Container maxWidth={false}>
          <Breadcrumbs aria-label="breadcrumb" className={classes.breadcrumbs}>
            <Typography color="textPrimary">
              <RepoIcon />
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
          <Grid container spacing={2} className={classes.container}>
            <Grid item xs={12}>
              <DynamicGithubTeamTable owner={owner} repo={repo} />
            </Grid>
            {owner === "bazelbuild" && repo === "bazel" && (
              <>
                <Grid item xs={12} md={6} xl={4}>
                  <GithubIssueQueryResultCard title="Unreviewed Issues" queryIds={["unreviewed"]}/>
                </Grid>
                <Grid item xs={12} md={6} xl={4}>
                  <GithubIssueQueryResultCard title="Untriaged Issues" queryIds={["total-untriaged"]}/>
                </Grid>
              </>
            )}
          </Grid>
        </Container>
      </main>
    </ThemeProvider>
  );
}
