import React, { useEffect, useMemo, useState } from "react";
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

function Chart(props: {
  org: string;
  pipeline: string;
  data: any[];
  domain: number[] | undefined;
  excludeWaitTime: boolean;
}) {
  const data = props.data;
  return (
    <div style={{ width: "100%", height: 200 }} className="pr-[70px]">
      <ResponsiveContainer>
        <AreaChart data={data} syncId="stats">
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
            content={({ active, payload, label }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-gray-100 p-2 border">
                    <p>Build: {data.buildNumber}</p>
                    {data.jobId && <p>Job: {data.jobId}</p>}
                    <p>
                      {DateTime.fromISO(data.createdAt).toLocaleString(
                        DateTime.DATETIME_SHORT
                      )}
                    </p>
                    <p>
                      Wait Time:{" "}
                      {formatDuration(
                        intervalToDuration({
                          start: 0,
                          end: data.waitTime * 1000,
                        })
                      )}
                    </p>
                    <p>
                      Run Time:{" "}
                      {formatDuration(
                        intervalToDuration({
                          start: 0,
                          end: data.runTime * 1000,
                        })
                      )}
                    </p>
                  </div>
                );
              }
              return null;
            }}
          />
          {!props.excludeWaitTime && (
            <Area
              type="monotone"
              dataKey="waitTime"
              stackId="1"
              stroke="#ffc658"
              fill="#ffc658"
            />
          )}
          <Area
            type="monotone"
            dataKey="runTime"
            stackId="1"
            stroke="#82ca9d"
            fill="#82ca9d"
            activeDot={{
              onClick: (_, e: any) => {
                const payload = e.payload;
                const url = `https://buildkite.com/${props.org}/${
                  props.pipeline
                }/builds/${payload.buildNumber}#${
                  payload.jobId ? payload.jobId : ""
                }`;
                window.open(url, "_blank");
              },
            }}
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
  monthOffset,
  setMonthOffset,
  excludeWaitTime,
  setExcludeWaitTime,
}: {
  param: StatsParam;
  domain: number[] | undefined;
  setDomain: (domain: number[]) => void;
  monthOffset: number;
  setMonthOffset: (monthOffset: number) => void;
  excludeWaitTime: boolean;
  setExcludeWaitTime: (excludeWaitTime: boolean) => void;
}) {
  const stats = useBuildkiteBuildStats(param.org, param.pipeline, {
    branch: param.branch,
    from: param.from,
  });
  useEffect(() => {
    if (domain === undefined && stats.data) {
      let max = 0;
      for (let item of stats.data.items) {
        const total = excludeWaitTime
          ? item.runTime
          : item.waitTime + item.runTime;
        max = Math.max(max, total);
      }
      max *= 1.1;
      setDomain([0, max]);
    }
  }, [stats, excludeWaitTime]);

  if (stats.loading || stats.error || domain === undefined) {
    return <></>;
  }
  const data = stats.data.items;

  return (
    <div className="flex flex-col border shadow rounded bg-white ring-1 ring-black ring-opacity-5 flex-auto">
      <div className="bg-gray-100 flex flex-row items-center border-b px-4 py-2">
        <div className="flex-auto flex">
          <span className="text-base font-medium">
            {param.org} / {param.pipeline} / {param.branch}
          </span>
        </div>
        <div className="flex flex-row space-x-2">
          <label>
            <span className="mx-2">Exclude Wait Time</span>
            <input
              id="exclude-wait-time"
              type="checkbox"
              name="Exclude Wait Time"
              checked={excludeWaitTime}
              onChange={(e) => setExcludeWaitTime(e.target.checked)}
            />
          </label>
          <select
            className="bg-gray-100"
            value={monthOffset}
            onChange={(e) => setMonthOffset(Number.parseInt(e.target.value))}
          >
            <option value={-1}>Past month</option>
            <option value={-3}>Past 3 months</option>
            <option value={-6}>Past 6 months</option>
            <option value={-9}>Past 9 months</option>
            <option value={-12}>Past 12 months</option>
            <option value={-24}>Past 24 months</option>
            <option value={0}>All</option>
          </select>
        </div>
      </div>
      <Chart
        org={param.org}
        pipeline={param.pipeline}
        data={data}
        domain={domain}
        excludeWaitTime={excludeWaitTime}
      />
    </div>
  );
}

function JobStats({
  param,
  domain,
  excludeWaitTime,
}: {
  param: StatsParam;
  domain: number[] | undefined;
  excludeWaitTime: boolean;
}) {
  const stats = useBuildkiteJobStats(param.org, param.pipeline, {
    branch: param.branch,
    from: param.from,
  });

  const sortedGroup = useMemo(() => {
    if (stats.loading || stats.error) {
      return [];
    }

    const data = stats.data.items;
    var group = _.groupBy(data, (item) => item.bazelCITask);

    return _.map(
      _.sortBy(
        _.map(group, (data) => {
          const max = _.max(
            _.map(data, (item) =>
              excludeWaitTime ? item.runTime : item.waitTime + item.runTime
            )
          );
          return { sortKey: -(max || 0), data: data };
        }),
        (item) => item.sortKey
      ),
      (item) => item.data
    );
  }, [stats, excludeWaitTime]);

  if (stats.loading || stats.error || domain === undefined) {
    return <></>;
  }

  return (
    <>
      {_.map(sortedGroup, (data) => (
        <div
          key={data[0].bazelCITask}
          className="flex flex-col border shadow rounded bg-white ring-1 ring-black ring-opacity-5 flex-auto"
        >
          <div className="bg-gray-100 flex flex-row items-center border-b">
            <span className="px-4 py-2 text-base font-medium">
              {data[0].bazelCITask} | {data[0].name}
            </span>
          </div>
          <Chart
            org={param.org}
            pipeline={param.pipeline}
            data={data}
            domain={domain}
            excludeWaitTime={excludeWaitTime}
          />
        </div>
      ))}
    </>
  );
}

export default function Page() {
  const [domain, setDomain] = useState<number[]>();
  const [monthOffset, setMonthOffset] = useState<number>(-1);
  const [excludeWaitTime, setExcludeWaitTime] = useState<boolean>(true);

  const param = useMemo(() => {
    return {
      org: "bazel",
      pipeline: "bazel-bazel",
      branch: "master",
      from:
        monthOffset < 0
          ? DateTime.now().minus({ month: -monthOffset }).toISO()
          : DateTime.fromSeconds(0).toISO(),
    };
  }, [monthOffset]);

  return (
    <Layout>
      <div className="m-8 flex flex-col gap-8">
        <BuildStats
          param={param}
          domain={domain}
          setDomain={setDomain}
          monthOffset={monthOffset}
          setMonthOffset={(v) => {
            setDomain(undefined);
            setMonthOffset(v);
          }}
          excludeWaitTime={excludeWaitTime}
          setExcludeWaitTime={(v) => {
            setDomain(undefined);
            setExcludeWaitTime(v);
          }}
        />
        <JobStats
          param={param}
          domain={domain}
          excludeWaitTime={excludeWaitTime}
        />
      </div>
    </Layout>
  );
}
