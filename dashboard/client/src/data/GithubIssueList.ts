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
  actionOwner?: string;
  data: {
    id: number;
    user: GithubIssueListItemUser;
    created_at: string;
    updated_at: string;
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
  total: number;
}

export type GithubIssueListStatus = 'TO_BE_REVIEWED' | 'REVIEWED' | 'TRIAGED' | 'CLOSED';

export interface GithubIssueListParams {
  isPullRequest?: boolean,
  status?: GithubIssueListStatus,
  page?: number,
  actionOwner?: string,
}

export function useGithubIssueList(
  owner: string,
  repo: string,
  params?: GithubIssueListParams,
) {
  const { data, error } = useSWR(
    queryString.stringifyUrl(
      { url: `/api/github/${owner}/${repo}/issues`, query: params as any },
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
