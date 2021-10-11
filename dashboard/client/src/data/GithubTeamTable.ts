import useSWR from "swr";

import fetcher from "./fetcher";

export interface GithubTeamTable {
  owner: string;
  repo: string;
  id: string;
  name: string;
  headers: Array<{
    id: string;
    name: string;
  }>;
  rows: Array<GithubTeamTableRow>;
}

export interface GithubTeamTableRow {
  team: {
    name: string;
    teamOwner: string;
  };
  cells: { [id: string]: GithubTeamTableCell };
}

export interface GithubTeamTableCell {
  url: string;
  count: number;
}

export function useGithubTeamTable(
  owner: string,
  repo: string,
  tableId: string
) {
  const { data, error } = useSWR(
    `/api/github/${owner}/${repo}/team-tables/${tableId}`,
    fetcher,
    {
      refreshInterval: 60000,
    }
  );
  return {
    data: data as GithubTeamTable,
    error,
    loading: !error && !data,
  };
}
