import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { ChevronDown, ChevronUp, Eye, Workflow } from 'lucide-react';
import AssetOrbit from '../components/AssetOrbit.jsx';
import ApproachDiagram from '../components/ApproachDiagram.jsx';
import SOPBlueprint from '../components/SOPBlueprint.jsx';
import { useDemoRole } from '../components/DemoRoleProvider.jsx';
import SimulationControls from '../components/SimulationControls.jsx';
import SOPGraph from '../components/SOPGraph.jsx';
import SimulationScenarioPanel from '../components/SimulationScenarioPanel.jsx';
import { useSimulation } from '../hooks/useSimulation.js';
import { sopApi } from '../lib/api.js';
import { getAffectedStepIds } from '../lib/simulation/relations.js';

const MODES = [
  { value: 'flow', label: 'Flow Network', icon: Workflow },
  { value: 'blueprint', label: 'Blueprint Heatmap', icon: Eye },
];

export default function SOPDetail() {
  const { id } = useParams();
  const { role } = useDemoRole();
  const [sop, setSop] = useState(null);
  const [message, setMessage] = useState(null);
  const [mode, setMode] = useState('flow');
  const [selectedZone, setSelectedZone] = useState(null);
  const [selectedStepId, setSelectedStepId] = useState(null);
  const [showReference, setShowReference] = useState(false);

  const canPublish = role === 'admin' || role === 'engineer';

  useEffect(() => {
    sopApi.get(id).then(setSop);
  }, [id]);

  const {
    steps,
    profile,
    profiles,
    summary,
    impactControls,
    impacts,
    triggers,
    selectedProfileId,
    setSelectedProfileId,
    setImpact,
    setTrigger,
    snapshots,
    currentTick,
    currentSnapshot,
    isPlaying,
    play,
    pause,
    setTick,
  } = useSimulation(sop);

  const affectedStepIds = useMemo(() => getAffectedStepIds(steps, selectedStepId), [selectedStepId, steps]);
  const selectedStep = useMemo(() => steps.find((step) => step.id === selectedStepId) || null, [selectedStepId, steps]);
  const zoneLoads = useMemo(() => {
    return Object.entries(currentSnapshot?.state?.zoneLoads || {})
      .sort((left, right) => right[1] - left[1])
      .slice(0, 4);
  }, [currentSnapshot]);

  useEffect(() => {
    setSelectedZone(null);
    setSelectedStepId(null);
  }, [selectedProfileId]);

  if (!sop) return <div className="text-ink-400">Loading...</div>;

  async function publish() {
    try {
      setSop(await sopApi.publish(sop.id));
      setMessage('SOP published successfully.');
    } catch (error) {
      setMessage(error?.response?.data?.detail || 'Publish failed for this role.');
    }
  }

  return (
    <div className="space-y-6">
      <section className="rounded-[28px] bg-gradient-to-br from-slate-950 via-slate-900 to-sky-950 text-white overflow-hidden">
        <div className="px-6 py-7 xl:px-8 xl:py-8 space-y-6">
          <div className="flex flex-col gap-5 2xl:flex-row 2xl:items-end 2xl:justify-between">
            <div className="space-y-3 max-w-4xl">
              <div className="flex flex-wrap items-center gap-2 text-xs uppercase tracking-[0.2em] text-sky-200">
                <span>Review workspace</span>
                <span className="rounded-full border border-white/15 px-3 py-1 text-[11px] tracking-[0.18em] text-white/80">{sop.station}</span>
              </div>
              <h1 className="text-3xl xl:text-4xl font-semibold tracking-tight">{sop.title}</h1>
              <div className="text-sm xl:text-base text-slate-300 max-w-3xl">
                This page is now the live simulation workspace for your SOP: movable process network, physical blueprint heatmap, linked asset impact field, and the architecture story that explains how the digital twin is produced.
              </div>
              <div className="flex flex-wrap gap-2 items-center">
                <span className={`pill-${sop.status}`}>{sop.status}</span>
                <span className="badge bg-white/10 text-white">{summary?.totalSteps || 0} simulated steps</span>
                <span className="badge bg-sky-400/15 text-sky-100">{summary?.zones?.length || 0} zones</span>
                <span className="badge bg-amber-400/15 text-amber-100">{summary?.assets?.length || 0} assets</span>
                {summary?.type && <span className="badge bg-violet-400/15 text-violet-100">{summary.type}</span>}
                {sop.status !== 'published' && canPublish && (
                  <button onClick={publish} className="btn bg-white text-slate-950 hover:bg-slate-100">
                    Publish
                  </button>
                )}
              </div>
              {message && <div className="text-sm text-sky-100">{message}</div>}
            </div>

            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4 min-w-full 2xl:min-w-[720px]">
              <HeroStat label="Mode" value={mode === 'flow' ? 'Network' : 'Blueprint'} />
              <HeroStat label="Tick" value={`${currentTick}/${Math.max(0, snapshots.length - 1)}`} />
              <HeroStat label="Risk" value={currentSnapshot?.state?.riskScore ?? 0} />
              <HeroStat label="Selected" value={selectedStep ? selectedStep.title : 'None'} />
            </div>
          </div>

          <div className="grid 2xl:grid-cols-[minmax(0,1fr)_440px] gap-5 items-start">
            <div className="space-y-4">
              <div className="rounded-[24px] border border-white/10 bg-white/5 p-4 xl:p-5 space-y-4 backdrop-blur-sm">
                <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
                  <div>
                    <div className="text-xs uppercase tracking-[0.2em] text-slate-300">Simulation canvas</div>
                    <div className="text-lg font-semibold mt-1">{mode === 'flow' ? 'Grid-structured SOP network' : 'Live blueprint heatmap'}</div>
                    <div className="text-sm text-slate-300 mt-1">
                      The canvas is the primary review surface. Click nodes to reveal downstream impact, asset propagation, and zone heat concentration.
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {MODES.map((item) => {
                      const Icon = item.icon;
                      return (
                        <button
                          key={item.value}
                          type="button"
                          onClick={() => setMode(item.value)}
                          className={`inline-flex items-center gap-2 rounded-xl border px-4 py-2 text-sm font-medium transition ${
                            item.value === mode
                              ? 'border-white bg-white text-slate-950'
                              : 'border-white/15 bg-transparent text-white hover:border-white/40'
                          }`}
                        >
                          <Icon size={16} />
                          {item.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <SimulationControls
                  currentTick={currentTick}
                  maxTick={Math.max(0, snapshots.length - 1)}
                  onChange={setTick}
                  onPlay={play}
                  onPause={pause}
                  isPlaying={isPlaying}
                />

                {mode === 'flow' ? (
                  <SOPGraph
                    steps={steps}
                    snapshot={currentSnapshot}
                    storageKey={`${sop.id}:${selectedProfileId}:layout-v2`}
                    selectedZone={selectedZone}
                    selectedStepId={selectedStepId}
                    affectedStepIds={affectedStepIds}
                    onSelectZone={setSelectedZone}
                    onSelectStep={setSelectedStepId}
                  />
                ) : (
                  <SOPBlueprint
                    steps={steps}
                    snapshot={currentSnapshot}
                    profile={summary}
                    selectedZone={selectedZone}
                    selectedStepId={selectedStepId}
                    affectedStepIds={affectedStepIds}
                    onSelectZone={setSelectedZone}
                    onSelectStep={setSelectedStepId}
                  />
                )}
              </div>
            </div>

            <div className="space-y-4 2xl:sticky 2xl:top-5">
              <SimulationScenarioPanel
                profile={summary}
                profiles={profiles}
                selectedProfileId={selectedProfileId}
                onProfileChange={setSelectedProfileId}
                impactControls={impactControls}
                impacts={impacts}
                onImpactChange={setImpact}
                triggers={triggers}
                triggerDefinitions={summary?.triggers || []}
                onTriggerChange={setTrigger}
                selectedZone={selectedZone}
                onZoneSelect={setSelectedZone}
              />

              <div className="grid gap-4 xl:grid-cols-2 2xl:grid-cols-1">
                <AssetOrbit
                  snapshot={currentSnapshot}
                  steps={steps}
                  selectedStepId={selectedStepId}
                  affectedStepIds={affectedStepIds}
                />
                <div className="card p-5 space-y-4">
                  <div>
                    <div className="text-sm text-ink-500">Live review cues</div>
                    <h2 className="text-lg font-semibold">What this selection affects</h2>
                  </div>

                  {selectedStep ? (
                    <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 space-y-2">
                      <div className="text-sm font-semibold text-amber-950">{selectedStep.title}</div>
                      <div className="text-xs text-amber-800">
                        Zone: {selectedStep.zone} · Asset: {selectedStep.asset} · Connected steps: {affectedStepIds.length}
                      </div>
                    </div>
                  ) : (
                    <div className="rounded-2xl border border-ink-100 bg-ink-50 px-4 py-3 text-sm text-ink-500">
                      Click a node to spotlight downstream process impact, shared assets, and zone heat changes.
                    </div>
                  )}

                  <div className="space-y-2">
                    <div className="text-xs uppercase tracking-[0.18em] text-ink-400">Top hot zones</div>
                    {zoneLoads.length === 0 ? (
                      <div className="text-sm text-ink-400">Start playback to populate live zone heat.</div>
                    ) : (
                      zoneLoads.map(([zone, value]) => (
                        <div key={zone} className="space-y-1">
                          <div className="flex items-center justify-between text-sm">
                            <span>{zone}</span>
                            <span>{value.toFixed(2)}</span>
                          </div>
                          <div className="h-2 rounded-full bg-ink-100 overflow-hidden">
                            <div className="h-full rounded-full bg-red-500" style={{ width: `${Math.min(100, value * 12)}%` }} />
                          </div>
                        </div>
                      ))
                    )}
                  </div>

                  <div className="space-y-2">
                    <div className="text-xs uppercase tracking-[0.18em] text-ink-400">Step list</div>
                    <ol className="space-y-2 max-h-[280px] overflow-y-auto pr-1">
                      {steps
                        .filter((step) => !selectedZone || step.zoneId === selectedZone)
                        .map((step) => {
                          const isActive = currentSnapshot?.state?.currentStep === step.id;
                          const isAffected = affectedStepIds.includes(step.id);
                          return (
                            <li
                              key={step.id}
                              className={`rounded-2xl border px-3 py-3 transition ${
                                isActive
                                  ? 'border-sky-200 bg-sky-50'
                                  : isAffected
                                    ? 'border-amber-200 bg-amber-50'
                                    : 'border-ink-100 bg-white'
                              }`}
                            >
                              <button type="button" onClick={() => setSelectedStepId(step.id === selectedStepId ? null : step.id)} className="w-full text-left">
                                <div className="text-sm font-medium">{(step.step_index ?? 0) + 1}. {step.title}</div>
                                <div className="mt-1 text-xs text-ink-500">
                                  {step.zone} · {step.asset} · {step.target_duration_s.toFixed(1)}s ±{step.tolerance_s.toFixed(1)}s
                                </div>
                              </button>
                            </li>
                          );
                        })}
                    </ol>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <ApproachDiagram />

      <section className="card p-5 space-y-4">
        <button
          type="button"
          onClick={() => setShowReference((value) => !value)}
          className="w-full flex items-center justify-between gap-4 text-left"
        >
          <div>
            <div className="text-sm text-ink-500">Procedure reference</div>
            <h2 className="text-xl font-semibold">Original SOP markdown</h2>
            <div className="text-sm text-ink-500 mt-1">Kept intact for review, but moved below the simulation workspace so the digital twin leads the story.</div>
          </div>
          {showReference ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </button>

        {showReference && (
          <div className="prose max-w-none rounded-2xl border border-ink-100 bg-white p-5">
            {sop.rendered_markdown ? (
              <ReactMarkdown>{sop.rendered_markdown}</ReactMarkdown>
            ) : (
              <div className="text-ink-400">No rendered markdown - SOP is empty.</div>
            )}
          </div>
        )}
      </section>
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


