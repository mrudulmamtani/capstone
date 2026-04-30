import BlueprintHeatmapFigure from './BlueprintHeatmapFigure.jsx';

export default function SOPBlueprint({
  steps = [],
  snapshot = null,
  profile = null,
  selectedZone = null,
  selectedStepId = null,
  affectedStepIds = [],
  onSelectZone,
  onSelectStep,
}) {
  const state = snapshot?.state || {};
  const selectedZoneMeta = profile?.zones?.find((zone) => zone.id === selectedZone) || null;
  const hottestZones = Object.entries(state.zoneLoads || {})
    .sort((left, right) => right[1] - left[1])
    .slice(0, 3);

  return (
    <div className="card p-5 space-y-4">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <div className="text-sm text-ink-500">Blueprint mode</div>
          <h2 className="text-lg font-semibold">Continuous physical heatmap</h2>
          <div className="mt-1 text-xs text-ink-400">
            The saved blueprint image is the base layer, with contour and heat overlays changing in realtime from triggers, impacts, and simulated step execution.
          </div>
        </div>
        <div className="flex flex-wrap gap-2 text-xs">
          {hottestZones.map(([zoneLabel, value]) => (
            <span key={zoneLabel} className="badge bg-red-100 text-red-700 px-3 py-1.5 rounded-full">
              {zoneLabel}: {value.toFixed(2)}
            </span>
          ))}
          <span className="badge bg-ink-100 text-ink-700 px-3 py-1.5 rounded-full">
            {state.currentStep ? `Active: ${state.currentStep}` : 'Idle'}
          </span>
        </div>
      </div>

      {selectedZoneMeta && (
        <div className="rounded-2xl border border-sky-100 bg-sky-50 px-4 py-3 text-sm text-sky-800">
          Filtering on <strong>{selectedZoneMeta.label}</strong>. Click the zone or node again to clear the focus.
        </div>
      )}

      <div className="overflow-hidden rounded-2xl border border-ink-100 bg-[#0f172a]">
        <BlueprintHeatmapFigure
          steps={steps}
          snapshot={snapshot}
          profile={profile}
          selectedZone={selectedZone}
          selectedStepId={selectedStepId}
          affectedStepIds={affectedStepIds}
          onSelectZone={onSelectZone}
          onSelectStep={onSelectStep}
          height={760}
        />
      </div>
    </div>
  );
}
