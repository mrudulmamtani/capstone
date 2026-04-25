export default function StatCard({ label, value, hint, accent = false }) {
  return (
    <div className={`card p-5 ${accent ? "bg-ink-900 text-white border-ink-900" : ""}`}>
      <div className={`text-sm ${accent ? "text-ink-300" : "text-ink-500"}`}>{label}</div>
      <div className="text-3xl font-bold mt-1">{value}</div>
      {hint && (
        <div className={`text-xs mt-2 ${accent ? "text-ink-300" : "text-ink-400"}`}>
          {hint}
        </div>
      )}
    </div>
  );
}
