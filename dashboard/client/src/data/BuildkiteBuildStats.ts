import useSWR from "swr";
import queryString from "query-string";

import fetcher from "./fetcher";

export interface BuildkiteBuildStatsParams {
  branch?: string;
  from?: string;
}

export interface BuildkiteBuildStats {
  org: string;
  pipeline: string;
  items: Array<BuildkiteBuildStatsItem>;
}

export interface BuildkiteBuildStatsItem {
  buildNumber: number;
  createdAt: string;
  branch: string;
  state: string;
  waitTime: number;
  runTime: number;
}

export function useBuildkiteBuildStats(
  org: string,
  pipeline: string,
  params: BuildkiteBuildStatsParams
) {
  const { data, error } = useSWR(
    queryString.stringifyUrl(
      {
        url: `/api/buildkite/organizations/${org}/pipelines/${pipeline}/stats`,
        query: params as any,
      },
      { skipNull: true }
    ),
    fetcher
  );
  return {
    data: data as BuildkiteBuildStats,
    error,
    loading: !error && !data,
  };
}
