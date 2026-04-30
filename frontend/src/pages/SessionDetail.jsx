import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Activity, AlertTriangle, Flame, StretchHorizontal } from 'lucide-react';
import { alertApi, analyticsApi, sessionApi, sopApi } from '../lib/api.js';
import { assetUrlFromSourceUri, findDemoAssetByServerPath, heatmapUrlFromSourceUri } from '../lib/demoAssets.js';
import SeverityPill from '../components/SeverityPill.jsx';
import BlueprintHeatmapFigure from '../components/BlueprintHeatmapFigure.jsx';
import ApproachDiagram from '../components/ApproachDiagram.jsx';
import { useSimulation } from '../hooks/useSimulation.js';
import { buildSessionSimulationPreset } from '../lib/simulation/scenario.js';
import { getAffectedStepIds } from '../lib/simulation/relations.js';

export default function SessionDetail() {
  const { id } = useParams();
  const [session, setSession] = useState(null);
  const [sop, setSop] = useState(null);
  const [summary, setSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [muda, setMuda] = useState(null);
  const [ergonomics, setErgonomics] = useState(null);
  const [selectedZone, setSelectedZone] = useState(null);
  const [selectedStepId, setSelectedStepId] = useState(null);

  useEffect(() => {
    sessionApi.get(id).then((result) => {
      setSession(result);
      if (result?.sop_id) {
        sopApi.get(result.sop_id).then(setSop).catch(() => {});
      }
    });
    sessionApi.summary(id).then(setSummary).catch(() => {});
    alertApi.list({ session_id: id }).then(setAlerts);
    analyticsApi.muda(id).then(setMuda).catch(() => {});
    analyticsApi.ergonomics(id).then(setErgonomics).catch(() => {});
  }, [id]);

  const preset = useMemo(() => buildSessionSimulationPreset(session, summary, alerts, ergonomics, muda), [alerts, ergonomics, muda, session, summary]);
  const { steps, summary: scenarioSummary, currentSnapshot } = useSimulation(sop, {
    impacts: preset.impacts,
    triggers: preset.triggers,
    disablePlayback: true,
    defaultTick: 'last',
  });
  const affectedStepIds = useMemo(() => getAffectedStepIds(steps, selectedStepId), [selectedStepId, steps]);
  const selectedStep = useMemo(() => steps.find((step) => step.id === selectedStepId) || null, [selectedStepId, steps]);

  const demoAsset = useMemo(() => findDemoAssetByServerPath(session?.source_uri), [session]);
  const videoUrl = session ? assetUrlFromSourceUri(session.source_uri) : '';
  const fallbackHeatmapUrl = demoAsset?.heatmapUrl || (session ? heatmapUrlFromSourceUri(session.source_uri) : '');

  if (!session) return <div className="text-ink-400">Loading...</div>;

  return (
    <div className="space-y-6">
      <section className="rounded-[28px] bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 text-white overflow-hidden">
        <div className="px-6 py-7 xl:px-8 xl:py-8 space-y-6">
          <div className="flex flex-col gap-5 2xl:flex-row 2xl:items-end 2xl:justify-between">
            <div className="space-y-3 max-w-4xl">
              <div className="text-xs uppercase tracking-[0.2em] text-emerald-200">Session review workspace</div>
              <h1 className="text-3xl xl:text-4xl font-semibold tracking-tight">Recorded run vs. blueprint twin</h1>
              <div className="text-sm xl:text-base text-slate-300 max-w-3xl">
                This review surface merges the recorded operator session, SOP-linked blueprint simulation, ergonomic indicators, and quality/alert findings into one presentation story.
              </div>
              <div className="flex flex-wrap gap-2 items-center">
                <span className={`badge ${session.status === 'completed' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}>
                  {session.status}
                </span>
                <span className="badge bg-white/10 text-white">{demoAsset?.title || 'Recorded run'}</span>
                {scenarioSummary?.label && <span className="badge bg-sky-400/15 text-sky-100">{scenarioSummary.label}</span>}
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4 min-w-full 2xl:min-w-[720px]">
              <HeroStat label="Cycle time" value={`${(session.cycle_time_s || 0).toFixed(1)}s`} />
              <HeroStat label="Deviation" value={`${((session.deviation_score || 0) * 100).toFixed(1)}%`} />
              <HeroStat label="Matched steps" value={summary?.matched_steps ?? '-'} />
              <HeroStat label="Ergo score" value={ergonomics?.score ?? '-'} />
            </div>
          </div>

          <div className="grid 2xl:grid-cols-[1.05fr_1fr] gap-5 items-start">
            <div className="rounded-[24px] border border-white/10 bg-white/5 p-5 space-y-4 backdrop-blur-sm">
              <div>
                <div className="text-xs uppercase tracking-[0.2em] text-slate-300">Observed evidence</div>
                <div className="text-lg font-semibold mt-1">Recorded operator run</div>
              </div>
              <video className="w-full rounded-2xl bg-ink-900 border border-white/10" src={videoUrl} controls />
              <div className="grid sm:grid-cols-3 gap-3 text-sm">
                <MiniStat label="Source" value={session.source_uri.split(/[\\/]/).pop() || session.source_uri} />
                <MiniStat label="Operator" value={session.operator_ref || '-'} />
                <MiniStat label="Alerts" value={alerts.length} />
              </div>
            </div>

            <div className="rounded-[24px] border border-white/10 bg-white/5 p-5 space-y-4 backdrop-blur-sm">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="text-xs uppercase tracking-[0.2em] text-slate-300">Spatial analytics</div>
                  <div className="text-lg font-semibold mt-1">Blueprint ergonomic heatmap</div>
                  <div className="text-sm text-slate-300 mt-1">
                    The session summary drives a SOP-linked blueprint heatmap instead of a disconnected static PNG.
                  </div>
                </div>
                {selectedStep && (
                  <div className="rounded-xl bg-white/10 px-3 py-2 text-xs text-white">
                    Focus: {selectedStep.title}
                  </div>
                )}
              </div>

              {scenarioSummary ? (
                <div className="overflow-hidden rounded-2xl border border-white/10 bg-[#0f172a]">
                  <BlueprintHeatmapFigure
                    steps={steps}
                    snapshot={currentSnapshot}
                    profile={scenarioSummary}
                    selectedZone={selectedZone}
                    selectedStepId={selectedStepId}
                    affectedStepIds={affectedStepIds}
                    onSelectZone={setSelectedZone}
                    onSelectStep={setSelectedStepId}
                    height={560}
                  />
                </div>
              ) : (
                <img src={fallbackHeatmapUrl} alt="Ergonomic heatmap" className="w-full rounded-2xl border border-white/10 bg-ink-50" />
              )}
            </div>
          </div>
        </div>
      </section>

      <div className="grid xl:grid-cols-[1.1fr_0.9fr] gap-4">
        <div className="card p-5 space-y-4">
          <div className="flex items-center justify-between gap-4">
            <div>
              <div className="text-sm text-ink-500">Golden batch comparison</div>
              <h2 className="text-xl font-semibold">Run outcome summary</h2>
            </div>
            {summary && <div className="badge bg-ink-100 text-ink-700">Total steps {summary.total_steps}</div>}
          </div>

          {summary ? (
            <div className="grid md:grid-cols-4 gap-4 text-sm">
              <KV k="Matched" v={summary.matched_steps} />
              <KV k="Skipped" v={summary.skipped_steps.join(', ') || '-'} />
              <KV k="Extra" v={summary.extra_steps.join(', ') || '-'} />
              <KV k="Selected impact" v={selectedStep ? `${affectedStepIds.length} linked steps` : 'Click heatmap node'} />
            </div>
          ) : (
            <div className="text-ink-400">Loading comparison...</div>
          )}

          <div className="space-y-2">
            {steps.slice(0, 8).map((step) => {
              const isAffected = affectedStepIds.includes(step.id);
              return (
                <button
                  key={step.id}
                  type="button"
                  onClick={() => setSelectedStepId(step.id === selectedStepId ? null : step.id)}
                  className={`w-full rounded-2xl border px-4 py-3 text-left transition ${
                    isAffected ? 'border-amber-200 bg-amber-50' : 'border-ink-100 bg-white hover:border-ink-300'
                  }`}
                >
                  <div className="font-medium text-sm">{step.title}</div>
                  <div className="text-xs text-ink-500 mt-1">{step.zone} · {step.asset}</div>
                </button>
              );
            })}
          </div>
        </div>

        <div className="space-y-4">
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
                  <div className="text-xs text-ink-400 mt-1">at {alert.at_s.toFixed(1)}s · rule {alert.rule}</div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div className="grid xl:grid-cols-[1fr_1fr] gap-4">
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

        <ApproachDiagram />
      </div>
    </div>
  );
}

function HeroStat({ label, value }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
      <div className="text-xs uppercase tracking-[0.18em] text-slate-300">{label}</div>
      <div className="text-lg font-semibold mt-1 break-words">{value}</div>
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
