import { useMemo } from 'react';
import Plot from 'react-plotly.js';

const GRID_COLUMNS = 44;
const GRID_ROWS = 30;

function resolveBlueprintSource(path) {
  if (!path) {
    return null;
  }

  if (typeof window === 'undefined') {
    return path;
  }

  try {
    return new URL(path, window.location.origin).toString();
  } catch {
    return path;
  }
}

function getStatusStyles(point, isSelected, isAffected) {
  if (isSelected) {
    return { color: '#111827', size: 22 };
  }
  switch (point?.status) {
    case 'violation':
      return { color: '#dc2626', size: isAffected ? 18 : 16 };
    case 'active':
      return { color: '#2563eb', size: isAffected ? 18 : 16 };
    case 'completed':
      return { color: '#16a34a', size: isAffected ? 15 : 13 };
    case 'blocked':
      return { color: '#6b7280', size: isAffected ? 16 : 14 };
    default:
      return { color: isAffected ? '#f59e0b' : '#ffffff', size: isAffected ? 13 : 10 };
  }
}

function buildHeatmapGrid(profile, heatPoints, selectedZone, affectedStepIds) {
  const width = profile?.width || 1000;
  const height = profile?.height || 700;
  const xValues = Array.from({ length: GRID_COLUMNS }, (_, index) => Number(((index / (GRID_COLUMNS - 1)) * width).toFixed(1)));
  const yValues = Array.from({ length: GRID_ROWS }, (_, index) => Number(((index / (GRID_ROWS - 1)) * height).toFixed(1)));
  const affectedSet = new Set(affectedStepIds || []);

  const zValues = yValues.map((y) =>
    xValues.map((x) => {
      let total = 0;
      for (const point of heatPoints) {
        if (selectedZone && point.zoneId !== selectedZone) {
          continue;
        }
        const dx = x - point.x;
        const dy = y - point.y;
        const sigma = point.status === 'active' ? 62 : point.status === 'violation' ? 74 : 54;
        const gaussian = Math.exp(-(dx * dx + dy * dy) / (2 * sigma * sigma));
        const affectedBoost = affectedSet.has(point.id) ? 1.22 : 1;
        total += point.intensity * affectedBoost * gaussian;
      }
      return Number(total.toFixed(4));
    })
  );

  return { xValues, yValues, zValues };
}

