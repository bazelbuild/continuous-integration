import React from "react";
import { Link } from "@material-ui/core";
import MUIDataTable, { MUIDataTableColumn } from "mui-datatables";
import { useGithubTeamTable } from "./data/GithubTeamTable";

function GithubTeamTableCellContainer({
  value,
  url,
  header,
}: {
  value: number;
  url: string;
  header: string | undefined;
}) {
  let style = {};
  if (
    header === "No Type" ||
    header === "No Priority" ||
    header === "Untriaged"
  ) {
    if (value >= 10) {
      style = { color: "#e53935", fontWeight: "bold" };
    }
  }
  return (
    <Link href={url} target="_blank" style={style}>
      {value}
    </Link>
  );
}

function TeamOwnerCell({ value }: { value: string }) {
  if (value === "(none)") {
    return null;
  }

  return (
    <Link href={`https://github.com/${value}`} target="_blank">
      {value}
    </Link>
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

  const data = React.useMemo(
    () =>
      table && table.rows
        ? table.rows.map((row, index) => {
            const data: any = {};
            for (let key of Object.keys(row.cells)) {
              data[`cells.${key}`] = row.cells[key].count;
            }
            data["team.name"] = row.team.name;
            let teamOwner = row.team.teamOwner;
            if (teamOwner === "") {
              teamOwner = "(none)";
            }
            data["team.teamOwner"] = teamOwner;
            data["index"] = index;
            return data;
          })
        : [],
    [table]
  );

  const columns: MUIDataTableColumn[] = React.useMemo(
    () =>
      table && table.headers
        ? [
            ...(table.rows.length > 1
              ? ([
                  {
                    name: "team.name",
                    label: "Team",
                    options: {
                      filterType: "multiselect",
                    },
                  },
                ] as MUIDataTableColumn[])
              : []),
            ...table.headers.map(
              (header) =>
                ({
                  name: `cells.${header.id}`,
                  label: header.name,
                  options: {
                    filter: false,
                    sortDescFirst: true,
                    customBodyRender: (value, tableMeta) => {
                      let url = "";

                      const row = table.rows.find(
                        (row) => row.team.name === tableMeta.rowData[0]
                      );
                      if (row) {
                        const key = tableMeta.columnData.name.substring(
                          "cells.".length
                        );
                        url = row.cells[key].url;
                      }

                      return (
                        <GithubTeamTableCellContainer
                          value={value}
                          url={url}
                          header={tableMeta.columnData.label}
                        />
                      );
                    },
                  },
                } as MUIDataTableColumn)
            ),
            {
              name: "team.teamOwner",
              label: "Owner",
              options: {
                filterType: "multiselect",
                customBodyRender: (value) => {
                  return <TeamOwnerCell value={value} />;
                },
              },
            },
          ]
        : [],
    [table]
  );

  if (loading) {
    return <span>loading</span>;
  }

  if (error) {
    return <span>error</span>;
  }

  return (
    <MUIDataTable
      title={table.name}
      columns={columns}
      data={data}
      options={{
        elevation: 1,
        selectableRows: "none",
        download: false,
        print: false,
      }}
    />
  );
}
