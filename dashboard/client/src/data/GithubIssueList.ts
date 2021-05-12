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
    pull_request?: {};
  };
}

export interface GithubIssueList {
  items: Array<GithubIssueListItem>;
  total: number;
  page: number;
  pageSize: number;
}

export type GithubIssueListStatus =
  | "TO_BE_REVIEWED"
  | "REVIEWED"
  | "TRIAGED"
  | "CLOSED";
export type GithubIssueListSort =
  | "EXPECTED_RESPOND_AT_ASC"
  | "EXPECTED_RESPOND_AT_DESC";

export interface GithubIssueListParams {
  isPullRequest?: boolean;
  status?: GithubIssueListStatus;
  page?: number;
  pageSize?: number;
  actionOwner?: string;
  sort?: GithubIssueListSort;
  labels?: Array<string>;
}

export function useGithubIssueList(
  params?: GithubIssueListParams
): GithubIssueListResult {
  const { data, error } = useSWR(
    queryString.stringifyUrl(
      { url: "/api/github/issues", query: params as any },
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

export interface GithubIssueListResult {
  data?: GithubIssueList;
  error?: any;
  loading: boolean;
}

export function useGithubIssueListActionOwner(params?: GithubIssueListParams) {
  const { data, error } = useSWR(
    queryString.stringifyUrl(
      { url: "/api/github/issues/owners", query: params as any },
      { skipNull: true }
    ),
    fetcher,
    {
      refreshInterval: 60000,
    }
  );
  return {
    data: data as Array<string>,
    error,
    loading: !error && !data,
  };
}
