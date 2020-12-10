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
  count?: number;
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
  const { data, error } = useSWR("/api/github/teams/issues", fetcher);
  return {
    data: data as Array<GithubTeamIssue>,
    error,
    loading: !error && !data,
  };
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
        accessor: (data) => data.openIssues.count,
      },
      {
        Header: "# open P0",
        accessor: (data) => data.openP0Issues.count,
      },
      {
        Header: "# open P1",
        accessor: (data) => data.openP1Issues.count,
      },
      {
        Header: "# open P2",
        accessor: (data) => data.openP2Issues.count,
      },
      {
        Header: "# open P3",
        accessor: (data) => data.openP3Issues.count,
      },
      {
        Header: "# open P4",
        accessor: (data) => data.openP4Issues.count,
      },
      {
        Header: "no type",
        accessor: (data) => data.openNoTypeIssues.count,
      },
      {
        Header: "no priority",
        accessor: (data) => data.openNoPriorityIssues.count,
      },
      {
        Header: "Untriaged",
        accessor: (data) => data.openUntriagedIssues.count,
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
                return <td {...cell.getCellProps()}>{cell.render("Cell")}</td>;
              })}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
