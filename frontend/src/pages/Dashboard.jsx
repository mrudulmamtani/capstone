import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import StatCard from "../components/StatCard.jsx";
import { heatmapUrlFromSourceUri } from "../lib/demoAssets.js";
import { alertApi, sessionApi, sopApi } from "../lib/api.js";

const SEV_COLORS = { info: "#0ea5e9", warning: "#f59e0b", critical: "#ef4444" };

export default function Dashboard() {
  const [sops, setSops] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    Promise.all([sopApi.list(), sessionApi.list(), alertApi.list({ limit: 100 })])
      .then(([sopRows, sessionRows, alertRows]) => {
        setSops(sopRows);
        setSessions(sessionRows);
        setAlerts(alertRows);
      })
      .catch(() => {});
  }, []);

  const stats = useMemo(() => {
    const published = sops.filter((sop) => sop.status === "published").length;
    const completed = sessions.filter((session) => session.status === "completed");
    const avgCycle =
      completed.reduce((total, session) => total + (session.cycle_time_s || 0), 0) /
      Math.max(1, completed.length);
    const avgDeviation =
      completed.reduce((total, session) => total + (session.deviation_score || 0), 0) /
      Math.max(1, completed.length);

    return {
      sopTotal: sops.length,
      sopPublished: published,
      sessionTotal: sessions.length,
      avgCycle: avgCycle.toFixed(1),
      avgDeviation: (avgDeviation * 100).toFixed(1),
      alertsOpen: alerts.filter((alert) => !alert.acknowledged).length,
    };
  }, [sops, sessions, alerts]);

  const sevData = useMemo(() => {
    const bucket = { info: 0, warning: 0, critical: 0 };
    alerts.forEach((alert) => {
      bucket[alert.severity] = (bucket[alert.severity] || 0) + 1;
    });
    return Object.entries(bucket).map(([name, value]) => ({ name, value }));
  }, [alerts]);

  const cycleData = useMemo(
    () =>
      sessions
        .filter((session) => session.cycle_time_s)
        .slice(0, 12)
        .reverse()
        .map((session, index) => ({
          name: `#${index + 1}`,
          cycle: Number(session.cycle_time_s.toFixed(1)),
          deviation: Number(((session.deviation_score || 0) * 100).toFixed(1)),
        })),
    [sessions]
  );

  return (
    <div className="space-y-6">
      <header>
        <div className="text-sm text-ink-500">Overview</div>
        <h1 className="text-2xl">Computer vision SOP demo</h1>
        <div className="text-sm text-ink-500 mt-1">
          Show the committee the full story: demo videos, generated SOPs, Golden-Batch comparison, alerts, and ergonomic heatmaps.
        </div>
      </header>

      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard label="SOPs total" value={stats.sopTotal} />
        <StatCard label="Published" value={stats.sopPublished} hint="golden batch ready" />
        <StatCard label="Sessions" value={stats.sessionTotal} hint="demo runs" />
        <StatCard label="Avg. cycle (s)" value={stats.avgCycle} />
        <StatCard label="Avg. deviation" value={`${stats.avgDeviation}%`} accent />
        <StatCard label="Open alerts" value={stats.alertsOpen} />
      </div>

      <div className="grid xl:grid-cols-3 gap-4">
        <Link to="/sops" className="card p-5 hover:shadow-md transition">
          <div className="text-xs text-ink-500">Phase 1</div>
          <div className="text-lg font-semibold mt-1">Generate SOPs from demo videos</div>
          <div className="text-sm text-ink-600 mt-2">
            Pick a built-in video, run the pipeline, and show the generated markdown SOP with target timings.
          </div>
        </Link>
        <Link to="/sessions" className="card p-5 hover:shadow-md transition">
          <div className="text-xs text-ink-500">Phase 2</div>
          <div className="text-lg font-semibold mt-1">Open heatmaps and ergonomic findings</div>
          <div className="text-sm text-ink-600 mt-2">
            Session pages now surface the run video, ergonomic heatmap, posture score, and layout recommendations.
          </div>
        </Link>
        <Link to="/alerts" className="card p-5 hover:shadow-md transition">
          <div className="text-xs text-ink-500">Phase 3</div>
          <div className="text-lg font-semibold mt-1">Show deviations and supervisor alerts</div>
          <div className="text-sm text-ink-600 mt-2">
            Highlight skipped steps, delay alerts, and motion-waste findings from the preloaded demo runs.
          </div>
        </Link>
      </div>

      <div className="grid lg:grid-cols-3 gap-4">
        <div className="card p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg">Cycle time & deviation — recent sessions</h2>
            <div className="text-xs text-ink-400">blue = cycle (s) · orange = deviation (%)</div>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={cycleData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" />
              <YAxis yAxisId="l" />
              <YAxis yAxisId="r" orientation="right" />
              <Tooltip />
              <Legend />
              <Bar yAxisId="l" dataKey="cycle" fill="#14203a" radius={[4, 4, 0, 0]} />
              <Bar yAxisId="r" dataKey="deviation" fill="#ff6b35" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-5">
          <h2 className="text-lg mb-3">Alerts by severity</h2>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={sevData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={90} paddingAngle={3}>
                {sevData.map((datum, index) => (
                  <Cell key={index} fill={SEV_COLORS[datum.name]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid xl:grid-cols-2 gap-4">
        {sessions.slice(0, 2).map((session) => (
          <Link key={session.id} to={`/sessions/${session.id}`} className="card p-5 hover:shadow-md transition">
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="text-xs text-ink-500 font-mono">{session.id.slice(0, 8)}...</div>
                <div className="text-lg font-semibold">Heatmap preview</div>
              </div>
              <div className="badge bg-ink-100 text-ink-700">{session.status}</div>
            </div>
            <img src={heatmapUrlFromSourceUri(session.source_uri)} alt="heatmap preview" className="w-full rounded-xl border border-ink-100 bg-ink-50" />
            <div className="grid grid-cols-3 gap-3 mt-4 text-sm">
              <div>
                <div className="text-xs text-ink-500">Operator</div>
                <div className="font-medium">{session.operator_ref || "-"}</div>
              </div>
              <div>
                <div className="text-xs text-ink-500">Cycle</div>
                <div className="font-medium">{session.cycle_time_s?.toFixed(1) || "-"}s</div>
              </div>
              <div>
                <div className="text-xs text-ink-500">Deviation</div>
                <div className="font-medium">{((session.deviation_score || 0) * 100).toFixed(1)}%</div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
