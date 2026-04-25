import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { Activity, AlertTriangle, Flame, StretchHorizontal } from "lucide-react";
import { alertApi, analyticsApi, sessionApi } from "../lib/api.js";
import { assetUrlFromSourceUri, findDemoAssetByServerPath, heatmapUrlFromSourceUri } from "../lib/demoAssets.js";
import SeverityPill from "../components/SeverityPill.jsx";

export default function SessionDetail() {
  const { id } = useParams();
  const [session, setSession] = useState(null);
  const [summary, setSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [muda, setMuda] = useState(null);
  const [ergonomics, setErgonomics] = useState(null);

  useEffect(() => {
    sessionApi.get(id).then(setSession);
    sessionApi.summary(id).then(setSummary).catch(() => {});
    alertApi.list({ session_id: id }).then(setAlerts);
    analyticsApi.muda(id).then(setMuda).catch(() => {});
    analyticsApi.ergonomics(id).then(setErgonomics).catch(() => {});
  }, [id]);

  const demoAsset = useMemo(() => findDemoAssetByServerPath(session?.source_uri), [session]);
  const videoUrl = session ? assetUrlFromSourceUri(session.source_uri) : "";
  const heatmapUrl = demoAsset?.heatmapUrl || (session ? heatmapUrlFromSourceUri(session.source_uri) : "");

  if (!session) return <div className="text-ink-400">Loading...</div>;

  return (
    <div className="space-y-6">
      <header className="flex items-start gap-4">
        <div>
          <div className="text-xs text-ink-500 font-mono">{session.id}</div>
          <h1 className="text-2xl">Session analysis</h1>
          <div className="text-sm text-ink-500 mt-1">
            {demoAsset?.title || "Recorded run"} · {session.status}
          </div>
        </div>
        <span className={`ml-auto badge ${session.status === "completed" ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`}>
          {session.status}
        </span>
      </header>

      <div className="grid md:grid-cols-4 gap-4">
        <Stat label="Cycle time" value={`${(session.cycle_time_s || 0).toFixed(1)}s`} icon={Activity} />
        <Stat label="Deviation" value={`${((session.deviation_score || 0) * 100).toFixed(1)}%`} icon={AlertTriangle} />
        <Stat label="Matched steps" value={summary?.matched_steps ?? "-"} icon={StretchHorizontal} />
        <Stat label="Ergo score" value={ergonomics?.score ?? "-"} icon={Flame} />
      </div>

      <div className="grid xl:grid-cols-[1.2fr_1fr] gap-4">
        <div className="card p-5 space-y-4">
          <div>
            <h2 className="text-lg">Observed run</h2>
            <div className="text-sm text-ink-500">Use this clip during the demo while discussing deviations and station redesign.</div>
          </div>
          <video className="w-full rounded-xl bg-ink-900" src={videoUrl} controls />
          <div className="grid sm:grid-cols-3 gap-3 text-sm">
            <MiniStat label="Source" value={session.source_uri.split(/[\\/]/).pop() || session.source_uri} />
            <MiniStat label="Operator" value={session.operator_ref || "-"} />
            <MiniStat label="Alerts" value={alerts.length} />
          </div>
        </div>

        <div className="card p-5 space-y-4">
          <div>
            <h2 className="text-lg">Ergonomic heatmap</h2>
            <div className="text-sm text-ink-500">Movement density and high-reach concentration for this run.</div>
          </div>
          <img
            src={heatmapUrl}
            alt="Ergonomic heatmap"
            className="w-full rounded-xl border border-ink-100 bg-ink-50"
          />
          {ergonomics && (
            <div className="grid grid-cols-3 gap-3 text-center">
              <MiniStat label="Score" value={ergonomics.score} />
              <MiniStat label="Shoulder" value={`${ergonomics.mean_shoulder_abduction_deg}°`} />
              <MiniStat label="Reach P95" value={ergonomics.reach_percentile_95} />
            </div>
          )}
        </div>
      </div>

      <div className="grid xl:grid-cols-3 gap-4">
        <div className="card p-5 xl:col-span-2">
          <h2 className="text-lg mb-3">Golden Batch comparison</h2>
          {summary ? (
            <div className="grid md:grid-cols-4 gap-4 text-sm">
              <KV k="Total steps" v={summary.total_steps} />
              <KV k="Matched" v={summary.matched_steps} />
              <KV k="Skipped" v={summary.skipped_steps.join(", ") || "-"} />
              <KV k="Extra" v={summary.extra_steps.join(", ") || "-"} />
            </div>
          ) : (
            <div className="text-ink-400">Loading comparison...</div>
          )}
        </div>

        <div className="card p-5">
          <h2 className="text-lg mb-3">Muda findings</h2>
          {!muda && <div className="text-ink-400">Loading...</div>}
          {muda && (
            <>
              <div className="grid grid-cols-3 gap-3 text-center mb-4">
                <MiniStat label="Idle" value={`${Math.round(muda.idle_fraction * 100)}%`} />
                <MiniStat label="Move" value={`${Math.round(muda.move_fraction * 100)}%`} />
                <MiniStat label="Over-proc." value={muda.overprocess_steps} />
              </div>
              <ul className="space-y-2 text-sm">
                {muda.findings.map((finding, index) => (
                  <li key={index}>
                    <span className={`sev-${finding.severity} mr-2`}>{finding.category}</span>
                    {finding.message}
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      </div>

      <div className="grid xl:grid-cols-2 gap-4">
        <div className="card p-5">
          <h2 className="text-lg mb-3">Ergonomic recommendations</h2>
          {!ergonomics && <div className="text-ink-400">Loading ergonomic analysis...</div>}
          {ergonomics && (
            <div className="space-y-3">
              {(ergonomics.hotspots || []).map((hotspot, index) => (
                <div key={index} className="rounded-lg bg-ink-50 p-3">
                  <div className="text-xs uppercase tracking-wide text-ink-500">{hotspot.area}</div>
                  <div className="text-sm text-ink-700 mt-1">{hotspot.message}</div>
                </div>
              ))}
              <ul className="space-y-2 text-sm text-ink-700">
                {(ergonomics.recommendations || []).map((item, index) => (
                  <li key={index}>• {item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="card p-5">
          <h2 className="text-lg mb-3">Alerts</h2>
          {alerts.length === 0 && <div className="text-ink-400">No alerts raised.</div>}
          <ul className="space-y-3">
            {alerts.map((alert) => (
              <li key={alert.id} className="border-b border-ink-100 pb-3 last:border-0">
                <div className="flex items-center gap-2">
                  <SeverityPill severity={alert.severity} />
                  <div className="font-medium">{alert.title}</div>
                </div>
                <div className="text-sm text-ink-600 mt-1">{alert.message}</div>
                <div className="text-xs text-ink-400 mt-1">
                  at {alert.at_s.toFixed(1)}s · rule {alert.rule}
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, icon: Icon }) {
  return (
    <div className="card p-4">
      <div className="flex items-center gap-2 text-xs text-ink-500">
        <Icon size={14} />
        {label}
      </div>
      <div className="text-2xl font-bold mt-2">{value}</div>
    </div>
  );
}

function MiniStat({ label, value }) {
  return (
    <div className="bg-ink-50 rounded-lg p-3">
      <div className="text-xs text-ink-500">{label}</div>
      <div className="text-xl font-bold break-words">{value}</div>
    </div>
  );
}

function KV({ k, v }) {
  return (
    <div>
      <div className="text-xs text-ink-500">{k}</div>
      <div className="font-medium">{v}</div>
    </div>
  );
}
