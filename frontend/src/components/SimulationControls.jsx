import { Pause, Play } from "lucide-react";

function clampTick(value, maxTick) {
  return Math.min(Math.max(0, value), Math.max(0, maxTick));
}

export default function SimulationControls({
  currentTick = 0,
  maxTick = 0,
  onChange,
  onPlay,
  onPause,
  isPlaying = false,
}) {
  function handleToggle() {
    if (isPlaying) {
      onPause?.();
      return;
    }

    onPlay?.();
  }

  function handleSliderChange(event) {
    onChange?.(Number(event.target.value));
  }

  const safeTick = clampTick(currentTick, maxTick);
  const progress = maxTick === 0 ? 0 : Math.round((safeTick / maxTick) * 100);

  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <div className="text-sm text-ink-500">Simulation playback</div>
          <h2 className="text-lg font-semibold">Controls</h2>
        </div>
        <div className="badge bg-ink-100 text-ink-700">
          Tick {safeTick} / {Math.max(0, maxTick)}
        </div>
      </div>

      <div className="flex flex-col gap-4 lg:flex-row lg:items-center">
        <button
          type="button"
          onClick={handleToggle}
          className={isPlaying ? "btn-ghost" : "btn-primary"}
          disabled={maxTick <= 0}
        >
          {isPlaying ? <Pause size={16} /> : <Play size={16} />}
          {isPlaying ? "Pause" : "Play"}
        </button>

        <div className="flex-1 space-y-2">
          <div className="flex items-center justify-between text-xs text-ink-500">
            <span>Progress</span>
            <span>{progress}%</span>
          </div>
          <input
            type="range"
            min="0"
            max={Math.max(0, maxTick)}
            value={safeTick}
            onChange={handleSliderChange}
            className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-ink-100 accent-ink-900"
          />
        </div>
      </div>
    </div>
  );
}
