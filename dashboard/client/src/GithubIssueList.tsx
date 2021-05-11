import React, { ReactNode, useState } from "react";
import { Transition } from "@headlessui/react";
import classNames from "classnames";
import {
  formatDistance,
  differenceInDays,
  differenceInHours,
  format,
  isAfter,
} from "date-fns";

import {
  GithubIssueListItem,
  GithubIssueListParams,
  GithubIssueListStatus,
  useGithubIssueList,
  GithubIssueList as GithubIssueListData,
  GithubIssueListSort,
  useGithubIssueListActionOwner,
  GithubIssueListResult,
} from "./data/GithubIssueList";

const LABEL_P0 = "P0";
const LABEL_P1 = "P1";
const LABEL_P2 = "P2";
const LABEL_TYPE_BUG = "type: bug";

function Status(props: {
  name: string;
  active?: boolean;
  count?: GithubIssueListResult;
  changeStatus: () => void;
}) {
  const active = props.active;
  const result = props.count;
  const count =
    (result &&
      !result.loading &&
      !result.error &&
      result.data &&
      result.data.total) ||
    0;
  return (
    <a
      className={classNames(
        "cursor-pointer text-base relative hover:text-black",
        active ? "text-black" : "text-gray-600",
        {
          "font-medium": active,
        }
      )}
      onClick={() => props.changeStatus()}
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

function SLOStatus(props: { expectedRespondAt: string; updatedAt: string }) {
  const now = new Date();
  const expectedRespondAt = new Date(props.expectedRespondAt);

  const diffInDays = differenceInDays(expectedRespondAt, now);
  const days = dayText(diffInDays);
  const overdue = isAfter(now, expectedRespondAt);
  let colorBg = "#ecd5d5";
  let colorFg = "#de3b3b";
  let percentage = 0.0;

  let suffix;
  if (overdue) {
    suffix = " overdue";
  } else {
    suffix = " to respond";
    const total = differenceInHours(
      expectedRespondAt,
      new Date(props.updatedAt)
    );
    if (total > 0) {
      percentage = differenceInHours(expectedRespondAt, now) / total;
      if (percentage > 0.7) {
        colorBg = "#ddecdb";
        colorFg = "#92cb8a";
      } else if (percentage > 0.3) {
        colorBg = "#e2e0d3";
        colorFg = "#cfc50f";
      }
    }
  }

  return (
    <div className="flex flex-col w-full">
      <span className="mr-1 text-center">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5 inline-block mr-1 text-red-600"
          style={{ color: colorFg }}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        {days}
        {suffix}
      </span>

      {percentage > 0.0 && (
        <div
          className="overflow-hidden h-1 text-xs flex rounded flex-auto my-2 mx-4"
          style={{
            backgroundColor: colorBg,
          }}
        >
          <div
            style={{
              width: `${Math.round(percentage * 100)}%`,
              backgroundColor: colorFg,
            }}
            className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center"
          />
        </div>
      )}
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
      {!item.data.pull_request ? (
        <svg
          className="flex-shrink-0 w-5 h-5 text-green-700 ml-4 mt-3"
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 16 16"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M8 1.5a6.5 6.5 0 100 13 6.5 6.5 0 000-13zM0 8a8 8 0 1116 0A8 8 0 010 8zm9 3a1 1 0 11-2 0 1 1 0 012 0zm-.25-6.25a.75.75 0 00-1.5 0v3.5a.75.75 0 001.5 0v-3.5z"
          />
        </svg>
      ) : (
        <svg
          className="flex-shrink-0 w-5 h-5 text-green-700 ml-4 mt-3"
          viewBox="0 0 16 16"
          xmlns="http://www.w3.org/2000/svg"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M7.177 3.073L9.573.677A.25.25 0 0110 .854v4.792a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122v5.256a2.251 2.251 0 11-1.5 0V5.372A2.25 2.25 0 011.5 3.25zM11 2.5h-1V4h1a1 1 0 011 1v5.628a2.251 2.251 0 101.5 0V5A2.5 2.5 0 0011 2.5zm1 10.25a.75.75 0 111.5 0 .75.75 0 01-1.5 0zM3.75 12a.75.75 0 100 1.5.75.75 0 000-1.5z"
          />
        </svg>
      )}

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
      <div className="hidden md:flex flex-shrink-0 w-4/12 flex-row">
        <div className="flex-1 mt-4">
          <div className="flex flex-row -space-x-4 hover:space-x-1 justify-center">
            {item.data.assignees.map((assignee) => (
              <a
                key={assignee.login}
                title={`Assigned to ${assignee.login}`}
                className="transition-all"
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

        <div className="flex-1 flex flex-row mt-4 justify-center">
          {item.actionOwner && (
            <a
              className="cursor-pointer hover:font-bold"
              onClick={() => props.changeActionOwner(item.actionOwner!)}
            >
              {item.actionOwner}
            </a>
          )}
        </div>

        <div className="flex-1 flex flex-col mt-4 items-center">
          {item.expectedRespondAt && (
            <SLOStatus
              expectedRespondAt={item.expectedRespondAt}
              updatedAt={item.data.updated_at}
            />
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
  data?: GithubIssueListData;
  loading: boolean;
  error?: any;
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

  if (props.error || !data || !data.items) {
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

function DownIcon() {
  return (
    <svg
      className="w-3 h-3"
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 1024 1024"
      fill="currentColor"
    >
      <path d="M163.446154 275.692308h697.107692c19.692308 0 33.476923 25.6 17.723077 43.323077L537.6 736.492308c-11.815385 15.753846-37.415385 15.753846-49.230769 0L143.753846 319.015385c-13.784615-17.723077-1.969231-43.323077 19.692308-43.323077z" />
    </svg>
  );
}

function Popup(props: {
  title: string;
  show: boolean;
  children: NonNullable<ReactNode>;
  onClose: () => void;
}) {
  return (
    <Transition
      show={props.show}
      enter="transition duration-100 ease-out z-50"
      enterFrom="transform -translate-y-10 opacity-0"
      enterTo="transform translate-y-0 opacity-100"
      leave="transition duration-100 ease-out z-50"
      leaveFrom="transform opacity-100"
      leaveTo="transform opacity-0"
    >
      <div
        className="fixed top-0 right-0 left-0 bottom-0 z-50"
        onClick={() => props.onClose()}
      />
      <div className="absolute right-0 border shadow rounded bg-white z-50 flex flex-col mt-2">
        <div className="flex flex-row justify-between items-center border-b px-2">
          <span className="p-2 text-base font-bold">{props.title}</span>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-4 w-4 cursor-pointer"
            onClick={() => props.onClose()}
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
        </div>

        {props.children}
      </div>
    </Transition>
  );
}

function FilterButton(props: { name: string; onClick: () => void }) {
  return (
    <a
      className="flex flex-row items-center space-x-1 text-gray-600 hover:text-black cursor-pointer select-none"
      onClick={() => props.onClick()}
    >
      <span className="text-base font-medium">{props.name}</span>
      <DownIcon />
    </a>
  );
}

function ActionOwnerFilterBody(
  props: ActionOwnerFilterProps & { onClose: () => void }
) {
  const result = useGithubIssueListActionOwner(props.params);

  console.log(result);

  const { data, loading, error } = result;
  if (loading || error) {
    return null;
  }

  if (!data || data.length == 0) {
    return <div className="px-5 py-2 border-b">No results found.</div>;
  }

  return (
    <div className="max-h-[300px] overflow-y-scroll">
      {data.map((owner) => (
        <div
          key={owner}
          className="p-2 border-b flex flex-row space-x-2 items-center hover:bg-gray-100 cursor-pointer"
          onClick={() => {
            props.changeActionOwner(owner);
            props.onClose();
          }}
        >
          {owner === props.activeOwner ? (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          ) : (
            <div className="w-5 h-5" />
          )}

          <span
            className={classNames("text-base", {
              "font-bold": owner === props.activeOwner,
            })}
          >
            {owner}
          </span>
        </div>
      ))}
    </div>
  );
}

export interface ActionOwnerFilterProps {
  changeActionOwner: (actionOwner: string) => void;
  activeOwner?: string;
  params?: GithubIssueListParams;
}

function ActionOwnerFilter(props: ActionOwnerFilterProps) {
  const [show, setShow] = useState(false);

  return (
    <span className="relative">
      <FilterButton name="Owner" onClick={() => setShow(!show)} />
      <Popup
        title="Filter by action owner"
        show={show}
        onClose={() => setShow(false)}
      >
        <div className="w-[300px]">
          <ActionOwnerFilterBody {...props} onClose={() => setShow(false)} />
        </div>
      </Popup>
    </span>
  );
}

function SortFilter(props: {
  changeSort: (sort: GithubIssueListSort) => void;
  activeSort?: GithubIssueListSort;
}) {
  const [show, setShow] = useState(false);

  return (
    <span className="relative">
      <FilterButton name="Sort" onClick={() => setShow(!show)} />
      <Popup title={"Sort by"} show={show} onClose={() => setShow(false)}>
        {[
          { name: "Most urgent", key: "EXPECTED_RESPOND_AT_ASC" },
          { name: "Newest", key: "EXPECTED_RESPOND_AT_DESC" },
        ].map((sort) => (
          <div
            key={sort.key}
            className="p-2 border-b flex flex-row space-x-2 items-center hover:bg-gray-100 cursor-pointer w-[300px]"
            onClick={() => {
              props.changeSort(sort.key as any);
              setShow(false);
            }}
          >
            {sort.key == props.activeSort ? (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            ) : (
              <div className="w-5 h-5" />
            )}

            <span
              className={classNames("text-base", {
                "font-bold": sort.key == props.activeSort,
              })}
            >
              {sort.name}
            </span>
          </div>
        ))}
      </Popup>
    </span>
  );
}

function FilterLabel(props: { name: string; onClear: () => void }) {
  return (
    <a className="inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none rounded-full bg-gray-300 space-x-1">
      <span className="text-s">{props.name}</span>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        className="h-3 w-3 cursor-pointer"
        onClick={() => props.onClear()}
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
  );
}

function labelContains(
  labels: Array<string> | undefined,
  label: string
): boolean {
  if (!labels) {
    return false;
  }

  return !!labels.find((l) => l === label);
}

function useGithubIssueListForListBody(params: GithubIssueListParams) {
  let requestParams = { ...params };
  if (params.status === "TO_BE_REVIEWED") {
    requestParams.actionOwner = undefined;
  }
  if (
    !params.sort &&
    (labelContains(params.labels, LABEL_P0) ||
      labelContains(params.labels, LABEL_P1) ||
      labelContains(params.labels, LABEL_P2))
  ) {
    requestParams.sort = "EXPECTED_RESPOND_AT_ASC";
  }
  return useGithubIssueList(requestParams);
}

export default function GithubIssueList(props: {
  paramString?: string;
  changeParams: (params: string) => void;
}) {
  let params: GithubIssueListParams = defaultGithubIssueListParams();
  if (props.paramString) {
    try {
      params = JSON.parse(props.paramString) as GithubIssueListParams;
    } catch (e) {
      console.error(e);
    }
  }

  const needReviewCount = useGithubIssueList({
    status: "TO_BE_REVIEWED",
    isPullRequest: false,
  });
  const needTriageCount = useGithubIssueList({
    status: "REVIEWED",
    isPullRequest: false,
    actionOwner: params.actionOwner,
  });
  const p0BugsCount = useGithubIssueList({
    status: "TRIAGED",
    labels: [LABEL_P0],
    isPullRequest: false,
    actionOwner: params.actionOwner,
  });
  const p1BugsCount = useGithubIssueList({
    status: "TRIAGED",
    labels: [LABEL_P1],
    isPullRequest: false,
    actionOwner: params.actionOwner,
  });
  const p2BugsCount = useGithubIssueList({
    status: "TRIAGED",
    labels: [LABEL_P2],
    isPullRequest: false,
    actionOwner: params.actionOwner,
  });

  const githubIssueList = useGithubIssueListForListBody(params);

  const changeParams = (newParams: GithubIssueListParams) => {
    props.changeParams(JSON.stringify(newParams));
  };

  const changeStatus = (
    status: GithubIssueListStatus,
    labels?: Array<string>
  ) => {
    let newParams = { ...params };
    newParams.status = status;
    newParams.labels = labels;
    newParams.page = 1;
    changeParams(newParams);
  };

  const changeActionOwner = (actionOwner: string | undefined) => {
    let newParams = { ...params };
    newParams.actionOwner = actionOwner;
    newParams.page = 1;
    changeParams(newParams);
  };

  const changeSort = (sort: GithubIssueListSort | undefined) => {
    let newParams = { ...params };
    newParams.sort = sort;
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
          <div className="flex-shrink-0 flex space-x-6 p-4">
            <Status
              name="Need Review"
              active={params.status == "TO_BE_REVIEWED"}
              count={needReviewCount}
              changeStatus={() => changeStatus("TO_BE_REVIEWED")}
            />
            <Status
              name="Need Triage"
              active={params.status == "REVIEWED"}
              count={needTriageCount}
              changeStatus={() => changeStatus("REVIEWED")}
            />
            <Status
              name="P0 Issues"
              active={
                params.status == "TRIAGED" &&
                labelContains(params.labels, LABEL_P0)
              }
              count={p0BugsCount}
              changeStatus={() => changeStatus("TRIAGED", [LABEL_P0])}
            />
            <Status
              name="P1 Issues"
              active={
                params.status == "TRIAGED" &&
                labelContains(params.labels, LABEL_P1)
              }
              count={p1BugsCount}
              changeStatus={() => changeStatus("TRIAGED", [LABEL_P1])}
            />
            <Status
              name="P2 Issues"
              active={
                params.status == "TRIAGED" &&
                labelContains(params.labels, LABEL_P2)
              }
              count={p2BugsCount}
              changeStatus={() => changeStatus("TRIAGED", [LABEL_P2])}
            />
          </div>

          <div className="flex-auto ml-4 space-x-2">
            {params.actionOwner && (
              <FilterLabel
                name={`Owner: ${params.actionOwner}`}
                onClear={() => changeActionOwner(undefined)}
              />
            )}

            {params.sort && (
              <FilterLabel
                name={`Sort: ${params.sort}`}
                onClear={() => changeSort(undefined)}
              />
            )}
          </div>

          <div className="flex-shrink-0 w-4/12 flex flex-row">
            <div className="flex-1 flex flex-row justify-center">
              <span className="text-base text-gray-600 font-medium">
                {/* intentionally empty */}
              </span>
            </div>
            <div className="flex-1 flex flex-row justify-center">
              <ActionOwnerFilter
                changeActionOwner={changeActionOwner}
                activeOwner={params.actionOwner}
                params={params}
              />
            </div>
            <div className="flex-1 flex flex-row justify-center">
              <SortFilter changeSort={changeSort} activeSort={params.sort} />
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
