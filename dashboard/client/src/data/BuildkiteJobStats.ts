import useSWR from "swr";
import queryString from "query-string";

import fetcher from "./fetcher";

export interface BuildkiteJobStatsParams {
  branch?: string;
  from?: string;
}

export interface BuildkiteJobStats {
  org: string;
  pipeline: string;
  items: Array<BuildkiteJobStatsItem>;
}

export interface BuildkiteJobStatsItem {
  buildNumber: number;
  jobId: string;
  bazelCITask: string;
  name: string;
  createdAt: string;
  branch: string;
  state: string;
  waitTime: number;
  runTime: number;
}

export function useBuildkiteJobStats(
  org: string,
  pipeline: string,
  params: BuildkiteJobStatsParams
) {
  const { data, error } = useSWR(
    queryString.stringifyUrl(
      {
        url: `/api/buildkite/organizations/${org}/pipelines/${pipeline}/jobs/stats`,
        query: params as any,
      },
      { skipNull: true }
    ),
    fetcher
  );
  return {
    data: data as BuildkiteJobStats,
    error,
    loading: !error && !data,
  };
}
