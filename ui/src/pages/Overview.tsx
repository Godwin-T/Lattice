import { Activity, DollarSign, Timer, TrendingUp } from "lucide-react";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useOverview } from "../api/hooks";
import StatCard from "../components/StatCard";

export default function Overview() {
  const { data, isLoading } = useOverview();

  if (isLoading || !data) {
    return <div>Loading overview...</div>;
  }

  return (
    <div className="space-y-8">
      <div className="grid gap-4 md:grid-cols-4">
        <StatCard title="Total Requests" value={data.total_requests.toLocaleString()} icon={<Activity size={18} />} />
        <StatCard title="Success Rate" value={`${data.success_rate.toFixed(1)}%`} icon={<TrendingUp size={18} />} />
        <StatCard title="Total Cost" value={`$${data.total_cost_usd.toFixed(2)}`} icon={<DollarSign size={18} />} />
        <StatCard title="Avg Latency" value={`${data.avg_latency_ms.toFixed(0)} ms`} icon={<Timer size={18} />} />
      </div>

      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-2)] p-6">
        <div className="mb-4 text-sm font-semibold">Request Trend (7 days)</div>
        <div style={{ width: "100%", height: 240 }}>
          <ResponsiveContainer>
            <LineChart data={data.trend}>
              <XAxis dataKey="date" tick={{ fill: "var(--muted)", fontSize: 12 }} />
              <YAxis tick={{ fill: "var(--muted)", fontSize: 12 }} />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="var(--primary)" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
