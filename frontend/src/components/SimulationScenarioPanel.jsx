import clsx from 'clsx';

export default function SimulationScenarioPanel({
  profile,
  profiles = [],
  selectedProfileId,
  onProfileChange,
  impactControls = [],
  impacts = {},
  onImpactChange,
  triggers = {},
  triggerDefinitions = [],
  onTriggerChange,
  selectedZone = null,
  onZoneSelect,
}) {
  if (!profile) {
    return null;
  }

  return (
    <div className="card p-5 space-y-5">
      <div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <div className="text-sm text-ink-500">Scenario profile</div>
          <h2 className="text-xl font-semibold">{profile.label}</h2>
          <div className="mt-2 text-sm text-ink-500 max-w-3xl">{profile.description}</div>
        </div>
        <label className="space-y-1 text-sm text-ink-500 min-w-[240px]">
          <span className="block">Blueprint context</span>
          <select
            value={selectedProfileId || profile.id}
            onChange={(event) => onProfileChange?.(event.target.value)}
            className="w-full rounded-xl border border-ink-200 bg-white px-3 py-2 text-sm text-ink-900 outline-none focus:border-ink-400"
          >
            {profiles.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-4">
          <div>
            <div className="text-xs uppercase tracking-[0.18em] text-ink-400">Blueprint analysis</div>
            <div className="mt-3 grid gap-2">
              {profile.analysis?.map((item) => (
                <div key={item} className="rounded-2xl border border-ink-100 bg-ink-50 px-4 py-3 text-sm text-ink-700">
                  {item}
                </div>
              ))}
            </div>
          </div>

          <div>
            <div className="text-xs uppercase tracking-[0.18em] text-ink-400">Use cases</div>
            <div className="mt-3 flex flex-wrap gap-2">
              {profile.useCases?.map((item) => (
                <span key={item} className="badge bg-sky-100 text-sky-700 px-3 py-1.5 rounded-full">
                  {item}
                </span>
              ))}
            </div>
          </div>

          <div>
            <div className="text-xs uppercase tracking-[0.18em] text-ink-400">Zones</div>
            <div className="mt-3 flex flex-wrap gap-2">
              {profile.zones?.map((zone) => (
                <button
                  key={zone.id}
                  type="button"
                  onClick={() => onZoneSelect?.(selectedZone === zone.id ? null : zone.id)}
                  className={clsx(
                    'rounded-full border px-3 py-1.5 text-sm transition',
                    selectedZone === zone.id
                      ? 'border-ink-900 bg-ink-900 text-white'
                      : 'border-ink-200 bg-white text-ink-700 hover:border-ink-400'
                  )}
                >
                  {zone.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-2xl border border-ink-100 bg-ink-50 p-4 space-y-3">
            <div className="text-xs uppercase tracking-[0.18em] text-ink-400">Impact sliders</div>
            {impactControls.map((control) => (
              <label key={control.id} className="block space-y-1.5">
                <div className="flex items-center justify-between gap-3 text-sm">
                  <span className="font-medium text-ink-800">{control.label}</span>
                  <span className="text-ink-500">{impacts[control.id] ?? control.defaultValue}%</span>
                </div>
                <input
                  type="range"
                  min={control.min}
                  max={control.max}
                  step={control.step}
                  value={impacts[control.id] ?? control.defaultValue}
                  onChange={(event) => onImpactChange?.(control.id, event.target.value)}
                  className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-ink-200 accent-ink-900"
                />
                <div className="text-xs text-ink-500">{control.description}</div>
              </label>
            ))}
          </div>

          <div className="rounded-2xl border border-ink-100 bg-white p-4 space-y-3">
            <div className="text-xs uppercase tracking-[0.18em] text-ink-400">Scenario triggers</div>
            {triggerDefinitions.map((trigger) => (
              <label key={trigger.id} className="flex items-start gap-3 rounded-2xl border border-ink-100 px-3 py-3 cursor-pointer hover:border-ink-300">
                <input
                  type="checkbox"
                  checked={Boolean(triggers[trigger.id])}
                  onChange={(event) => onTriggerChange?.(trigger.id, event.target.checked)}
                  className="mt-1 h-4 w-4 rounded border-ink-300 text-ink-900 focus:ring-ink-500"
                />
                <div>
                  <div className="font-medium text-sm text-ink-900">{trigger.label}</div>
                  <div className="text-xs text-ink-500 mt-1">{trigger.description}</div>
                </div>
              </label>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
