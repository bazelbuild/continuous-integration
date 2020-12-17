import React from "react";
import { Column, Row, useSortBy, useTable } from "react-table";
import useSWR from "swr";
import {
  Link,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
} from "@material-ui/core";

function fetcher(input: RequestInfo, init?: RequestInit) {
  return fetch(input, init).then((res) => res.json());
}

interface GithubIssueTeam {
  owner: string;
  repo: string;
  label: string;
  name: string;
  teamOwner: string;
}

interface GithubTeamIssueStats {
  url: string;
  count: number | null;
}

interface GithubTeamIssue {
  team: GithubIssueTeam;
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

function useGithubTeamIssues(owner: string, repo: string) {
  const { data, error } = useSWR(
    `/api/github/${owner}/${repo}/teams/issues`,
    fetcher,
    {
      refreshInterval: 60000,
    }
  );
  return {
    data: data as Array<GithubTeamIssue>,
    error,
    loading: !error && !data,
  };
}

function IssueStatsCell({ value }: { value: GithubTeamIssueStats }) {
  const content = value.count !== null ? value.count : "";
  return (
    <Link href={value.url} target="_blank">
      {content}
    </Link>
  );
}

function TeamOwnerCell({ value }: { value: string }) {
  return (
    <Link href={`https://github.com/${value}`} target="_blank">
      {value}
    </Link>
  );
}

export default function GithubTeamIssueTable() {
  const { data, error, loading } = useGithubTeamIssues("bazelbuild", "bazel");

  const issueStatsSortType = React.useMemo(
    () => (rowA: Row<any>, rowB: Row<any>, id: string, _desc: boolean) => {
      const a = rowA.values[id] as GithubTeamIssueStats;
      const b = rowB.values[id] as GithubTeamIssueStats;
      if (!a.count) {
        return 1;
      } else if (!b.count) {
        return -1;
      } else {
        if (a.count > b.count) {
          return -1;
        } else if (b.count > a.count) {
          return 1;
        } else {
          return 0;
        }
      }
    },
    []
  );

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
        sortType: issueStatsSortType,
      },
      {
        Header: "# open P0",
        accessor: (data) => data.openP0Issues,
        Cell: IssueStatsCell,
        sortType: issueStatsSortType,
      },
      {
        Header: "# open P1",
        accessor: (data) => data.openP1Issues,
        Cell: IssueStatsCell,
        sortType: issueStatsSortType,
      },
      {
        Header: "# open P2",
        accessor: (data) => data.openP2Issues,
        Cell: IssueStatsCell,
        sortType: issueStatsSortType,
      },
      {
        Header: "# open P3",
        accessor: (data) => data.openP3Issues,
        Cell: IssueStatsCell,
        sortType: issueStatsSortType,
      },
      {
        Header: "# open P4",
        accessor: (data) => data.openP4Issues,
        Cell: IssueStatsCell,
        sortType: issueStatsSortType,
      },
      {
        Header: "no type",
        accessor: (data) => data.openNoTypeIssues,
        Cell: IssueStatsCell,
        sortType: issueStatsSortType,
      },
      {
        Header: "no priority",
        accessor: (data) => data.openNoPriorityIssues,
        Cell: IssueStatsCell,
        sortType: issueStatsSortType,
      },
      {
        Header: "Untriaged",
        accessor: (data) => data.openUntriagedIssues,
        Cell: IssueStatsCell,
        sortType: issueStatsSortType,
      },
      {
        Header: "Owner",
        accessor: (data) => data.team.teamOwner,
        Cell: TeamOwnerCell,
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
  } = useTable({ columns, data: data || [] }, useSortBy);

  if (loading) {
    return <div>loading</div>;
  }

  if (error) {
    return <div>error</div>;
  }

  return (
    <TableContainer>
      <Table size="small" {...getTableProps()}>
        <TableHead>
          {headerGroups.map((headerGroup) => (
            <TableRow {...headerGroup.getHeaderGroupProps()}>
              {headerGroup.headers.map((column) => (
                <TableCell
                  {...column.getHeaderProps(
                    (column as any).getSortByToggleProps()
                  )}
                >
                  <TableSortLabel
                    active={(column as any).isSorted}
                    direction={(column as any).isSortedDesc ? "desc" : "asc"}
                  >
                    {column.render("Header")}
                  </TableSortLabel>
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableHead>
        <TableBody {...getTableBodyProps()}>
          {rows.map((row) => {
            prepareRow(row);
            return (
              <TableRow {...row.getRowProps()}>
                {row.cells.map((cell) => {
                  return (
                    <TableCell {...cell.getCellProps()}>
                      {cell.render("Cell")}
                    </TableCell>
                  );
                })}
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
