import { useEffect, useMemo, useState } from 'react';
import { runSimulation } from '../lib/simulation/engine.js';
import {
  getDefaultImpacts,
  getDefaultTriggers,
  getImpactControls,
  getScenarioSummary,
  getSimulationProfile,
  listSimulationProfiles,
  materializeSimulationSteps,
} from '../lib/simulation/scenario.js';

const PLAYBACK_INTERVAL_MS = 500;

function clampTick(value, max) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return 0;
  }
  return Math.max(0, Math.min(max, Math.floor(parsed)));
}

export function useSimulation(sop, options = {}) {
  const profiles = useMemo(() => listSimulationProfiles(), []);
  const impactControls = useMemo(() => getImpactControls(), []);
  const [selectedProfileId, setSelectedProfileId] = useState(options.profileId || null);
  const [impacts, setImpacts] = useState(() => ({ ...getDefaultImpacts(), ...(options.impacts || {}) }));
  const [triggers, setTriggers] = useState(() => options.triggers || {});
  const [snapshots, setSnapshots] = useState([]);
  const [currentTick, setCurrentTick] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    if (!sop) {
      return;
    }

    const defaultProfile = getSimulationProfile(sop, options.profileId);
    setSelectedProfileId(options.profileId || defaultProfile.id);
    setImpacts({ ...getDefaultImpacts(), ...(options.impacts || {}) });
    setTriggers({ ...getDefaultTriggers(defaultProfile), ...(options.triggers || {}) });
    setCurrentTick(0);
    setIsPlaying(false);
  }, [options.impacts, options.profileId, options.triggers, sop?.id]);

  const profile = useMemo(() => {
    if (!sop) {
      return profiles[0] || null;
    }
    return getSimulationProfile(sop, selectedProfileId);
  }, [profiles, selectedProfileId, sop]);

  useEffect(() => {
    if (!profile) {
      return;
    }

    setTriggers((current) => ({
      ...getDefaultTriggers(profile),
      ...current,
      ...(options.triggers || {}),
    }));
  }, [options.triggers, profile]);

  const steps = useMemo(() => {
    if (!profile) {
      return [];
    }

    return materializeSimulationSteps(sop, {
      profileId: profile.id,
      impacts,
      triggers,
    });
  }, [impacts, profile, sop, triggers]);

  const summary = useMemo(() => {
    if (!profile) {
      return null;
    }

    return getScenarioSummary(sop, {
      profileId: profile.id,
      impacts,
      triggers,
    });
  }, [impacts, profile, sop, triggers]);

  useEffect(() => {
    if (!steps.length) {
      setSnapshots([]);
      setCurrentTick(0);
      setIsPlaying(false);
      return;
    }

    const throughputFactor = (impacts.throughputPressure ?? 58) / 100;
    const equipmentFactor = (impacts.equipmentStrain ?? 46) / 100;
    const qualityFactor = (impacts.qualitySensitivity ?? 57) / 100;
    const staffingGap = 1 - (impacts.staffingLevel ?? 74) / 100;
    const triggerCount = Object.values(triggers).filter(Boolean).length;
    const failureRate = Math.min(
      0.72,
      0.04 + throughputFactor * 0.08 + equipmentFactor * 0.14 + qualityFactor * 0.06 + staffingGap * 0.08 + triggerCount * 0.03
    );

    const nextSnapshots = runSimulation(steps, {
      maxTicks: Math.max(steps.length * 3, 80),
      seed: [sop?.id, profile?.id, JSON.stringify(impacts), JSON.stringify(triggers)].join('::'),
      failureRate,
      impacts,
      triggers,
    });

    setSnapshots(nextSnapshots);
    setCurrentTick((tick) => {
      const fallback = options.defaultTick === 'last' ? Math.max(0, nextSnapshots.length - 1) : 0;
      return clampTick(nextSnapshots.length ? tick || fallback : 0, Math.max(0, nextSnapshots.length - 1));
    });
    setIsPlaying(false);
  }, [impacts, options.defaultTick, profile?.id, sop?.id, steps, triggers]);

  useEffect(() => {
    if (!isPlaying || snapshots.length <= 1 || options.disablePlayback) {
      return undefined;
    }

    const timer = window.setInterval(() => {
      setCurrentTick((tick) => {
        if (tick >= snapshots.length - 1) {
          setIsPlaying(false);
          return snapshots.length - 1;
        }
        return tick + 1;
      });
    }, PLAYBACK_INTERVAL_MS);

    return () => window.clearInterval(timer);
  }, [isPlaying, options.disablePlayback, snapshots.length]);

  const currentSnapshot = snapshots[currentTick] || null;

  function play() {
    if (snapshots.length <= 1 || options.disablePlayback) {
      return;
    }

    setCurrentTick((tick) => (tick >= snapshots.length - 1 ? 0 : tick));
    setIsPlaying(true);
  }

  function pause() {
    setIsPlaying(false);
  }

  function setTick(value) {
    setCurrentTick(clampTick(value, Math.max(0, snapshots.length - 1)));
  }

  function setImpact(controlId, value) {
    setImpacts((current) => ({
      ...current,
      [controlId]: Math.max(0, Math.min(100, Number(value))),
    }));
  }

  function setTrigger(triggerId, enabled) {
    setTriggers((current) => ({
      ...current,
      [triggerId]: Boolean(enabled),
    }));
  }

  return {
    steps,
    profile,
    profiles,
    summary,
    impactControls,
    impacts,
    triggers,
    selectedProfileId: profile?.id || selectedProfileId,
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
  };
}
