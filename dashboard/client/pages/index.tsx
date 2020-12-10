import styles from "./index.module.scss";

import React from "react";
import GithubTeamIssueTable from "../components/GithubTeamIssueTable";

export default function Home() {
  return (
    <div className={styles.container}>
      <GithubTeamIssueTable />
    </div>
  );
}
