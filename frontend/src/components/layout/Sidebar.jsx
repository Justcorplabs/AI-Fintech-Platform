import { NavLink } from "react-router-dom";
import {
  BarChart3,
  ShieldCheck,
  CreditCard,
  Activity,
  LineChart,
  FileText,
  Settings,
  Radar,
  Users,
  FileSearch,
} from "lucide-react";

const sections = [
  {
    title: "Fraud Intelligence",
    items: [
      { to: "/dashboard", label: "Dashboard", icon: BarChart3 },
      { to: "/fraud", label: "Fraud Detection", icon: ShieldCheck },
      { to: "/transactions", label: "Review Queue", icon: CreditCard },
      { to: "/analytics", label: "Analytics", icon: LineChart },
      { to: "/reports", label: "Reports", icon: FileText },
      { to: "/drift", label: "Drift Monitor", icon: Radar },
    ],
  },
  {
    title: "Recruitment AI",
    items: [
      { to: "/recruitment", label: "Candidate Ranking", icon: Users },
      { to: "/resume-reviewer", label: "Resume Reviewer", icon: FileSearch },
    ],
  },
  {
    title: "System",
    items: [{ to: "/settings", label: "Settings", icon: Settings }],
  },
];

export default function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 z-30 flex h-screen w-72 flex-col border-r border-slate-800 bg-slate-950 px-5 py-6">
      <div className="shrink-0">
        <h1 className="text-3xl font-bold tracking-tight text-white">
          SentinelAI
        </h1>
        <p className="mt-2 text-sm text-slate-400">
          Enterprise AI Intelligence
        </p>
      </div>

      <nav className="mt-8 flex-1 space-y-7 overflow-y-auto pr-1">
        {sections.map((section) => (
          <div key={section.title}>
            <p className="mb-3 px-2 text-xs font-bold uppercase tracking-wider text-slate-500">
              {section.title}
            </p>

            <div className="space-y-2">
              {section.items.map((item) => {
                const Icon = item.icon;

                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) =>
                      `flex items-center gap-3 rounded-2xl border px-4 py-3 text-sm font-semibold transition ${
                        isActive
                          ? "border-sky-400 bg-sky-500 text-white shadow-lg shadow-sky-500/20"
                          : "border-slate-800 bg-slate-900 text-slate-300 hover:border-sky-500/60 hover:bg-slate-800 hover:text-white"
                      }`
                    }
                  >
                    <Icon size={18} />
                    <span>{item.label}</span>
                  </NavLink>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="mt-5 shrink-0 rounded-2xl border border-slate-800 bg-slate-900 p-4">
        <p className="text-xs uppercase tracking-wider text-slate-500">
          Active Suite
        </p>
        <p className="mt-1 text-sm font-semibold text-white">
          Fraud + Recruitment AI
        </p>

        <div className="mt-3 flex items-center gap-2 text-sm text-emerald-400">
          <Activity size={15} />
          <span>System Healthy</span>
        </div>
      </div>
    </aside>
  );
}