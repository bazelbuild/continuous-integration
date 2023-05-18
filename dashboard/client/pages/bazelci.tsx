import React from "react";
import Layout from "../src/Layout";
import { useBuildkiteBuildStats } from "../src/data/BuildkiteBuildStats";
import { useBuildkiteJobStats } from "../src/data/BuildkiteJobStats";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { DateTime } from "luxon";
import { intervalToDuration } from "date-fns";
import _ from "lodash";

function formatDuration(dur: Duration) {
  var items = [
    { value: dur.days, unit: "d" },
    { value: dur.hours, unit: "h" },
    { value: dur.minutes, unit: "m" },
    { value: dur.seconds, unit: "s" },
  ].filter((item) => item.value);

  if (items.length == 0) {
    return "0s";
  }

  if (items.length > 2) {
    items.length = 2;
  }

  return items.map((item) => `${item.value}${item.unit}`).join(" ");
}

function Chart(props: { data: any[] }) {
  return (
    <div style={{ width: "100%", height: 300 }}>
      <ResponsiveContainer>
        <AreaChart data={props.data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="createdAt"
            tickFormatter={(tick) => {
              return DateTime.fromISO(tick).toFormat("HH:mm");
            }}
          />
          <YAxis
            tickFormatter={(tick) => {
              const dur = intervalToDuration({
                start: 0,
                end: tick * 1000,
              });
              return formatDuration(dur);
            }}
          />
          <Tooltip
            formatter={(value: any, name: any) => {
              if (name.endsWith("Time")) {
                const dur = intervalToDuration({
                  start: 0,
                  end: value * 1000,
                });
                return formatDuration(dur);
              }
              return value;
            }}
          />
          <Area
            type="monotone"
            dataKey="waitTime"
            stackId="1"
            stroke="#ffc658"
            fill="#ffc658"
          />
          <Area
            type="monotone"
            dataKey="runTime"
            stackId="1"
            stroke="#82ca9d"
            fill="#82ca9d"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function BuildStats({ org, pipeline }: { org: string; pipeline: string }) {
  const stats = useBuildkiteBuildStats(org, pipeline, {
    branch: "master",
    from: "2023-04-18T00:00:00Z",
  });

  if (stats.loading || stats.error) {
    return <></>;
  }

  const data = stats.data.items;

  return (
    <div className="flex flex-col border shadow rounded bg-white ring-1 ring-black ring-opacity-5 flex-auto">
      <div className="bg-gray-100 flex flex-row items-center border-b">
        <span className="px-4 py-2 text-base font-medium">Build Time</span>
      </div>
      <Chart data={data} />
    </div>
  );
}

function JobStats({ org, pipeline }: { org: string; pipeline: string }) {
  const stats = useBuildkiteJobStats(org, pipeline, {
    branch: "master",
    from: "2023-04-18T00:00:00Z",
  });

  if (stats.loading || stats.error) {
    return <></>;
  }

  const data = stats.data.items;
  var group = _.groupBy(data, (item) => item.bazelCITask);
  return (
    <>
      {_.map(group, (data) => (
        <div className="flex flex-col border shadow rounded bg-white ring-1 ring-black ring-opacity-5 flex-auto">
          <div className="bg-gray-100 flex flex-row items-center border-b">
            <span className="px-4 py-2 text-base font-medium">
              {data[0].name} / {data[0].bazelCITask}
            </span>
          </div>
          <Chart key={data[0].bazelCITask} data={data} />
        </div>
      ))}
    </>
  );
}

export default function Page() {
  return (
    <Layout>
      <div className="m-8 flex flex-col gap-8">
        <BuildStats org="bazel" pipeline="bazel-bazel" />
        <JobStats org="bazel" pipeline="bazel-bazel" />
      </div>
    </Layout>
  );
}
