const API_ROOT = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const DEMO_VIDEO_LIBRARY = [
  {
    id: "final-assembly-reference",
    title: "Final Assembly Reference",
    station: "Station 1",
    sopTitle: "Final Assembly QA",
    description: "Golden-batch reference clip used to generate the published SOP and optimized heatmap.",
    serverPath: "/app/data/videos/final-assembly-reference.mp4",
    publicUrl: `${API_ROOT}/assets/videos/final-assembly-reference.mp4`,
    heatmapUrl: `${API_ROOT}/assets/heatmaps/final-assembly-reference.png`,
    tags: ["golden batch", "reference", "heatmap"],
  },
  {
    id: "final-assembly-run-delayed",
    title: "Final Assembly Delayed Run",
    station: "Station 1",
    sopTitle: "Final Assembly QA",
    description: "Monitoring run with added delay and extra transport motion for a strong deviation demo.",
    serverPath: "/app/data/videos/final-assembly-run-delayed.mp4",
    publicUrl: `${API_ROOT}/assets/videos/final-assembly-run-delayed.mp4`,
    heatmapUrl: `${API_ROOT}/assets/heatmaps/final-assembly-run-delayed.png`,
    tags: ["deviation", "alerts", "ergonomics"],
  },
  {
    id: "subassembly-reference",
    title: "Sub-Assembly Reference",
    station: "Station 2",
    sopTitle: "Sub-Assembly Part B",
    description: "Reference sub-assembly clip that shows the optimized workstation layout.",
    serverPath: "/app/data/videos/subassembly-reference.mp4",
    publicUrl: `${API_ROOT}/assets/videos/subassembly-reference.mp4`,
    heatmapUrl: `${API_ROOT}/assets/heatmaps/subassembly-reference.png`,
    tags: ["optimized", "reference", "station 2"],
  },
  {
    id: "subassembly-motion-waste",
    title: "Sub-Assembly Motion Waste",
    station: "Station 2",
    sopTitle: "Sub-Assembly Part B",
    description: "Deliberately wider movement pattern that makes the ergonomic heatmap and layout recommendations obvious.",
    serverPath: "/app/data/videos/subassembly-motion-waste.mp4",
    publicUrl: `${API_ROOT}/assets/videos/subassembly-motion-waste.mp4`,
    heatmapUrl: `${API_ROOT}/assets/heatmaps/subassembly-motion-waste.png`,
    tags: ["motion waste", "layout", "ergonomics"],
  },
];

export function findDemoAssetByServerPath(path) {
  return DEMO_VIDEO_LIBRARY.find((asset) => asset.serverPath === path) || null;
}

export function assetUrlFromSourceUri(sourceUri) {
  if (!sourceUri) return "";
  const filename = sourceUri.split(/[\\/]/).pop();
  return filename ? `${API_ROOT}/assets/videos/${filename}` : "";
}

export function heatmapUrlFromSourceUri(sourceUri) {
  if (!sourceUri) return "";
  const filename = sourceUri.split(/[\\/]/).pop();
  const stem = filename?.replace(/\.[^.]+$/, "");
  return stem ? `${API_ROOT}/assets/heatmaps/${stem}.png` : "";
}
