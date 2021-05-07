import classNames from "classnames";
import {
  GithubIssueListItem,
  useGithubIssueList,
} from "./data/GithubIssueList";
import formatDistance from "date-fns/formatDistance";
import differenceInCalendarDays from "date-fns/differenceInCalendarDays";
import format from "date-fns/format";

function Status({ name, active }: { name: string; active?: boolean }) {
  return (
    <a
      className={classNames(
        "text-base",
        active ? "text-black" : "text-gray-600",
        {
          "font-medium": active,
        }
      )}
    >
      {name}
    </a>
  );
}

function Label({
  name,
  color,
  description,
}: {
  name: string;
  color: string;
  description: string;
}) {
  return (
    <a
      className="inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none rounded-full"
      style={{ backgroundColor: color, color: "white" }}
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
  const diff = Math.abs(differenceInCalendarDays(base, date));
  if (diff > 356) {
    return "on " + format(date, "MMM d");
  } else if (diff > 30) {
    return "on " + format(date, "MMM d");
  } else {
    return formatDistance(date, base, { addSuffix: true });
  }
}

function ListItem({ item }: { item: GithubIssueListItem }) {
  const issueLink = `https://github.com/${item.owner}/${item.repo}/issues/${item.issueNumber}`;
  return (
    <div className="flex">
      <div className="ml-4 flex-auto flex flex-col space-y-1 p-2">
        <div className="flex flex-row space-x-1 space-y-1 flex-wrap">
          <a
            className="text-base font-medium hover:text-blue-700"
            target="_blank"
            href={issueLink}
          >
            {item.data.title}
          </a>
          {item.data.labels.map((label) => (
            <Label
              key={label.id}
              name={label.name}
              color={`#${label.color}`}
              description={label.description}
            />
          ))}
        </div>
        <div className="flex flex-row text-gray-700 text-sm space-x-4">
          <span>
            <a
              href={issueLink}
              target="_blank"
              className="hover:text-blue-700"
            >{`#${item.issueNumber}`}</a>
            {" opened "}
            {dateDistance(new Date(item.data.created_at), new Date())}
            {" by "}
            <a
              target="_blank"
              href={userLink(item.data.user.login)}
              className="hover:text-blue-700"
            >
              {item.data.user.login}
            </a>
          </span>

          {/*{item.expectedRespondAt && (*/}
          {/*  <span>*/}
          {/*    expected to response{" "}*/}
          {/*    {dateDistance(new Date(item.expectedRespondAt), new Date())}*/}
          {/*  </span>*/}
          {/*)}*/}
        </div>
      </div>
      <div className="flex-shrink-0 w-3/12 flex flex-row">
        <div className="flex-1"></div>

        <div className="flex-1">
          <div className="flex flex-row -space-x-4 mt-4 hover:space-x-1">
            {item.data.assignees.map((assignee) => (
              <a
                key={assignee.login}
                title={`Assigned to ${assignee.login}`}
                className="transition-all relative"
                href={assignee.login}
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

        <div className="flex-1">
          <div className="mt-4"></div>
        </div>
      </div>
    </div>
  );
}

export default function GithubIssueList({
  owner,
  repo,
}: {
  owner: string;
  repo: string;
}) {
  const { data, error, loading } = useGithubIssueList(owner, repo, { status: 'TO_BE_REVIEWED' });

  if (loading) {
    return <span>loading</span>;
  }

  if (error) {
    return <span>error</span>;
  }

  return (
    <div className="flex flex-col border shadow rounded bg-white ring-1 ring-black ring-opacity-5">
      <div className="p-4 bg-gray-100 flex justify-between">
        <div className="flex space-x-4">
          <Status name="Need Review" active={true} />
          <Status name="Need Triage" />
          <Status name="Triaged" />
          <Status name="Closed" />
        </div>
        <div className="flex">
          <div className="flex">
            <span className="text-base text-gray-600">Sort</span>
          </div>
        </div>
      </div>
      <div className="flex flex-col">
        {data.items.map((item) => (
          <div key={item.data.id} className="border-t hover:bg-gray-100">
            <ListItem item={item} />
          </div>
        ))}
      </div>
    </div>
  );
}
