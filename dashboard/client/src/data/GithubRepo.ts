import useSWR from "swr";

import fetcher from "./fetcher";

export interface GithubRepo {
  owner: string;
  repo: string;
}

export function useGithubRepo() {
  const { data, error } = useSWR(`/api/github/repos`, fetcher);
  return {
    data: data as Array<GithubRepo>,
    error,
    loading: !error && !data,
  };
}
