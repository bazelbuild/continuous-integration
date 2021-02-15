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
  GithubTeamTableCell,
  GithubTeamTableRow,
} from "./data/GithubTeamTable";

function GithubTeamTableCellContainer({
  value,
  header,
}: {
  value: GithubTeamTableCell;
  header: string,
}) {
  const content = value.count !== null ? value.count : "";
  let style = {};
  if (header === "No Type" || header === "No Priority" || header === "Untriaged") {
    if (value.count >= 10) {
      style = { color: "#e53935", fontWeight: "bold" };
    }
  }
  return (
    <Link href={value.url} target="_blank" style={style}>
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

function UnderlyingTable({
  columns,
  data,
}: {
  columns: Array<Column<GithubTeamTableRow>>;
  data: Array<GithubTeamTableRow>;
}) {
  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
  } = useTable({ columns, data }, useSortBy);

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
                  const header = cell.column.Header;
                  return (
                    <TableCell {...cell.getCellProps()}>
                      {cell.render("Cell", { header })}
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

export interface GithubTeamTableContainerProps {
  owner: string;
  repo: string;
}

export default function GithubTeamTableContainer({
  owner,
  repo,
}: GithubTeamTableContainerProps) {
  const { data: table, error, loading } = useGithubTeamTable(
    owner,
    repo,
    "open-issues"
  );

  const githubTeamTableCellSortType = React.useMemo(
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
          Cell: GithubTeamTableCellContainer,
          sortType: githubTeamTableCellSortType,
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

  if (loading) {
    return <div>loading</div>;
  }

  if (error) {
    return <div>error</div>;
  }

  return <UnderlyingTable columns={columns} data={table.rows} />;
}
