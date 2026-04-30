import { describe, expect, it } from "vitest";
import { runSimulation } from "./engine.js";

function createBackendStep(stepIndex, overrides = {}) {
  return {
    id: overrides.id || `step-${stepIndex}`,
    step_index: stepIndex,
    action_label: overrides.action_label || `action-${stepIndex}`,
    title: overrides.title || `Step ${stepIndex + 1}`,
    instruction: overrides.instruction || `Execute step ${stepIndex + 1}`,
    target_duration_s: overrides.target_duration_s ?? 2.5,
    tolerance_s: overrides.tolerance_s ?? 0.5,
    clip_start_s: overrides.clip_start_s ?? null,
    clip_end_s: overrides.clip_end_s ?? null,
    clip_path: overrides.clip_path ?? null,
    required_ppe: overrides.required_ppe ?? [],
    ...overrides,
  };
}

describe("runSimulation", () => {
  it("completes a linear SOP fully", () => {
    const sop = [
      createBackendStep(0, { id: "pick" }),
      createBackendStep(1, { id: "place" }),
      createBackendStep(2, { id: "inspect" }),
    ];

    const snapshots = runSimulation(sop, {
      maxTicks: 10,
      seed: "linear-seed",
      failureRate: 0,
    });

    expect(snapshots).toHaveLength(3);
    expect(snapshots.at(-1)?.state.completedSteps).toEqual(["pick", "place", "inspect"]);
    expect(snapshots.at(-1)?.state.violations).toEqual([]);
  });

  it("triggers a violation when a backend step is missing from sequence", () => {
    const sop = [
      createBackendStep(0, { id: "pick" }),
      createBackendStep(2, { id: "inspect" }),
    ];

    const snapshots = runSimulation(sop, {
      maxTicks: 10,
      seed: "missing-step-seed",
      failureRate: 0,
    });

    expect(snapshots.length).toBeGreaterThan(0);
    expect(snapshots[0].state.violations).toContain("missing required step at order 1");
    expect(snapshots[0].events).toContain("tick 1: missing required step at order 1");
  });

  it("is deterministic for the same seed", () => {
    const sop = [
      createBackendStep(0, { id: "pick" }),
      createBackendStep(1, { id: "place" }),
      createBackendStep(2, { id: "inspect" }),
      createBackendStep(3, { id: "pack" }),
    ];

    const config = {
      maxTicks: 12,
      seed: "deterministic-seed",
      failureRate: 0.35,
    };

    const firstRun = runSimulation(sop, config);
    const secondRun = runSimulation(sop, config);

    expect(firstRun).toEqual(secondRun);
  });
});
