import React from "react";
import {
  AppBar,
  Toolbar,
  Theme,
  makeStyles,
  createStyles,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Link,
  Drawer,
  Hidden,
} from "@material-ui/core";
import { RepoIcon } from "@primer/octicons-react";
import NextLink from "next/link";

import { GithubRepo, useGithubRepo } from "./data/GithubRepo";

const appBarHeight = 48;
const drawerWidth = 256;

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    appBar: {
      zIndex: theme.zIndex.drawer + 1,
    },
    drawer: {},
    toolbar: {
      width: drawerWidth,
      paddingTop: appBarHeight,
    },
    main: {
      paddingTop: appBarHeight,
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
    return <p>error</p>;
  }
  return <List>{data.map((repo) => RepoListItem(repo))}</List>;
}

export interface LayoutProps {
  children: NonNullable<React.ReactNode>;
}

export default function Layout({ children }: LayoutProps) {
  const classes = useStyles();
  return (
    <>
      <AppBar position="fixed" className={classes.appBar}>
        <Toolbar variant="dense">
          <img
            src="https://bazel.build/images/bazel-navbar.svg"
            style={{height: 28}}
            alt="Bazel"
          />
        </Toolbar>
      </AppBar>

      <Hidden smDown implementation="css">
        <Drawer variant={"permanent"} className={classes.drawer}>
          <Toolbar className={classes.toolbar}>
            <RepoList />
          </Toolbar>
        </Drawer>
      </Hidden>

      <main className={classes.main}>{children}</main>
    </>
  );
}
