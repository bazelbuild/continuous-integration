import classNames from "classnames";
import formatDistance from "date-fns/formatDistance";
import differenceInDays from "date-fns/differenceInDays";
import format from "date-fns/format";
import isAfter from "date-fns/isAfter";
import { useRouter } from "next/router";
import queryString from "query-string";

import {
  GithubIssueListItem,
  GithubIssueListParams,
  GithubIssueListStatus,
  useGithubIssueList,
  GithubIssueList as GithubIssueListData,
} from "./data/GithubIssueList";

function Status(props: {
  name: string;
  status: GithubIssueListStatus;
  count: number;
  currentStatus?: GithubIssueListStatus;
  changeStatus: (status: GithubIssueListStatus) => void;
}) {
  const active = props.status == props.currentStatus;
  const count = props.count;
  return (
    <a
      className={classNames(
        "cursor-pointer text-base relative hover:text-black",
        active ? "text-black" : "text-gray-600",
        {
          "font-medium": active,
        }
      )}
      onClick={() => props.changeStatus(props.status)}
    >
      {props.name}
      {count > 0 && (
        <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-red-100 transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full">
          {count > 99 ? "99+" : count}
        </span>
      )}
    </a>
  );
}

function colorHexToRGB(hex: string) {
  const r = parseInt(hex.substring(1, 3), 16);
  const g = parseInt(hex.substring(3, 5), 16);
  const b = parseInt(hex.substring(5, 7), 16);
  return { r, g, b };
}

function Label({
  name,
  colorHex,
  description,
}: {
  name: string;
  colorHex: string;
  description: string;
}) {
  const color = colorHexToRGB(colorHex);
  return (
    <a
      className="inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none rounded-full issue-label"
      style={
        {
          "--label-r": color.r,
          "--label-g": color.g,
          "--label-b": color.b,
        } as any
      }
      title={description}
    >
      {name}
    </a>
  );
}

function userLink(login: string) {
  return `https://github.com/${login}`;
}

function dateDistance(date: Date, base: Date) {
  const diff = Math.abs(differenceInDays(base, date));
  if (diff > 356) {
    return "on " + format(date, "MMM d");
  } else if (diff > 30) {
    return "on " + format(date, "MMM d");
  } else {
    return formatDistance(date, base, { addSuffix: true });
  }
}

function dayText(diff: number) {
  diff = Math.abs(diff);
  if (diff == 0) {
    return "less than 1 day";
  } else if (diff == 1) {
    return "1 day";
  } else {
    return `${diff} days`;
  }
}

function SLOStatus(props: { expectedRespondAt: string }) {
  const now = new Date();
  const expectedRespondAt = new Date(props.expectedRespondAt);

  const diffInDays = differenceInDays(expectedRespondAt, now);
  const days = dayText(diffInDays);
  let suffix;

  if (isAfter(now, expectedRespondAt)) {
    suffix = " overdue";
  } else {
    suffix = " to respond";
  }

  return (
    <div className="flex flex-col">
      <span className="mr-1">
        {days}
        {suffix}
      </span>
    </div>
  );
}

function ListItem(props: {
  item: GithubIssueListItem;
  changeActionOwner: (actionOwner: string) => void;
}) {
  const item = props.item;
  const issueLink = `https://github.com/${item.owner}/${item.repo}/issues/${item.issueNumber}`;
  return (
    <div className="flex flex-row">
      <svg
        className="flex-shrink-0 w-7 h-7 text-green-700 ml-4 mt-3 -mr-2"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="currentColor"
      >
        <path
          fillRule="evenodd"
          d="M8 1.5a6.5 6.5 0 100 13 6.5 6.5 0 000-13zM0 8a8 8 0 1116 0A8 8 0 010 8zm9 3a1 1 0 11-2 0 1 1 0 012 0zm-.25-6.25a.75.75 0 00-1.5 0v3.5a.75.75 0 001.5 0v-3.5z"
        />
      </svg>

      <div className="flex-auto flex flex-col space-y-1 p-2">
        <div className="flex flex-row space-x-1 space-y-1 flex-wrap">
          <a
            className="text-base font-medium hover:text-blue-github"
            target="_blank"
            href={issueLink}
          >
            {item.data.title}
          </a>
          {item.data.labels.map((label) => (
            <Label
              key={label.id}
              name={label.name}
              colorHex={`#${label.color}`}
              description={label.description}
            />
          ))}
        </div>
        <div className="flex flex-row text-gray-700 text-sm space-x-4">
          <span>
            <a
              href={issueLink}
              target="_blank"
              className="hover:text-blue-github"
            >{`#${item.issueNumber}`}</a>
            {" opened "}
            {dateDistance(new Date(item.data.created_at), new Date())}
            {" by "}
            <a
              target="_blank"
              href={userLink(item.data.user.login)}
              className="hover:text-blue-github"
            >
              {item.data.user.login}
            </a>
            {item.data.updated_at != item.data.created_at && (
              <span>
                {", updated "}
                {dateDistance(new Date(item.data.updated_at), new Date())}
              </span>
            )}
          </span>
        </div>
      </div>
      <div className="hidden md:flex flex-shrink-0 w-3/12 flex-row items-center">
        <div className="flex-1">
          <div className="flex flex-row -space-x-4 hover:space-x-1 justify-center">
            {item.data.assignees.map((assignee) => (
              <a
                key={assignee.login}
                title={`Assigned to ${assignee.login}`}
                className="transition-all relative"
                href={userLink(assignee.login)}
                target="_blank"
              >
                <img
                  className="inline object-cover w-6 h-6 rounded-full"
                  src={assignee.avatar_url}
                  alt={`@${assignee.login}`}
                />
              </a>
            ))}
          </div>
        </div>

        <div className="flex-1 flex flex-row justify-center">
          {item.actionOwner && (
            <a
              className="cursor-pointer"
              onClick={() => props.changeActionOwner(item.actionOwner!)}
            >
              @{item.actionOwner}
            </a>
          )}
        </div>

        <div className="flex-1 flex flex-col items-center">
          {item.expectedRespondAt && (
            <SLOStatus expectedRespondAt={item.expectedRespondAt} />
          )}
        </div>
      </div>
    </div>
  );
}

