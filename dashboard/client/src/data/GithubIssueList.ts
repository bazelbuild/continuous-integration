import useSWR from "swr";
import queryString from "query-string";

import fetcher from "./fetcher";

export interface GithubIssueListItemUser {
  login: string;
  avatar_url: string;
}

export interface GithubIssueListItem {
  owner: string;
  repo: string;
  issueNumber: number;
  status: string;
  expectedRespondAt?: string;
  data: {
    id: number;
    user: GithubIssueListItemUser;
    created_at: string;
    title: string;
    labels: Array<{
      id: number;
      name: string;
      color: string;
      description: string;
    }>;
    assignees: Array<GithubIssueListItemUser>;
  };
}

export interface GithubIssueList {
  items: Array<GithubIssueListItem>;
}

export function useGithubIssueList(
  owner: string,
  repo: string,
  params: {
    status?: 'TO_BE_REVIEWED' | 'REVIEWED' | 'TRIAGED' | 'CLOSED';
  }
) {
  const { data, error } = useSWR(
    queryString.stringifyUrl(
      { url: `/api/github/${owner}/${repo}/issues`, query: params },
      { skipNull: true }
    ),
    fetcher,
    {
      refreshInterval: 60000,
    }
  );
  return {
    data: data as GithubIssueList,
    error,
    loading: !error && !data,
  };
}
