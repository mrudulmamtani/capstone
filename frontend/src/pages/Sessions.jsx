import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { PlayCircle } from "lucide-react";
import { DEMO_VIDEO_LIBRARY } from "../lib/demoAssets.js";
import { sessionApi, sopApi } from "../lib/api.js";

export default function Sessions() {
  const [rows, setRows] = useState([]);
  const [sops, setSops] = useState([]);
  const [form, setForm] = useState({
    sop_id: "",
    operator_ref: "OP-DEMO",
    source_uri: "/app/data/videos/final-assembly-run-delayed.mp4",
  });
  const [msg, setMsg] = useState(null);

  async function refresh() {
    setRows(await sessionApi.list());
  }

  useEffect(() => {
    refresh();
    sopApi.list().then((items) => {
      setSops(items);
      const defaultSop = items.find((item) => item.title === "Final Assembly QA");
      if (defaultSop) {
        setForm((current) => ({ ...current, sop_id: current.sop_id || defaultSop.id }));
      }
    });
  }, []);

  const sopMap = useMemo(() => Object.fromEntries(sops.map((sop) => [sop.id, sop])), [sops]);

  async function create(e) {
    e.preventDefault();
    setMsg(null);
    try {
      const session = await sessionApi.create(form);
      setMsg(`Started session ${session.id.slice(0, 8)}. Open it to see live status, heatmaps, and deviations.`);
      await refresh();
    } catch (error) {
      setMsg(error?.response?.data?.detail || "Failed to queue session");
    }
  }

  function chooseDemo(asset) {
    const matchingSop = sops.find((sop) => sop.title === asset.sopTitle);
    setForm((current) => ({
      ...current,
      sop_id: matchingSop?.id || current.sop_id,
      source_uri: asset.serverPath,
      operator_ref: `OP-${asset.station.replace(/\D/g, "") || "DEMO"}`,
    }));
    setMsg(`Loaded ${asset.title} into the monitoring session form.`);
  }

  return (
    <div className="space-y-6">
      <header>
        <div className="text-sm text-ink-500">Phase 3 · Continuous compliance</div>
        <h1 className="text-2xl">Monitoring Sessions</h1>
        <div className="text-sm text-ink-500 mt-1">
          Launch a demo monitoring run or open a seeded run to show Golden-Batch comparison, alerts, and ergonomic heatmaps.
        </div>
      </header>

      <div className="grid lg:grid-cols-[1.1fr_1fr] gap-4">
        <form onSubmit={create} className="card p-5 grid md:grid-cols-4 gap-3 self-start">
          <div className="md:col-span-4 flex items-center gap-2 text-sm font-medium text-ink-700">
            <PlayCircle size={16} className="text-accent" /> Start monitoring from a demo video
          </div>
          <select
            required
            className="border border-ink-200 rounded-lg px-3 py-2"
            value={form.sop_id}
            onChange={(e) => setForm({ ...form, sop_id: e.target.value })}
          >
            <option value="">— Select SOP —</option>
            {sops.map((sop) => (
              <option key={sop.id} value={sop.id}>
                {sop.title} ({sop.station})
              </option>
            ))}
          </select>
          <input
            className="border border-ink-200 rounded-lg px-3 py-2"
            placeholder="Operator ref"
            value={form.operator_ref}
            onChange={(e) => setForm({ ...form, operator_ref: e.target.value })}
          />
          <input
            required
            className="border border-ink-200 rounded-lg px-3 py-2 md:col-span-2 font-mono text-xs"
            placeholder="/app/data/videos/demo.mp4"
            value={form.source_uri}
            onChange={(e) => setForm({ ...form, source_uri: e.target.value })}
          />
          <button className="btn-accent justify-center md:col-span-4">
            <PlayCircle size={16} /> Start session
          </button>
          {msg && <div className="md:col-span-4 text-sm text-ink-600">{msg}</div>}
        </form>

        <div className="grid sm:grid-cols-2 gap-4">
          {DEMO_VIDEO_LIBRARY.map((asset) => (
            <button
              key={asset.id}
              type="button"
              onClick={() => chooseDemo(asset)}
              className="card p-4 text-left hover:shadow-md transition"
            >
              <video className="w-full rounded-lg bg-ink-900 mb-3" src={asset.publicUrl} muted loop autoPlay playsInline />
              <div className="text-xs text-ink-500">{asset.station}</div>
              <div className="font-semibold">{asset.title}</div>
              <div className="text-sm text-ink-600 mt-1">{asset.description}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="card p-5">
        <table className="w-full text-sm">
          <thead className="text-left text-ink-500 border-b border-ink-100">
            <tr>
              <th className="py-2">Session</th>
              <th>SOP</th>
              <th>Operator</th>
              <th>Status</th>
              <th>Cycle</th>
              <th>Deviation</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-b border-ink-100 last:border-0">
                <td className="py-2 font-mono text-xs">{row.id.slice(0, 8)}...</td>
                <td>{row.sop_id ? sopMap[row.sop_id]?.title || row.sop_id.slice(0, 8) : "-"}</td>
                <td>{row.operator_ref || "-"}</td>
                <td>{row.status}</td>
                <td>{row.cycle_time_s?.toFixed(1) || "-"}</td>
                <td>{((row.deviation_score || 0) * 100).toFixed(1)}%</td>
                <td className="text-right space-x-3">
                  <Link className="text-accent hover:underline" to={`/sessions/${row.id}`}>
                    View
                  </Link>
                  <Link className="text-accent hover:underline" to={`/monitor/${row.id}`}>
                    Live
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
