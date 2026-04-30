import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Background,
  Controls,
  MiniMap,
  Position,
  ReactFlow,
  Handle,
  useEdgesState,
  useNodesState,
} from '@xyflow/react';
import { Expand, Shrink } from 'lucide-react';
import '@xyflow/react/dist/style.css';
import { layoutGraph } from '../lib/graph/layout.js';

const STORAGE_PREFIX = 'vision-sop-layout:';
const ZONE_LABELS = [
  { id: 'receiving', label: 'Receiving' },
  { id: 'cleaning', label: 'Cleaning' },
  { id: 'treatment', label: 'Processing' },
  { id: 'silos', label: 'Storage / QA' },
  { id: 'dispatch', label: 'Dispatch' },
  { id: 'raw', label: 'Raw / Prep' },
  { id: 'primary', label: 'Primary / Cook' },
  { id: 'packaging', label: 'Packaging' },
  { id: 'dining', label: 'Dining / Service' },
  { id: 'machining', label: 'Machining' },
];

const STATUS_STYLES = {
  completed: {
    container: 'border-emerald-200 bg-emerald-50 text-emerald-900',
    pill: 'bg-emerald-600 text-white',
  },
  active: {
    container: 'border-sky-200 bg-sky-50 text-sky-950 shadow-[0_0_0_1px_rgba(14,165,233,0.15)]',
    pill: 'bg-sky-600 text-white',
  },
  blocked: {
    container: 'border-slate-300 bg-slate-100 text-slate-700',
    pill: 'bg-slate-600 text-white',
  },
  violation: {
    container: 'border-red-200 bg-red-50 text-red-900',
    pill: 'bg-red-600 text-white',
  },
  idle: {
    container: 'border-ink-200 bg-white text-ink-900',
    pill: 'bg-ink-200 text-ink-700',
  },
};

function getSnapshotState(snapshot) {
  return snapshot?.state || snapshot || {};
}

function extractViolationStepIds(violations = [], steps = []) {
  return Array.from(
    new Set(
      violations.flatMap((entry) =>
        steps
          .filter((step) => String(entry).includes(step.id) || String(entry).includes(step.title || ''))
          .map((step) => step.id)
      )
    )
  );
}

function getNodeStatus(stepId, state, violationStepIds) {
  if (violationStepIds.includes(stepId)) return 'violation';
  if (state.currentStep === stepId) return 'active';
  if ((state.completedSteps || []).includes(stepId)) return 'completed';
  if ((state.blockedSteps || []).includes(stepId)) return 'blocked';
  return 'idle';
}

function readStoredPositions(storageKey) {
  if (typeof window === 'undefined' || !storageKey) {
    return {};
  }

  try {
    return JSON.parse(window.localStorage.getItem(`${STORAGE_PREFIX}${storageKey}`) || '{}');
  } catch {
    return {};
  }
}

function writeStoredPositions(storageKey, nodes) {
  if (typeof window === 'undefined' || !storageKey) {
    return;
  }

  const payload = Object.fromEntries(nodes.map((node) => [node.id, node.position]));
  window.localStorage.setItem(`${STORAGE_PREFIX}${storageKey}`, JSON.stringify(payload));
}

