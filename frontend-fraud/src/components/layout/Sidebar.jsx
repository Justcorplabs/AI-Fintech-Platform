import {
  Activity,
  BarChart3,
  FileText,
  Gauge,
  LayoutDashboard,
  ListChecks,
  Settings,
  ShieldAlert,
} from "lucide-react";
import { NavLink } from "react-router";

const navigationItems = [
  {
    label: "Dashboard",
    path: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Fraud Detection",
    path: "/fraud",
    icon: ShieldAlert,
  },
  {
    label: "Transactions",
    path: "/transactions",
    icon: ListChecks,
  },
  {
    label: "Analytics",
    path: "/analytics",
    icon: BarChart3,
  },
  {
    label: "Reports",
    path: "/reports",
    icon: FileText,
  },
  {
    label: "Model Drift",
    path: "/drift",
    icon: Activity,
  },
  {
    label: "Settings",
    path: "/settings",
    icon: Settings,
  },
];

function navigationClass({ isActive }) {
  const baseClasses =
    "flex items-center gap-3 rounded-lg px-4 py-3 " +
    "text-sm font-medium transition-colors";

  if (isActive) {
    return (
      baseClasses +
      " bg-cyan-500/15 text-cyan-300 " +
      "border border-cyan-500/30"
    );
  }

  return (
    baseClasses +
    " text-slate-400 hover:bg-slate-800 " +
    "hover:text-slate-100"
  );
}

export default function Sidebar() {
  return (
    <aside
      className="
        fixed inset-y-0 left-0 z-40 w-72
        border-r border-slate-800
        bg-slate-950 px-5 py-6
      "
    >
      <div className="mb-8 flex items-center gap-3 px-3">
        <div
          className="
            flex h-11 w-11 items-center justify-center
            rounded-xl bg-cyan-500/15 text-cyan-300
          "
        >
          <Gauge size={24} />
        </div>

        <div>
          <p className="font-semibold text-slate-100">
            JustCorp Sentinel
          </p>

          <p className="text-xs text-slate-500">
            Fraud Intelligence
          </p>
        </div>
      </div>

      <nav className="space-y-2">
        {navigationItems.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={navigationClass}
            >
              <Icon size={19} />

              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
