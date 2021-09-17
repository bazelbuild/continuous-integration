import useSWR from "swr";

import fetcher from "./fetcher";

export interface GithubIssueQueryCountTaskResult {
  id: string;
  name: string;
  url: string;
  items: Array<{
    timestamp: string;
    count: number | null;
  }>;
}

export function useGithubIssueQueryCountTaskResult(
  owner: string,
  repo: string,
  queryIds: Array<string>,
  period: string,
  amount: number,
) {
  let url = `/api/github/${owner}/${repo}/search/count?period=${period}&amount=${amount}`;
  for (let queryId of queryIds) {
    url = url + "&queryId=" + queryId;
  }
  const { data, error } = useSWR(url, fetcher, {
    refreshInterval: 3600000,
  });
  return {
    data: data as Array<GithubIssueQueryCountTaskResult>,
    error,
    loading: !error && !data,
  };
}
