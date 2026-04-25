export default function SeverityPill({ severity }) {
  const cls =
    severity === "critical"
      ? "sev-critical"
      : severity === "warning"
      ? "sev-warning"
      : "sev-info";
  return <span className={cls}>{severity}</span>;
}