function SOPNode({ data }) {
  const styles = STATUS_STYLES[data.status] || STATUS_STYLES.idle;
  const order = Number.isFinite(data.order)
    ? data.order + 1
    : Number.isFinite(data.step_index)
      ? data.step_index + 1
      : null;

  return (
    <>
      <Handle type="target" position={Position.Left} className="!h-3 !w-3 !border-2 !border-white !bg-ink-400" />
      <div
        className={`min-w-[260px] max-w-[300px] rounded-2xl border p-4 transition shadow-sm ${styles.container} ${
          data.isMuted ? 'opacity-25' : 'opacity-100'
        } ${data.isAffected ? 'ring-2 ring-amber-400/60' : ''} ${data.isSelected ? 'ring-4 ring-ink-900/20 scale-[1.01]' : ''}`}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="text-[11px] uppercase tracking-[0.2em] opacity-70">{data.zone || 'station'}</div>
            <div className="mt-1 text-base font-semibold leading-6 break-words">
              {order ? `${order}. ` : ''}
              {data.title || data.action_label || data.id}
            </div>
          </div>
          <span className={`rounded-full px-2.5 py-1 text-[11px] font-medium capitalize whitespace-nowrap ${styles.pill}`}>
            {data.status}
          </span>
        </div>

        <div className="mt-3 flex flex-wrap gap-2 text-xs opacity-85">
          <span className="rounded-full bg-white/70 px-2 py-1">{data.action_label || 'step'}</span>
          {data.asset && <span className="rounded-full bg-white/70 px-2 py-1">{data.asset}</span>}
          {Number.isFinite(data.target_duration_s) && (
            <span className="rounded-full bg-white/70 px-2 py-1">{data.target_duration_s.toFixed(1)}s</span>
          )}
        </div>
      </div>
      <Handle type="source" position={Position.Right} className="!h-3 !w-3 !border-2 !border-white !bg-ink-400" />
    </>
  );
}

const nodeTypes = { sopNode: SOPNode };

