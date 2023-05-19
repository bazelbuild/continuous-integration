import React, { useEffect, useState } from "react";
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

function Chart(props: { data: any[]; domain: number[] | undefined }) {
  const data = props.data;
  return (
    <div style={{ width: "100%", height: 300 }} className="pr-[70px]">
      <ResponsiveContainer>
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="createdAt"
            tickFormatter={(tick) => {
              return DateTime.fromISO(tick).toFormat("MMM d");
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
            width={70}
            type="number"
            domain={props.domain}
            interval={0}
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

interface StatsParam {
  org: string;
  pipeline: string;
  from: string;
  branch: string;
}

function BuildStats({
  param,
  domain,
  setDomain,
}: {
  param: StatsParam;
  domain: number[] | undefined;
  setDomain: (domain: number[]) => void;
}) {
  const stats = useBuildkiteBuildStats(param.org, param.pipeline, {
    branch: param.branch,
    from: param.from,
  });
  useEffect(() => {
    if (domain === undefined && stats.data) {
      let max = 0;
      for (let item of stats.data.items) {
        const total = item.runTime + item.waitTime;
        max = Math.max(max, total);
      }
      max *= 1.1;
      console.log(max);
      setDomain([0, max]);
    }
  }, [stats]);

  if (stats.loading || stats.error || domain === undefined) {
    return <></>;
  }
  const data = stats.data.items;

  return (
    <div className="flex flex-col border shadow rounded bg-white ring-1 ring-black ring-opacity-5 flex-auto">
      <div className="bg-gray-100 flex flex-row items-center border-b">
        <span className="px-4 py-2 text-base font-medium">
          {param.org} / {param.pipeline} / {param.branch}
        </span>
      </div>
      <Chart data={data} domain={domain} />
    </div>
  );
}

function JobStats({
  param,
  domain,
}: {
  param: StatsParam;
  domain: number[] | undefined;
}) {
  const stats = useBuildkiteJobStats(param.org, param.pipeline, {
    branch: param.branch,
    from: param.from,
  });

  if (stats.loading || stats.error || domain === undefined) {
    return <></>;
  }

  const data = stats.data.items;
  var group = _.groupBy(data, (item) => item.bazelCITask);
  var sortedGroup = _.sortBy(group, (data) => {
    const max = _.maxBy(data, (item) => item.waitTime + item.runTime);
    return -(max?.runTime || 0);
  });
  return (
    <>
      {_.map(sortedGroup, (data) => (
        <div className="flex flex-col border shadow rounded bg-white ring-1 ring-black ring-opacity-5 flex-auto">
          <div className="bg-gray-100 flex flex-row items-center border-b">
            <span className="px-4 py-2 text-base font-medium">
              {data[0].bazelCITask} | {data[0].name}
            </span>
          </div>
          <Chart key={data[0].bazelCITask} data={data} domain={domain} />
        </div>
      ))}
    </>
  );
}

export default function Page() {
  const [domain, setDomain] = useState<number[]>();
  const param = {
    org: "bazel",
    pipeline: "bazel-bazel",
    branch: "master",
    from: DateTime.now().minus({ days: 30 }).toISO(),
  };
  return (
    <Layout>
      <div className="m-8 flex flex-col gap-8">
        <BuildStats param={param} domain={domain} setDomain={setDomain} />
        <JobStats param={param} domain={domain} />
      </div>
    </Layout>
  );
}
