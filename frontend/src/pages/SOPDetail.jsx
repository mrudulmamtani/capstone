import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import { useDemoRole } from "../components/DemoRoleProvider.jsx";
import { sopApi } from "../lib/api.js";

export default function SOPDetail() {
  const { id } = useParams();
  const { role } = useDemoRole();
  const [sop, setSop] = useState(null);
  const [message, setMessage] = useState(null);

  const canPublish = role === "admin" || role === "engineer";

  useEffect(() => {
    sopApi.get(id).then(setSop);
  }, [id]);

  if (!sop) return <div className="text-ink-400">Loading...</div>;

  async function publish() {
    try {
      setSop(await sopApi.publish(sop.id));
      setMessage("SOP published successfully.");
    } catch (error) {
      setMessage(error?.response?.data?.detail || "Publish failed for this role.");
    }
  }

  return (
    <div className="grid lg:grid-cols-[1fr_380px] gap-6">
      <div className="space-y-6">
        <header>
          <div className="text-xs text-ink-500">{sop.station}</div>
          <h1 className="text-2xl">{sop.title}</h1>
          <div className="mt-2 flex gap-2 items-center">
            <span className={`pill-${sop.status}`}>{sop.status}</span>
            {sop.status !== "published" && canPublish && (
              <button onClick={publish} className="btn-primary">
                Publish
              </button>
            )}
          </div>
          {message && <div className="mt-3 text-sm text-ink-500">{message}</div>}
        </header>

        <div className="card p-6 prose max-w-none">
          {sop.rendered_markdown ? (
            <ReactMarkdown>{sop.rendered_markdown}</ReactMarkdown>
          ) : (
            <div className="text-ink-400">No rendered markdown - SOP is empty.</div>
          )}
        </div>
      </div>

      <aside className="card p-5 space-y-3 self-start sticky top-6">
        <div className="text-sm text-ink-500">Steps ({sop.steps.length})</div>
        <ol className="space-y-2">
          {sop.steps.map((step) => (
            <li key={step.id} className="flex items-start gap-3 py-2 border-b border-ink-100 last:border-0">
              <div className="w-7 h-7 rounded-full bg-ink-900 text-white grid place-items-center text-xs font-bold">
                {step.step_index + 1}
              </div>
              <div className="flex-1">
                <div className="font-medium text-sm">{step.title}</div>
                <div className="text-xs text-ink-500">
                  {step.action_label} - target {step.target_duration_s.toFixed(1)}s - +/-
                  {step.tolerance_s.toFixed(1)}s
                </div>
              </div>
            </li>
          ))}
        </ol>
        <div className="text-xs text-ink-400">
          Target cycle: <strong>{sop.target_cycle_time_s?.toFixed(1) || "-"}s</strong>
        </div>
      </aside>
    </div>
  );
}
