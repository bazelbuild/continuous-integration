import React from "react";
import { Column, Row, useSortBy, useTable } from "react-table";
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

import {
  GithubTeamIssue,
  GithubTeamIssueStats,
  useGithubTeamIssues,
} from "./data/GithubTeamIssue";

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
        Header: "Total",
        accessor: (data) => data.openIssues,
        Cell: IssueStatsCell,
        sortType: issueStatsSortType,
      },
      {
        Header: "P0",
        accessor: (data) => data.openP0Issues,
        Cell: IssueStatsCell,
        sortType: issueStatsSortType,
      },
      {
        Header: "P1",
        accessor: (data) => data.openP1Issues,
        Cell: IssueStatsCell,
        sortType: issueStatsSortType,
      },
      {
        Header: "P2",
        accessor: (data) => data.openP2Issues,
        Cell: IssueStatsCell,
        sortType: issueStatsSortType,
      },
      {
        Header: "P3",
        accessor: (data) => data.openP3Issues,
        Cell: IssueStatsCell,
        sortType: issueStatsSortType,
      },
      {
        Header: "P4",
        accessor: (data) => data.openP4Issues,
        Cell: IssueStatsCell,
        sortType: issueStatsSortType,
      },
      {
        Header: "No Type",
        accessor: (data) => data.openNoTypeIssues,
        Cell: IssueStatsCell,
        sortType: issueStatsSortType,
      },
      {
        Header: "No Priority",
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
        Header: "PR",
        accessor: (data) => data.openPullRequests,
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