function defaultGithubIssueListParams(): GithubIssueListParams {
  return {
    status: "TO_BE_REVIEWED",
    page: 1,
    isPullRequest: false,
  };
}

function GithubIssueListBody(props: {
  data: GithubIssueListData;
  loading: boolean;
  error: any;
  changeActionOwner: (actionOwner: string) => void;
}) {
  const data = props.data;

  if (props.loading) {
    return (
      <div className="flex justify-center py-8">
        <svg
          className="animate-spin h-8 w-8 text-gray-700"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      </div>
    );
  }

  if (props.error || !data.items) {
    return <div className="p-4">Error</div>;
  }

  if (data.items.length == 0) {
    return (
      <div className="flex flex-col items-center p-12">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-8 w-8 text-gray-300"
          viewBox="0 0 24 24"
          fill="currentColor"
        >
          <path d="M12 7a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0112 7zm1 9a1 1 0 11-2 0 1 1 0 012 0z" />
          <path
            fillRule="evenodd"
            d="M12 1C5.925 1 1 5.925 1 12s4.925 11 11 11 11-4.925 11-11S18.075 1 12 1zM2.5 12a9.5 9.5 0 1119 0 9.5 9.5 0 01-19 0z"
          />
        </svg>
        <div className="text-xl font-medium mt-4">No results found.</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      {data.items.map((item) => (
        <div key={item.data.id} className="border-t hover:bg-gray-100">
          <ListItem item={item} changeActionOwner={props.changeActionOwner} />
        </div>
      ))}
    </div>
  );
}

function GithubIssueListFooter(props: {
  page: number;
  total: number;
  goToPage: (page: number) => void;
}) {
  const page = props.page;
  const total = props.total;
  const pageSize = 10;
  const lastPage = Math.ceil(total / pageSize);

  const start = 1 + pageSize * (page - 1);
  const end = Math.min(total, start + pageSize - 1);

  if (start > total) {
    return null;
  }

  return (
    <div className="flex flex-row-reverse mt-2">
      <div className="flex space-x-2 flex-row items-center">
        <span className="mr-4">
          {start}-{end} of {props.total}
        </span>

        <button
          className="h-8 px-1 rounded-lg ring-gray-300 hover:ring-1 focus:outline-none disabled:text-gray-400"
          disabled={page == 1}
          onClick={() => props.goToPage(page - 1)}
        >
          <svg
            className="w-6 h-6"
            focusable="false"
            viewBox="0 0 24 24"
            aria-hidden="true"
            fill="currentColor"
          >
            <path d="M15.41 16.09l-4.58-4.59 4.58-4.59L14 5.5l-6 6 6 6z" />
          </svg>
        </button>

        <button
          className="h-8 px-1 rounded-lg ring-gray-300 hover:ring-1 focus:outline-none disabled:text-gray-400"
          disabled={page == lastPage}
          onClick={() => props.goToPage(page + 1)}
        >
          <svg
            className="w-6 h-6"
            focusable="false"
            viewBox="0 0 24 24"
            aria-hidden="true"
            fill="currentColor"
          >
            <path d="M8.59 16.34l4.58-4.59-4.58-4.59L10 5.75l6 6-6 6z" />
          </svg>
        </button>
      </div>
    </div>
  );
}

export default function GithubIssueList({
  owner,
  repo,
  queryKey,
}: {
  owner: string;
  repo: string;
  queryKey: string;
}) {
  const router = useRouter();
  const query = queryString.parseUrl(router.asPath);
  const params: GithubIssueListParams = query.query[queryKey]
    ? (JSON.parse(query.query[queryKey] as string) as GithubIssueListParams)
    : defaultGithubIssueListParams();

  const needReviewCount = useGithubIssueList(owner, repo, {
    status: "TO_BE_REVIEWED",
    isPullRequest: false,
  });
  const needTriageCount = useGithubIssueList(owner, repo, {
    status: "REVIEWED",
    isPullRequest: false,
    actionOwner: params.actionOwner,
  });

  const githubIssueList = useGithubIssueList(owner, repo, params);

  const changeParams = (newParams: GithubIssueListParams) => {
    let newQuery = { ...query.query };
    newQuery[queryKey] = JSON.stringify(newParams);

    const newUrl = queryString.stringifyUrl({
      url: query.url,
      query: newQuery,
    });
    router.push(newUrl, undefined, { scroll: false });
  };

  const changeStatus = (status: GithubIssueListStatus) => {
    let newParams = { ...params };
    newParams.status = status;
    if (status == "TO_BE_REVIEWED") {
      newParams.actionOwner = undefined;
    }
    newParams.page = 1;
    changeParams(newParams);
  };

  const changeActionOwner = (actionOwner: string | undefined) => {
    let newParams = { ...params };
    newParams.actionOwner = actionOwner;
    newParams.page = 1;
    changeParams(newParams);
  };

  const goToPage = (page: number) => {
    let newParams = { ...params };
    newParams.page = page;
    changeParams(newParams);
  };

  return (
    <div className="flex flex-col">
      <div className="flex flex-col border shadow rounded bg-white ring-1 ring-black ring-opacity-5">
        <div className="bg-gray-100 flex flex-row items-center">
          <div className="flex-auto flex space-x-6 p-4">
            <Status
              name="Need Review"
              status="TO_BE_REVIEWED"
              count={
                (!needReviewCount.loading &&
                  !needReviewCount.error &&
                  needReviewCount.data &&
                  needReviewCount.data.total) ||
                0
              }
              currentStatus={params.status}
              changeStatus={changeStatus}
            />
            <Status
              name="Need Triage"
              status="REVIEWED"
              count={
                (!needTriageCount.loading &&
                  !needTriageCount.error &&
                  needTriageCount.data &&
                  needTriageCount.data.total) ||
                0
              }
              currentStatus={params.status}
              changeStatus={changeStatus}
            />
            <Status
              name="Triaged"
              status="TRIAGED"
              count={0}
              currentStatus={params.status}
              changeStatus={changeStatus}
            />
          </div>
          <div className="flex-shrink-0 w-3/12 flex flex-row">
            <div className="flex-1 flex flex-row justify-center">
              <span className="text-base text-gray-600 font-medium">
                Assignees
              </span>
            </div>
            {params.actionOwner && (
              <a
                className="flex-1 flex flex-row justify-center items-center space-x-1 text-gray-600 hover:text-black cursor-pointer"
                onClick={() => changeActionOwner(undefined)}
              >
                <span className="font-bold text-base">
                  @{params.actionOwner}
                </span>
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </a>
            )}
            {!params.actionOwner && (
              <a className="flex-1 flex flex-row justify-center items-center space-x-1 text-gray-600 hover:text-black cursor-pointer">
                <span className="text-base font-medium">Owner</span>
                <span>
                  <svg
                    className="w-3 h-3"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 1024 1024"
                    fill="currentColor"
                  >
                    <path d="M163.446154 275.692308h697.107692c19.692308 0 33.476923 25.6 17.723077 43.323077L537.6 736.492308c-11.815385 15.753846-37.415385 15.753846-49.230769 0L143.753846 319.015385c-13.784615-17.723077-1.969231-43.323077 19.692308-43.323077z" />
                  </svg>
                </span>
              </a>
            )}
            <div className="flex-1 flex flex-row justify-center">
              <span className="text-base text-gray-600 font-medium">
                SLO Status
              </span>
            </div>
          </div>
        </div>

        <GithubIssueListBody
          {...githubIssueList}
          changeActionOwner={changeActionOwner}
        />
      </div>
      {!githubIssueList.loading &&
        !githubIssueList.error &&
        githubIssueList.data && (
          <GithubIssueListFooter
            page={params.page!}
            total={githubIssueList.data.total}
            goToPage={goToPage}
          />
        )}
    </div>
  );
}
