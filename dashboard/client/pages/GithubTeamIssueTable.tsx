import React from "react";
import {Column, useTable} from "react-table";

interface Data {
  teamLabel: string;
  teamLabelOwner: string;
  numberOfOpenIssues: number;
  numberOfOpenP1Issues: number;
  numberOfOpenP2Issues: number;
  numberOfOpenP3Issues: number;
  numberOfOpenP4Issues: number;
  numberOfNoTypeIssues: number;
  numberOfNoPriorityIssues: number;
  numberOfUntriagedIssues: number;
}

export default function GithubTeamIssueTable() {
  const data: Array<Data> = React.useMemo(
    () => [
      {
        teamLabel: "(none)",
        teamLabelOwner: 'ahumesky',
        numberOfOpenIssues: 21,
        numberOfOpenP1Issues: 2,
        numberOfOpenP2Issues: 0,
        numberOfOpenP3Issues: 0,
        numberOfOpenP4Issues: 0,
        numberOfNoTypeIssues: 3,
        numberOfNoPriorityIssues: 1,
        numberOfUntriagedIssues: 0
      },
    ],
    []
  );

  const columns: Array<Column<Data>> = React.useMemo(
    () => [
      {
        Header: "Team Label",
        accessor: (data) => data.teamLabel,
      },
      {
        Header: "# open issues",
        accessor: (data) => data.numberOfOpenIssues,
      },
      {
        Header: "# open P1",
        accessor: (data) => data.numberOfOpenP1Issues,
      },
      {
        Header: "# open P2",
        accessor: (data) => data.numberOfOpenP2Issues,
      },
      {
        Header: "# open P3",
        accessor: (data) => data.numberOfOpenP3Issues,
      },
      {
        Header: "# open P4",
        accessor: (data) => data.numberOfOpenP4Issues,
      },
      {
        Header: "no type",
        accessor: (data) => data.numberOfNoTypeIssues,
      },
      {
        Header: "no priority",
        accessor: (data) => data.numberOfNoPriorityIssues,
      },
      {
        Header: "Untriaged",
        accessor: (data) => data.numberOfUntriagedIssues,
      },
      {
        Header: "Owner",
        accessor: (data) => data.teamLabelOwner,
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
  } = useTable({columns, data});

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
