const GRID_X = 360;
const GRID_Y = 220;
const ORIGIN_X = 110;
const ORIGIN_Y = 90;

function normalizeSteps(steps) {
  if (!Array.isArray(steps)) {
    return [];
  }

  return steps
    .map((step, index) => ({
      ...step,
      id: String(step?.id || `step-${index + 1}`),
      order: Number.isFinite(step?.order)
        ? step.order
        : Number.isFinite(step?.step_index)
          ? step.step_index
          : index,
    }))
    .sort((left, right) => left.order - right.order);
}

function getNodePosition(step, index) {
  if (step?.flowPosition) {
    return step.flowPosition;
  }

  const column = Number.isFinite(step?.column) ? step.column : index % 5;
  const row = Number.isFinite(step?.row) ? step.row : Math.floor(index / 5);

  return {
    x: ORIGIN_X + column * GRID_X,
    y: ORIGIN_Y + row * GRID_Y,
  };
}

export function layoutGraph(steps) {
  const orderedSteps = normalizeSteps(steps);

  const nodes = orderedSteps.map((step, index) => ({
    id: step.id,
    data: step,
    position: getNodePosition(step, index),
  }));

  const edges = orderedSteps.slice(1).map((step, index) => {
    const previousStep = orderedSteps[index];
    return {
      id: `${previousStep.id}-${step.id}`,
      source: previousStep.id,
      target: step.id,
    };
  });

  return { nodes, edges };
}

