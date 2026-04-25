import { useEffect, useState } from "react";
import { Check } from "lucide-react";
import { alertApi } from "../lib/api.js";
import SeverityPill from "../components/SeverityPill.jsx";

export default function Alerts() {
  const [rows, setRows] = useState([]);
  const [onlyOpen, setOnlyOpen] = useState(true);

  async function refresh() {
    setRows(await alertApi.list({ acknowledged: onlyOpen ? false : undefined }));
  }
  useEffect(() => {
    refresh();
  }, [onlyOpen]);

  async function ack(id) {
    await alertApi.ack(id);
    refresh();
  }

  return (
    <div className="space-y-6">
      <header className="flex items-center">
        <div>
          <div className="text-sm text-ink-500">Supervisor desk</div>
          <h1 className="text-2xl">Alerts</h1>
        </div>
        <label className="ml-auto text-sm flex items-center gap-2">
          <input
            type="checkbox"
            checked={onlyOpen}
            onChange={(e) => setOnlyOpen(e.target.checked)}
          />
          Only show open
        </label>
      </header>

      <div className="card divide-y divide-ink-100">
        {rows.length === 0 && <div className="p-6 text-ink-400">Nothing to review.</div>}
        {rows.map((a) => (
          <div key={a.id} className="p-4 flex items-start gap-4">
            <SeverityPill severity={a.severity} />
            <div className="flex-1">
              <div className="font-medium">{a.title}</div>
              <div className="text-sm text-ink-600">{a.message}</div>
              <div className="text-xs text-ink-400 mt-1">
                session <span className="font-mono">{a.session_id.slice(0, 8)}</span> · rule {a.rule} · at {a.at_s.toFixed(1)}s
              </div>
            </div>
            {!a.acknowledged && (
              <button onClick={() => ack(a.id)} className="btn-ghost">
                <Check size={14} /> ack
              </button>
            )}
            {a.acknowledged && <span className="text-xs text-emerald-600">acknowledged</span>}
          </div>
        ))}
      </div>
    </div>
  );
}
