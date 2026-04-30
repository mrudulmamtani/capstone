import { useMemo } from 'react';

const SVG_SIZE = 320;
const CENTER = SVG_SIZE / 2;
const ORBIT_RADIUS = 108;

function buildAssets(snapshot, steps, selectedStepId, affectedStepIds) {
  const state = snapshot?.state || {};
  const assetImpacts = state.assetImpacts || {};
  const affectedSet = new Set(affectedStepIds || []);
  const selectedStep = steps.find((step) => step.id === selectedStepId);
  const relevantSteps = selectedStepId
    ? steps.filter((step) => affectedSet.has(step.id))
    : steps.filter((step) => (state.currentStep ? state.completedSteps?.includes(step.id) || state.currentStep === step.id : true));

  const seen = new Set();
  const assets = [];

  for (const step of relevantSteps) {
    if (!step.asset || seen.has(step.asset)) {
      continue;
    }
    seen.add(step.asset);
    assets.push({
      name: step.asset,
      intensity: Number(assetImpacts[step.asset] || step.heat || 0.6),
      impacted: Boolean(selectedStepId ? affectedSet.has(step.id) : step.id === state.currentStep || state.completedSteps?.includes(step.id)),
      relatedToSelection: Boolean(selectedStep && (step.asset === selectedStep.asset || step.zoneId === selectedStep.zoneId || affectedSet.has(step.id))),
    });
  }

  return assets.sort((left, right) => right.intensity - left.intensity);
}

export default function AssetOrbit({ snapshot, steps = [], selectedStepId = null, affectedStepIds = [] }) {
  const assets = useMemo(() => buildAssets(snapshot, steps, selectedStepId, affectedStepIds), [affectedStepIds, selectedStepId, snapshot, steps]);

  return (
    <div className="card p-5 space-y-4">
      <div>
        <div className="text-sm text-ink-500">Asset field</div>
        <h2 className="text-lg font-semibold">Linked impacted assets</h2>
        <div className="text-xs text-ink-400 mt-1">
          {selectedStepId
            ? 'Showing assets affected by the selected node and its downstream path.'
            : 'Showing assets currently energized by the active simulation state.'}
        </div>
      </div>

      <div className="rounded-2xl border border-ink-100 bg-ink-950 px-4 py-5 text-white">
        <svg viewBox={`0 0 ${SVG_SIZE} ${SVG_SIZE}`} className="mx-auto h-[300px] w-full max-w-[300px]">
          <defs>
            <radialGradient id="orbit-core" cx="50%" cy="50%">
              <stop offset="0%" stopColor="#60a5fa" stopOpacity="0.85" />
              <stop offset="100%" stopColor="#0f172a" stopOpacity="0" />
            </radialGradient>
          </defs>

          <circle cx={CENTER} cy={CENTER} r={ORBIT_RADIUS} fill="none" stroke="rgba(148,163,184,0.35)" strokeWidth="1.5" strokeDasharray="4 8" />
          <circle cx={CENTER} cy={CENTER} r={48} fill="url(#orbit-core)" />
          <circle cx={CENTER} cy={CENTER} r={18} fill="#e2e8f0" />

          {assets.map((asset, index) => {
            const angle = (Math.PI * 2 * index) / Math.max(assets.length, 1);
            const x = CENTER + ORBIT_RADIUS * Math.cos(angle);
            const y = CENTER + ORBIT_RADIUS * Math.sin(angle);
            const radius = 10 + Math.min(16, asset.intensity * 5);
            const fill = asset.relatedToSelection ? '#f59e0b' : asset.impacted ? '#ef4444' : '#ffffff';
            const opacity = asset.relatedToSelection || asset.impacted ? 0.98 : 0.72;

            return (
              <g key={asset.name} transform={`translate(${x} ${y})`}>
                {(asset.relatedToSelection || asset.impacted) && (
                  <circle r={radius + 10} fill="none" stroke={asset.relatedToSelection ? '#f59e0b' : '#ef4444'} strokeWidth="2" opacity="0.35">
                    <animate attributeName="r" values={`${radius + 6};${radius + 16};${radius + 6}`} dur="1.8s" repeatCount="indefinite" />
                    <animate attributeName="opacity" values="0.35;0.08;0.35" dur="1.8s" repeatCount="indefinite" />
                  </circle>
                )}
                <circle r={radius} fill={fill} opacity={opacity} stroke="#0f172a" strokeWidth="3" />
                <text y={radius + 16} textAnchor="middle" fill="#e2e8f0" fontSize="11" fontWeight="600">
                  {asset.name}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