export default function BlueprintHeatmapFigure({
  steps = [],
  snapshot = null,
  profile = null,
  selectedZone = null,
  selectedStepId = null,
  affectedStepIds = [],
  onSelectZone,
  onSelectStep,
  height = 720,
}) {
  const state = snapshot?.state || {};
  const heatPoints = state.heatPoints || [];
  const affectedSet = useMemo(() => new Set(affectedStepIds || []), [affectedStepIds]);
  const imageSource = useMemo(() => resolveBlueprintSource(profile?.blueprintImage), [profile?.blueprintImage]);

  const { xValues, yValues, zValues } = useMemo(
    () => buildHeatmapGrid(profile, heatPoints, selectedZone, affectedStepIds),
    [affectedStepIds, heatPoints, profile, selectedZone]
  );

  const markers = useMemo(() => {
    return steps.map((step) => {
      const point = heatPoints.find((heatPoint) => heatPoint.id === step.id);
      const styles = getStatusStyles(point, step.id === selectedStepId, affectedSet.has(step.id));
      return {
        ...step,
        x: step.blueprintPosition?.x ?? 0,
        y: step.blueprintPosition?.y ?? 0,
        status: point?.status || 'idle',
        color: styles.color,
        size: styles.size,
      };
    });
  }, [affectedSet, heatPoints, selectedStepId, steps]);

  const layout = useMemo(() => {
    const width = profile?.width || 1000;
    const plotHeight = profile?.height || 700;

    return {
      autosize: true,
      margin: { l: 0, r: 0, t: 0, b: 0 },
      paper_bgcolor: '#ffffff',
      plot_bgcolor: '#ffffff',
      showlegend: false,
      dragmode: 'pan',
      images: imageSource
        ? [
            {
              source: imageSource,
              xref: 'x',
              yref: 'y',
              x: 0,
              y: plotHeight,
              sizex: width,
              sizey: plotHeight,
              xanchor: 'left',
              yanchor: 'top',
              sizing: 'stretch',
              opacity: 1,
              layer: 'below',
            },
          ]
        : [],
      shapes: (profile?.zones || []).map((zone) => ({
        type: 'rect',
        x0: zone.bounds[0],
        y0: zone.bounds[1],
        x1: zone.bounds[2],
        y1: zone.bounds[3],
        line: {
          color: zone.id === selectedZone ? zone.color : 'rgba(15, 23, 42, 0.12)',
          width: zone.id === selectedZone ? 3 : 1,
          dash: zone.id === selectedZone ? 'solid' : 'dot',
        },
        fillcolor: zone.id === selectedZone ? 'rgba(15, 23, 42, 0.05)' : 'rgba(255, 255, 255, 0)',
      })),
      xaxis: { range: [0, width], visible: false, fixedrange: true },
      yaxis: { range: [plotHeight, 0], visible: false, fixedrange: true, scaleanchor: 'x', scaleratio: 1 },
    };
  }, [imageSource, profile, selectedZone]);

  const data = useMemo(() => {
    const filteredMarkers = markers.filter((item) => !selectedZone || item.zoneId === selectedZone);
    const zMax = Math.max(1.2, ...zValues.flat());

    return [
      {
        type: 'heatmap',
        x: xValues,
        y: yValues,
        z: zValues,
        zsmooth: 'best',
        opacity: 0.55,
        hoverinfo: 'skip',
        colorscale: [
          [0, 'rgba(0,0,0,0)'],
          [0.15, 'rgba(34,197,94,0.22)'],
          [0.35, 'rgba(234,179,8,0.34)'],
          [0.6, 'rgba(249,115,22,0.52)'],
          [1, 'rgba(220,38,38,0.78)'],
        ],
        zmin: 0,
        zmax: zMax,
        showscale: false,
      },
      {
        type: 'contour',
        x: xValues,
        y: yValues,
        z: zValues,
        opacity: 0.25,
        showscale: false,
        hoverinfo: 'skip',
        contours: {
          coloring: 'lines',
          showlines: true,
          start: 0.15,
          end: zMax,
          size: 0.12,
        },
        line: { color: 'rgba(15,23,42,0.45)', width: 0.9 },
      },
      {
        type: 'scatter',
        mode: 'markers+text',
        x: filteredMarkers.map((item) => item.x),
        y: filteredMarkers.map((item) => item.y),
        text: filteredMarkers.map((item) => item.title),
        textposition: 'top center',
        textfont: { family: 'Inter, sans-serif', size: 11, color: '#111827' },
        marker: {
          color: filteredMarkers.map((item) => item.color),
          size: filteredMarkers.map((item) => item.size),
          line: { color: '#ffffff', width: 2 },
          opacity: filteredMarkers.map((item) => {
            if (selectedStepId && item.id !== selectedStepId && !affectedSet.has(item.id)) {
              return 0.3;
            }
            return 1;
          }),
        },
        customdata: filteredMarkers.map((item) => [item.id, item.zoneId]),
        hovertemplate: '<b>%{text}</b><extra></extra>',
      },
    ];
  }, [affectedSet, markers, selectedStepId, selectedZone, xValues, yValues, zValues]);

  function handleClick(event) {
    const [stepId, zoneId] = event?.points?.[0]?.customdata || [];
    if (stepId) {
      onSelectStep?.(stepId === selectedStepId ? null : stepId);
    }
    if (zoneId) {
      onSelectZone?.(zoneId === selectedZone ? null : zoneId);
    }
  }

  return (
    <Plot
      data={data}
      layout={layout}
      onClick={handleClick}
      config={{
        displaylogo: false,
        responsive: true,
        modeBarButtonsToRemove: ['lasso2d', 'select2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d'],
      }}
      style={{ width: '100%', height: `${height}px` }}
      useResizeHandler
    />
  );
}
