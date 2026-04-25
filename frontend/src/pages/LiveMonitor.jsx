import { useMemo } from "react";
import { useParams } from "react-router-dom";
import { Activity } from "lucide-react";
import { useLiveSession } from "../hooks/useLiveSession.js";
import SeverityPill from "../components/SeverityPill.jsx";

export default function LiveMonitor() {
  const { id } = useParams();
  const { events, status } = useLiveSession(id);

  const scores = useMemo(
    () => events.filter((e) => e.kind === "score").slice(-40),
    [events]
  );
  const alerts = useMemo(() => events.filter((e) => e.kind === "alert"), [events]);

  return (
    <div className="space-y-6">
      <header className="flex items-center gap-3">
        <Activity className="text-accent" />
        <div>
          <div className="text-xs text-ink-500 font-mono">{id}</div>
          <h1 className="text-2xl">Live monitor</h1>
        </div>
        <span className={`ml-auto badge ${status === "connected" ? "bg-emerald-100 text-emerald-800" : "bg-ink-100 text-ink-500"}`}>
          {status}
        </span>
      </header>

      <div className="grid lg:grid-cols-3 gap-4">
        <div className="card p-5 lg:col-span-2">
          <h2 className="text-lg mb-3">Action stream</h2>
          <div className="grid grid-cols-10 gap-1">
            {scores.map((s, i) => (
              <div
                key={i}
                title={`${s.label} · ${(s.confidence * 100).toFixed(0)}%`}
                className="h-10 rounded"
                style={{ background: colourFor(s.label), opacity: 0.4 + s.confidence * 0.6 }}
              />
            ))}
            {scores.length === 0 && (
              <div className="col-span-10 text-ink-400 text-sm py-6 text-center">
                Waiting for frames…
              </div>
            )}
          </div>
          <Legend />
        </div>

        <div className="card p-5">
          <h2 className="text-lg mb-3">Alerts</h2>
          <ul className="space-y-3 max-h-[400px] overflow-y-auto">
            {alerts.length === 0 && <div className="text-ink-400 text-sm">No alerts.</div>}
            {alerts
              .slice()
              .reverse()
              .map((a, i) => (
                <li key={i} className="border-b border-ink-100 pb-2 last:border-0">
                  <div className="flex items-center gap-2">
                    <SeverityPill severity={a.severity} />
                    <div className="font-medium text-sm">{a.title}</div>
                  </div>
                  <div className="text-xs text-ink-600 mt-1">{a.message}</div>
                </li>
              ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

const LABEL_COLORS = {
  idle: "#cbd5e1",
  reach: "#60a5fa",
  pick: "#818cf8",
  place: "#a78bfa",
  screw: "#f59e0b",
  inspect: "#10b981",
  move: "#ef4444",
};

function colourFor(label) {
  return LABEL_COLORS[label] || "#475569";
}

function Legend() {
  return (
    <div className="mt-3 flex flex-wrap gap-3 text-xs">
      {Object.entries(LABEL_COLORS).map(([label, col]) => (
        <div key={label} className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded" style={{ background: col }} />
          {label}
        </div>
      ))}
    </div>
  );
}
