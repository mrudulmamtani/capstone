import { NavLink, Outlet } from "react-router-dom";
import { BookOpen, ChartLine, Factory, Siren, Workflow } from "lucide-react";
import { useDemoRole } from "./DemoRoleProvider.jsx";
import { DEMO_ROLES, getDemoRoleMeta } from "../lib/demoRole.js";

const NAV = [
  { to: "/", label: "Overview", icon: ChartLine, end: true },
  { to: "/sops", label: "SOP Library", icon: BookOpen },
  { to: "/sessions", label: "Sessions", icon: Workflow },
  { to: "/alerts", label: "Alerts", icon: Siren },
];

export default function Layout() {
  const { role, setRole } = useDemoRole();
  const activeRole = getDemoRoleMeta(role);

  return (
    <div className="min-h-screen grid grid-cols-[240px_1fr]">
      <aside className="bg-ink-900 text-white p-5 flex flex-col gap-1">
        <div className="flex items-center gap-2 mb-8">
          <Factory className="text-accent" size={26} />
          <div>
            <div className="font-bold tracking-tight">VISION-SOP</div>
            <div className="text-xs text-ink-300">Auto-SOP and compliance</div>
          </div>
        </div>

        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm ${
                isActive
                  ? "bg-ink-700 text-white"
                  : "text-ink-300 hover:bg-ink-800 hover:text-white"
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}

        <div className="mt-auto text-xs text-ink-300 space-y-2">
          <div>Capstone demo mode</div>
          <div>Mrudul Mamtani - 22BCE3721</div>
        </div>
      </aside>

      <main className="p-8 overflow-y-auto">
        <div className="card p-4 mb-6 flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <div className="text-xs uppercase tracking-[0.18em] text-ink-400">Capstone demo</div>
            <div className="text-lg font-semibold">Preloaded results - no sign-in and no manual uploads</div>
            <div className="text-sm text-ink-500">Viewing as {activeRole.label}. {activeRole.blurb}.</div>
          </div>
          <div className="flex flex-wrap gap-2">
            {DEMO_ROLES.map((item) => (
              <button
                key={item.value}
                type="button"
                onClick={() => setRole(item.value)}
                className={`px-4 py-2 rounded-lg text-sm font-medium border transition ${
                  item.value === role
                    ? "bg-ink-900 text-white border-ink-900"
                    : "bg-white text-ink-700 border-ink-200 hover:border-ink-400"
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>

        <Outlet />
      </main>
    </div>
  );
}
