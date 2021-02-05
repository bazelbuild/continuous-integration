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
  useGithubTeamTable,
  GithubTeamTable,
  GithubTeamTableCell,
  GithubTeamTableRow,
} from "./data/GithubTeamTable";

function IssueStatsCell({ value }: { value: GithubTeamTableCell }) {
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
  const { data: table, error, loading } = useGithubTeamTable(
    "bazelbuild",
    "bazel",
    "open-issues"
  );

  const issueStatsSortType = React.useMemo(
    () => (rowA: Row<any>, rowB: Row<any>, id: string, _desc: boolean) => {
      const a = rowA.values[id] as GithubTeamTableCell;
      const b = rowB.values[id] as GithubTeamTableCell;
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

  const columns: Array<Column<GithubTeamTableRow>> = React.useMemo(
    () => [
      {
        Header: "Team",
        accessor: (data) => data.team.name,
      },
      ...(loading ? [] : table.headers).map((header) => {
        return {
          Header: header.name,
          accessor: (data: GithubTeamTableRow) => data.cells[header.id],
          Cell: IssueStatsCell,
          sortType: issueStatsSortType,
        };
      }),
      {
        Header: "Owner",
        accessor: (data) => data.team.teamOwner,
        Cell: TeamOwnerCell,
      },
    ],
    [table]
  );

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
  } = useTable({ columns, data: loading ? [] : table.rows }, useSortBy);

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
