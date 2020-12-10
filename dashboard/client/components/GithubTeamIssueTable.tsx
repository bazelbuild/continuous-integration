import styles from "./GithubTeamIssueTable.module.scss";

import React from "react";
import { Column, useTable } from "react-table";
import useSWR from "swr";

function fetcher(input: RequestInfo, init?: RequestInit) {
  return fetch(input, init).then((res) => res.json());
}

interface GithubTeamIssueTeam {
  name: string;
  owner: string;
  label: string;
}

interface GithubTeamIssueStats {
  url: string;
  count: number | null;
}

interface GithubTeamIssue {
  team: GithubTeamIssueTeam;
  openIssues: GithubTeamIssueStats;
  openP0Issues: GithubTeamIssueStats;
  openP1Issues: GithubTeamIssueStats;
  openP2Issues: GithubTeamIssueStats;
  openP3Issues: GithubTeamIssueStats;
  openP4Issues: GithubTeamIssueStats;
  openNoTypeIssues: GithubTeamIssueStats;
  openNoPriorityIssues: GithubTeamIssueStats;
  openUntriagedIssues: GithubTeamIssueStats;
  updatedAt: string;
}

function useGithubTeamIssues() {
  const { data, error } = useSWR("/api/github/teams/issues", fetcher, {
    refreshInterval: 60000,
  });
  return {
    data: data as Array<GithubTeamIssue>,
    error,
    loading: !error && !data,
  };
}

function IssueStatsCell({ value }: { value: GithubTeamIssueStats }) {
  const text = value.count !== null ? String(value.count) : "(none)";
  return (
    <div className={styles.stats}>
      <a href={value.url} target="_blank">
        {text}
      </a>
    </div>
  );
}

export default function GithubTeamIssueTable() {
  const { data, error, loading } = useGithubTeamIssues();
  const columns: Array<Column<GithubTeamIssue>> = React.useMemo(
    () => [
      {
        Header: "Team",
        accessor: (data) => data.team.name,
      },
      {
        Header: "# open issues",
        accessor: (data) => data.openIssues,
        Cell: IssueStatsCell,
      },
      {
        Header: "# open P0",
        accessor: (data) => data.openP0Issues,
        Cell: IssueStatsCell,
      },
      {
        Header: "# open P1",
        accessor: (data) => data.openP1Issues,
        Cell: IssueStatsCell,
      },
      {
        Header: "# open P2",
        accessor: (data) => data.openP2Issues,
        Cell: IssueStatsCell,
      },
      {
        Header: "# open P3",
        accessor: (data) => data.openP3Issues,
        Cell: IssueStatsCell,
      },
      {
        Header: "# open P4",
        accessor: (data) => data.openP4Issues,
        Cell: IssueStatsCell,
      },
      {
        Header: "no type",
        accessor: (data) => data.openNoTypeIssues,
        Cell: IssueStatsCell,
      },
      {
        Header: "no priority",
        accessor: (data) => data.openNoPriorityIssues,
        Cell: IssueStatsCell,
      },
      {
        Header: "Untriaged",
        accessor: (data) => data.openUntriagedIssues,
        Cell: IssueStatsCell,
      },
      {
        Header: "Owner",
        accessor: (data) => data.team.owner,
      },
    ],
    []
  );

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
  } = useTable({ columns, data: data || [] });

  if (loading) {
    return <div>loading</div>;
  }

  console.log(data);

  return (
    <div className={styles.container}>
      <table {...getTableProps()}>
        <thead>
          {headerGroups.map((headerGroup) => (
            <tr {...headerGroup.getHeaderGroupProps()}>
              {headerGroup.headers.map((column) => (
                <th {...column.getHeaderProps()}>{column.render("Header")}</th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody {...getTableBodyProps()}>
          {rows.map((row) => {
            prepareRow(row);
            return (
              <tr {...row.getRowProps()}>
                {row.cells.map((cell) => {
                  return (
                    <td {...cell.getCellProps()}>{cell.render("Cell")}</td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
