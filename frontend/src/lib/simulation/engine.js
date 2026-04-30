function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function toFiniteNumber(value, fallback) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function hashSeed(input) {
  const text = String(input ?? 'vision-sop');
  let hash = 2166136261;

  for (let index = 0; index < text.length; index += 1) {
    hash ^= text.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }

  return hash >>> 0;
}

function createSeededRng(seed) {
  let state = hashSeed(seed) || 1;

  return function nextRandom() {
    state += 0x6d2b79f5;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

function normalizeSteps(sop) {
  if (!Array.isArray(sop)) {
    return [];
  }

  const ordered = sop
    .map((step, index) => {
      const inferredOrder = Number.isFinite(step?.order)
        ? step.order
        : Number.isFinite(step?.step_index)
          ? step.step_index
          : index;

      return {
        source: step || {},
        id: String(step?.id || `step-${index + 1}`),
        order: inferredOrder,
      };
    })
    .sort((left, right) => left.order - right.order);

  return ordered.map((step, index) => ({
    ...step.source,
    id: step.id,
    order: step.order,
    dependencies: Array.isArray(step.source?.dependencies)
      ? step.source.dependencies.map(String)
      : index === 0
        ? []
        : [ordered[index - 1].id],
  }));
}

function findMissingStepViolations(steps) {
  if (steps.length === 0) {
    return [];
  }

  const violations = [];
  let expectedOrder = steps[0].order > 0 ? 0 : steps[0].order;

  for (const step of steps) {
    while (expectedOrder < step.order) {
      violations.push(`missing required step at order ${expectedOrder}`);
      expectedOrder += 1;
    }

    expectedOrder = step.order + 1;
  }

  return violations;
}

function findBlockedSteps(steps, completedStepIds) {
  const completed = new Set(completedStepIds);

  return steps
    .filter((step) => !completed.has(step.id))
    .filter((step) => step.dependencies.some((dependencyId) => !completed.has(dependencyId)))
    .map((step) => step.id);
}

function canExecute(step, completedStepIds) {
  const completed = new Set(completedStepIds);
  return step.dependencies.every((dependencyId) => completed.has(dependencyId));
}

function normalizeControls(config = {}) {
  const impacts = config.impacts || {};
  const triggers = config.triggers || {};

  return {
    impacts: {
      throughputPressure: clamp(toFiniteNumber(impacts.throughputPressure, 58), 0, 100) / 100,
      staffingLevel: clamp(toFiniteNumber(impacts.staffingLevel, 74), 0, 100) / 100,
      equipmentStrain: clamp(toFiniteNumber(impacts.equipmentStrain, 46), 0, 100) / 100,
      safetySensitivity: clamp(toFiniteNumber(impacts.safetySensitivity, 63), 0, 100) / 100,
      qualitySensitivity: clamp(toFiniteNumber(impacts.qualitySensitivity, 57), 0, 100) / 100,
    },
    triggers: Object.fromEntries(
      Object.entries(triggers).map(([key, value]) => [key, Boolean(value)])
    ),
  };
}

function getFailureThreshold(step, controls, failureRate) {
  const staffingGap = 1 - controls.impacts.staffingLevel;
  let threshold = failureRate;
  threshold += (step?.risk || 0) * 0.22;
  threshold += controls.impacts.equipmentStrain * 0.12;
  threshold += controls.impacts.qualitySensitivity * 0.08;
  threshold += staffingGap * 0.08;

  if (controls.triggers.equipmentFault) threshold += 0.15;
  if (controls.triggers.qualityHold) threshold += 0.08;
  if (controls.triggers.contaminationAlert && /care|cook|pack|qa|quality/i.test(String(step?.zone || ''))) threshold += 0.12;
  if (controls.triggers.forkliftSurge && /dispatch|receiv|dock|load/i.test(String(step?.zone || ''))) threshold += 0.08;
  if (controls.triggers.congestionSpike) threshold += 0.06;
  if (controls.triggers.rushOrder) threshold += 0.05;

  return clamp(threshold, 0, 0.95);
}

function extractViolationStepIds(violations, steps) {
  return Array.from(
    new Set(
      violations.flatMap((violation) =>
        steps
          .filter((step) => String(violation).includes(step.id) || String(violation).includes(step.title || ''))
          .map((step) => step.id)
      )
    )
  );
}

function buildHeatPoints(steps, currentStepId, completedSteps, blockedStepIds, violationStepIds, controls) {
  const completed = new Set(completedSteps);
  const blocked = new Set(blockedStepIds);
  const violations = new Set(violationStepIds);

  return steps.map((step) => {
    const isCompleted = completed.has(step.id);
    const isActive = currentStepId === step.id;
    const isBlocked = blocked.has(step.id);
    const isViolation = violations.has(step.id);

    let intensity = 0.08 + (step.heat || 0.5) * 0.12;
    if (isCompleted) intensity += 0.34;
    if (isActive) intensity += 0.52;
    if (isBlocked) intensity += 0.12;
    if (isViolation) intensity += 0.22;
    intensity += controls.impacts.throughputPressure * 0.12;
    intensity += controls.impacts.equipmentStrain * 0.1;
    intensity += (1 - controls.impacts.staffingLevel) * 0.08;
    if (controls.triggers.congestionSpike) intensity += 0.12;
    if (controls.triggers.rushOrder) intensity += 0.08;
    if (controls.triggers.forkliftSurge && /dispatch|receiv|loading|dock|lane/i.test(String(step.zone || ''))) intensity += 0.14;
    if (controls.triggers.contaminationAlert && /care|cook|pack|quality|lab/i.test(String(step.zone || ''))) intensity += 0.15;
    if (controls.triggers.qualityHold && /quality|inspection|qa|expo/i.test(String(step.zone || ''))) intensity += 0.11;

    return {
      id: step.id,
      zone: step.zone,
      zoneId: step.zoneId,
      asset: step.asset,
      x: step?.blueprintPosition?.x ?? step?.flowPosition?.x ?? 0,
      y: step?.blueprintPosition?.y ?? step?.flowPosition?.y ?? 0,
      intensity: Number(clamp(intensity, 0, 1.4).toFixed(3)),
      status: isViolation ? 'violation' : isActive ? 'active' : isCompleted ? 'completed' : isBlocked ? 'blocked' : 'idle',
    };
  });
}

function summarizeByKey(points, key) {
  return points.reduce((accumulator, point) => {
    const bucketKey = point[key] || 'unassigned';
    accumulator[bucketKey] = Number(((accumulator[bucketKey] || 0) + point.intensity).toFixed(3));
    return accumulator;
  }, {});
}

function buildSnapshotState(steps, currentStepId, completedSteps, blockedStepIds, violations, controls) {
  const violationStepIds = extractViolationStepIds(violations, steps);
  const heatPoints = buildHeatPoints(steps, currentStepId, completedSteps, blockedStepIds, violationStepIds, controls);
  const zoneLoads = summarizeByKey(heatPoints, 'zone');
  const assetImpacts = summarizeByKey(heatPoints, 'asset');
  const riskScore = Number(
    clamp(
      violations.length * 0.12 + Object.values(zoneLoads).reduce((total, value) => total + value, 0) / Math.max(1, heatPoints.length * 4),
      0,
      1
    ).toFixed(3)
  );

  return {
    currentStep: currentStepId,
    activeZone: steps.find((step) => step.id === currentStepId)?.zone || null,
    completedSteps: [...completedSteps],
    blockedSteps: [...blockedStepIds],
    violations: [...violations],
    violationStepIds,
    heatPoints,
    zoneLoads,
    assetImpacts,
    riskScore,
    triggeredScenarios: Object.keys(controls.triggers).filter((key) => controls.triggers[key]),
  };
}

export function runSimulation(sop, config = {}) {
  const steps = normalizeSteps(sop);
  const maxTicks = Math.max(0, Math.floor(toFiniteNumber(config.maxTicks, 100)));
  const failureRate = clamp(toFiniteNumber(config.failureRate, 0), 0, 1);
  const rng = createSeededRng(config.seed ?? 'vision-sop-simulation');
  const controls = normalizeControls(config);

  const timeline = [];
  const completedSteps = [];
  const violations = [...findMissingStepViolations(steps)];

  if (steps.length === 0 || maxTicks === 0) {
    return timeline;
  }

  for (let tick = 1; tick <= maxTicks; tick += 1) {
    const nextStep = steps.find((step) => !completedSteps.includes(step.id));

    if (!nextStep) {
      break;
    }

    const blockedSteps = findBlockedSteps(steps, completedSteps);
    const events = [];

    if (tick === 1 && violations.length > 0) {
      events.push(...violations.map((violation) => `tick ${tick}: ${violation}`));
    }

    if (!canExecute(nextStep, completedSteps)) {
      events.push(`tick ${tick}: ${nextStep.id} blocked by incomplete dependencies`);
    } else {
      const threshold = getFailureThreshold(nextStep, controls, failureRate);
      const failed = rng() < threshold;

      if (failed) {
        const violation = `tick ${tick}: ${nextStep.id} failed`;
        violations.push(violation);
        events.push(`tick ${tick}: attempted ${nextStep.id}`);
        events.push(violation);
      } else {
        completedSteps.push(nextStep.id);
        events.push(`tick ${tick}: completed ${nextStep.id}`);
      }
    }

    const state = buildSnapshotState(steps, nextStep.id, completedSteps, blockedSteps, violations, controls);

    timeline.push({
      tick,
      state,
      events,
    });

    if (completedSteps.length === steps.length) {
      break;
    }
  }

  return timeline;
}

