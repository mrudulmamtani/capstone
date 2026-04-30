function collectDownstream(startId, adjacency) {
  const visited = new Set();
  const queue = [startId];

  while (queue.length > 0) {
    const current = queue.shift();
    if (!current || visited.has(current)) {
      continue;
    }
    visited.add(current);
    for (const nextId of adjacency.get(current) || []) {
      if (!visited.has(nextId)) {
        queue.push(nextId);
      }
    }
  }

  return visited;
}

export function getAffectedStepIds(steps = [], selectedStepId = null) {
  if (!selectedStepId) {
    return [];
  }

  const selectedStep = steps.find((step) => step.id === selectedStepId);
  if (!selectedStep) {
    return [];
  }

  const adjacency = new Map();
  for (const step of steps) {
    const dependencies = Array.isArray(step.dependencies) ? step.dependencies : [];
    for (const dependencyId of dependencies) {
      const list = adjacency.get(dependencyId) || [];
      list.push(step.id);
      adjacency.set(dependencyId, list);
    }
  }

  const affected = collectDownstream(selectedStepId, adjacency);

  for (const step of steps) {
    if (step.asset && step.asset === selectedStep.asset) {
      affected.add(step.id);
    }
    if (step.zoneId && step.zoneId === selectedStep.zoneId) {
      affected.add(step.id);
    }
  }

  return Array.from(affected);
}

export function getAffectedAssets(steps = [], selectedStepId = null) {
  const affectedStepIds = new Set(getAffectedStepIds(steps, selectedStepId));
  return Array.from(
    new Set(
      steps
        .filter((step) => affectedStepIds.has(step.id))
        .map((step) => step.asset)
        .filter(Boolean)
    )
  );
}
