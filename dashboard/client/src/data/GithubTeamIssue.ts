import useSWR from "swr";

import fetcher from "./fetcher";

export interface GithubTeam {
  owner: string;
  repo: string;
  label: string;
  name: string;
  teamOwner: string;
}

export interface GithubTeamIssueStats {
  url: string;
  count: number | null;
}

export interface GithubTeamIssue {
  team: GithubTeam;
  openIssues: GithubTeamIssueStats;
  openP0Issues: GithubTeamIssueStats;
  openP1Issues: GithubTeamIssueStats;
  openP2Issues: GithubTeamIssueStats;
  openP3Issues: GithubTeamIssueStats;
  openP4Issues: GithubTeamIssueStats;
  openNoTypeIssues: GithubTeamIssueStats;
  openNoPriorityIssues: GithubTeamIssueStats;
  openUntriagedIssues: GithubTeamIssueStats;
  openPullRequests: GithubTeamIssueStats;
  updatedAt: string;
}

export function useGithubTeamIssues(owner: string, repo: string) {
  const { data, error } = useSWR(
    `/api/github/${owner}/${repo}/teams/issues`,
    fetcher,
    {
      refreshInterval: 60000,
    }
  );
  return {
    data: data as Array<GithubTeamIssue>,
    error,
    loading: !error && !data,
  };
}

