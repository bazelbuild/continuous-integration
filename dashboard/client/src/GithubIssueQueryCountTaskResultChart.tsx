import { useGithubIssueQueryCountTaskResult } from "./data/GithubIssueQueryCountTask";
import {
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { DateTime } from "luxon";

export interface GithubIssueQueryCountTaskResultChartProps {
  queryIds: Array<string>;
  days: number
}

export default function GithubIssueQueryCountTaskResultChart({
  queryIds,
  days,
}: GithubIssueQueryCountTaskResultChartProps) {
  const { data, loading, error } = useGithubIssueQueryCountTaskResult(
    "bazelbuild",
    "bazel",
    queryIds,
    "DAILY",
    days
  );
  if (loading) {
    return <span>Loading</span>;
  }
  if (error) {
    return <span>Error</span>;
  }

  return (
    <ResponsiveContainer height={300}>
      <LineChart margin={{ left: -20 }}>
        {data.map((result) => {
          return (
            <Line
              connectNulls
              key={result.id}
              type="monotone"
              isAnimationActive={false}
              dot={false}
              data={result.items}
              dataKey="count"
              name={result.name}
              activeDot={{
                onClick: () => {
                  window.open(result.url, "_blank");
                },
              }}
            />
          );
        })}
        <XAxis
          dataKey={(data) => {
            return DateTime.fromISO(data.timestamp).toFormat("MM-dd");
          }}
        />
        <YAxis />
        <Tooltip />
        {data.length > 1 && <Legend />}
      </LineChart>
    </ResponsiveContainer>
  );
}
