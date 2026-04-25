import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Film, Plus, Sparkles, Upload } from "lucide-react";
import { DEMO_VIDEO_LIBRARY } from "../lib/demoAssets.js";
import { sopApi } from "../lib/api.js";

export default function SOPLibrary() {
  const [sops, setSops] = useState([]);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    title: "Final Assembly QA",
    station: "Station 1",
    source_video_path: "/app/data/videos/final-assembly-reference.mp4",
  });
  const [msg, setMsg] = useState(null);

  async function refresh() {
    setSops(await sopApi.list());
  }

  useEffect(() => {
    refresh();
  }, []);

  async function onUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    setMsg(null);
    try {
      const result = await sopApi.uploadVideo(file);
      setForm((current) => ({ ...current, source_video_path: result.path }));
      setMsg(`Uploaded demo video to ${result.path}`);
    } catch (error) {
      setMsg(error?.response?.data?.detail || "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function onGenerate(e) {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    try {
      const sop = await sopApi.generate(form);
      setMsg(`Generated SOP ${sop.title} with ${sop.steps.length} detected steps.`);
      await refresh();
    } catch (error) {
      setMsg(error?.response?.data?.detail || "Generation failed");
    } finally {
      setBusy(false);
    }
  }

  function loadDemo(asset) {
    setForm({
      title: asset.sopTitle,
      station: asset.station,
      source_video_path: asset.serverPath,
    });
    setMsg(`Loaded ${asset.title} into the SOP generator.`);
  }

  return (
    <div className="space-y-6">
      <header>
        <div className="text-sm text-ink-500">Phase 1 · Observation & digitization</div>
        <h1 className="text-2xl">SOP Library</h1>
        <div className="text-sm text-ink-500 mt-1">
          Use the built-in demo clips to show reference-video ingestion, SOP generation, and downstream analytics.
        </div>
      </header>

      <div className="grid lg:grid-cols-[1.25fr_1fr] gap-4">
        <form onSubmit={onGenerate} className="card p-5 grid md:grid-cols-4 gap-3">
          <div className="md:col-span-4 flex items-center gap-2 text-sm font-medium text-ink-700">
            <Sparkles size={16} className="text-accent" /> Generate SOP from video
          </div>
          <input
            placeholder="SOP title"
            className="border border-ink-200 rounded-lg px-3 py-2 md:col-span-2"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            required
          />
          <input
            placeholder="Station"
            className="border border-ink-200 rounded-lg px-3 py-2"
            value={form.station}
            onChange={(e) => setForm({ ...form, station: e.target.value })}
            required
          />
          <label className="btn-ghost border border-dashed border-ink-300 justify-center cursor-pointer">
            <Upload size={16} />
            {busy ? "Uploading..." : "Upload video"}
            <input type="file" accept="video/*" className="hidden" onChange={onUpload} />
          </label>
          <input
            readOnly
            placeholder="Source video path"
            className="border border-ink-200 rounded-lg px-3 py-2 md:col-span-3 font-mono text-xs bg-ink-50"
            value={form.source_video_path}
          />
          <button disabled={busy || !form.source_video_path} className="btn-accent justify-center">
            <Plus size={16} /> Generate SOP
          </button>
          {msg && <div className="md:col-span-4 text-sm text-ink-600">{msg}</div>}
        </form>

        <div className="card p-5">
          <div className="flex items-center gap-2 mb-3">
            <Film size={16} className="text-accent" />
            <h2 className="text-lg">Demo video library</h2>
          </div>
          <div className="space-y-4 max-h-[460px] overflow-y-auto pr-1">
            {DEMO_VIDEO_LIBRARY.map((asset) => (
              <div key={asset.id} className="rounded-xl border border-ink-100 p-3 space-y-3">
                <video className="w-full rounded-lg bg-ink-900" src={asset.publicUrl} controls muted />
                <div>
                  <div className="text-xs text-ink-500">{asset.station}</div>
                  <div className="font-semibold">{asset.title}</div>
                  <div className="text-sm text-ink-600 mt-1">{asset.description}</div>
                </div>
                <div className="flex flex-wrap gap-2 text-xs">
                  {asset.tags.map((tag) => (
                    <span key={tag} className="badge bg-ink-100 text-ink-600">
                      {tag}
                    </span>
                  ))}
                </div>
                <button type="button" onClick={() => loadDemo(asset)} className="btn-primary w-full justify-center">
                  Use this demo clip
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
        {sops.map((sop) => (
          <Link
            key={sop.id}
            to={`/sops/${sop.id}`}
            className="card p-5 hover:shadow-md hover:-translate-y-0.5 transition"
          >
            <div className="flex items-start justify-between">
              <div>
                <div className="text-xs text-ink-500">{sop.station}</div>
                <div className="font-semibold text-lg">{sop.title}</div>
              </div>
              <span className={`pill-${sop.status}`}>{sop.status}</span>
            </div>
            <div className="mt-3 text-sm text-ink-500">
              {sop.steps.length} steps · target cycle {sop.target_cycle_time_s?.toFixed(1) || "-"}s
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
