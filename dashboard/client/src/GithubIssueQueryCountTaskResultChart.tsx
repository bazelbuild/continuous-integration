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
}

export default function GithubIssueQueryCountTaskResultChart({
  queryIds,
}: GithubIssueQueryCountTaskResultChartProps) {
  const { data, loading, error } = useGithubIssueQueryCountTaskResult(
    "bazelbuild",
    "bazel",
    queryIds,
    "DAILY"
  );
  if (loading) {
    return <span>loading</span>;
  }
  if (error) {
    return <span>error</span>;
  }

  return (
    <ResponsiveContainer height={300}>
      <LineChart margin={{ left: -20 }}>
        {data.map((result) => {
          return (
            <Line
              key={result.id}
              type="monotone"
              data={result.items}
              dataKey="count"
              name={result.name}
            />
          );
        })}
        <XAxis
          dataKey={(data) => {
            return DateTime.fromISO(data.timestamp).toFormat("MM-dd");
          }}
        />
        <YAxis  />
        <Tooltip />
        {data.length > 1 && <Legend />}
      </LineChart>
    </ResponsiveContainer>
  );
}