export default function SOPGraph({
  steps = [],
  snapshot = null,
  storageKey = 'default',
  selectedZone = null,
  selectedStepId = null,
  affectedStepIds = [],
  onSelectZone,
  onSelectStep,
}) {
  const graph = useMemo(() => layoutGraph(steps), [steps]);
  const state = getSnapshotState(snapshot);
  const [flowInstance, setFlowInstance] = useState(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const containerRef = useRef(null);
  const affectedSet = useMemo(() => new Set(affectedStepIds || []), [affectedStepIds]);

  const baseNodes = useMemo(() => {
    const violationStepIds = extractViolationStepIds(state.violations, steps);
    return graph.nodes.map((node) => {
      const status = getNodeStatus(node.id, state, violationStepIds);
      const isSelected = node.id === selectedStepId;
      const isAffected = affectedSet.has(node.id);
      const isMuted = Boolean(selectedStepId) && !isSelected && !isAffected;
      const zoneMuted = Boolean(selectedZone) && node.data.zoneId !== selectedZone;
      return {
        ...node,
        type: 'sopNode',
        draggable: true,
        selectable: true,
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
        data: {
          ...node.data,
          status,
          isSelected,
          isAffected,
          isMuted: isMuted || zoneMuted,
        },
      };
    });
  }, [affectedSet, graph.nodes, selectedStepId, selectedZone, state, steps]);

  const baseEdges = useMemo(
    () =>
      graph.edges.map((edge) => {
        const isActive = state.currentStep === edge.target;
        const isAffected = affectedSet.has(edge.source) && affectedSet.has(edge.target);
        const isMuted = Boolean(selectedStepId) && !isAffected;
        const sourceStep = steps.find((step) => step.id === edge.source);
        const targetStep = steps.find((step) => step.id === edge.target);
        const zoneFiltered = Boolean(selectedZone) && sourceStep?.zoneId !== selectedZone && targetStep?.zoneId !== selectedZone;
        return {
          ...edge,
          type: 'smoothstep',
          animated: isActive,
          hidden: zoneFiltered,
          style: {
            stroke: isActive ? '#0ea5e9' : isAffected ? '#f59e0b' : '#94a3b8',
            strokeWidth: isActive ? 3 : isAffected ? 3 : 2,
            opacity: isMuted || zoneFiltered ? 0.18 : 1,
          },
        };
      }),
    [affectedSet, graph.edges, selectedStepId, selectedZone, state.currentStep, steps]
  );

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    const storedPositions = readStoredPositions(storageKey);
    setNodes((currentNodes) => {
      const currentPositions = Object.fromEntries(currentNodes.map((node) => [node.id, node.position]));
      return baseNodes.map((node) => ({
        ...node,
        position: currentPositions[node.id] || storedPositions[node.id] || node.position,
      }));
    });
  }, [baseNodes, setNodes, storageKey]);

  useEffect(() => {
    setEdges(baseEdges);
  }, [baseEdges, setEdges]);

  useEffect(() => {
    function handleFullscreenChange() {
      setIsFullscreen(Boolean(document.fullscreenElement && containerRef.current && document.fullscreenElement === containerRef.current));
    }

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  function handleNodeDragStop(_, draggedNode) {
    setNodes((currentNodes) => {
      const nextNodes = currentNodes.map((node) => (node.id === draggedNode.id ? { ...node, position: draggedNode.position } : node));
      writeStoredPositions(storageKey, nextNodes);
      return nextNodes;
    });
  }

  function handleNodeClick(_, node) {
    onSelectStep?.(node.id === selectedStepId ? null : node.id);
    const zoneId = node?.data?.zoneId;
    if (zoneId) {
      onSelectZone?.(zoneId);
    }
  }

  function toggleFullscreen() {
    if (!containerRef.current) {
      return;
    }

    if (document.fullscreenElement === containerRef.current) {
      document.exitFullscreen?.();
      return;
    }

    containerRef.current.requestFullscreen?.();
  }

  useEffect(() => {
    if (!flowInstance || !state.currentStep) {
      return;
    }

    const activeNode = nodes.find((node) => node.id === state.currentStep);
    if (!activeNode) {
      return;
    }

    flowInstance.setCenter(activeNode.position.x + 140, activeNode.position.y + 70, {
      zoom: isFullscreen ? 1.02 : 0.92,
      duration: 450,
    });
  }, [flowInstance, isFullscreen, nodes, state.currentStep]);

  const canvasHeight = isFullscreen ? 'calc(100vh - 160px)' : '760px';

  return (
    <div ref={containerRef} className={`card p-5 space-y-4 ${isFullscreen ? 'rounded-none border-0 shadow-none bg-white h-screen' : ''}`}>
      <div className="flex items-center justify-between gap-4">
        <div>
          <div className="text-sm text-ink-500">Flow mode</div>
          <h2 className="text-lg font-semibold">Movable zone-based SOP network</h2>
          <div className="text-xs text-ink-400 mt-1">
            Drag nodes freely, stored per SOP in localStorage. Click a node to reveal the affected path, linked assets, and the related blueprint zone.
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs">
          {['completed', 'active', 'blocked', 'violation'].map((label) => (
            <span key={label} className={`rounded-full px-2.5 py-1 font-medium capitalize ${STATUS_STYLES[label].pill}`}>
              {label}
            </span>
          ))}
          <button type="button" onClick={toggleFullscreen} className="btn-ghost">
            {isFullscreen ? <Shrink size={16} /> : <Expand size={16} />}
            {isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
          </button>
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-ink-100 bg-slate-50">
        <div className="flex flex-wrap gap-x-5 gap-y-2 border-b border-ink-100 bg-white/80 px-4 py-3 text-xs uppercase tracking-[0.2em] text-ink-400">
          {ZONE_LABELS.map((zone) => (
            <button
              key={zone.id}
              type="button"
              onClick={() => onSelectZone?.(selectedZone === zone.id ? null : zone.id)}
              className={`${selectedZone === zone.id ? 'text-ink-900 font-semibold' : ''}`}
            >
              {zone.label}
            </button>
          ))}
        </div>
        <div style={{ height: canvasHeight }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeDragStop={handleNodeDragStop}
            onNodeClick={handleNodeClick}
            onInit={setFlowInstance}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.18, minZoom: 0.4 }}
            minZoom={0.2}
            maxZoom={1.9}
            proOptions={{ hideAttribution: true }}
            nodesDraggable
            nodesConnectable={false}
            elementsSelectable
            panOnDrag
            selectionOnDrag
            snapToGrid={false}
            defaultEdgeOptions={{ type: 'smoothstep' }}
          >
            <MiniMap pannable zoomable nodeStrokeWidth={3} />
            <Background color="#cbd5e1" gap={20} size={1.2} />
            <Controls showInteractive={false} position="bottom-right" />
          </ReactFlow>
        </div>
      </div>
    </div>
  );
}
