import {
  Bell,
  Brain,
  LogOut,
  UserCircle,
} from "lucide-react";

import {
  useAuth,
} from "../../auth/AuthContext";

function formatRole(role) {
  if (!role) {
    return "Authenticated User";
  }

  return role
    .replaceAll("_", " ")
    .replace(
      /\b\w/g,
      (letter) => letter.toUpperCase()
    );
}

export default function TopBar() {
  const {
    user,
    logout,
  } = useAuth();

  const displayName =
    user?.full_name ||
    user?.email ||
    "Authenticated User";

  return (
    <header className="sticky top-0 z-20 flex h-20 items-center justify-between border-b border-slate-800 bg-slate-950/90 px-8 backdrop-blur">
      <div>
        <h2 className="text-xl font-semibold text-white">
          JustCorp Resume Intelligence
        </h2>

        <p className="mt-1 text-sm text-slate-400">
          AI-assisted recruitment and resume
          review workspace
        </p>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 rounded-full border border-sky-500/30 bg-sky-500/10 px-4 py-2 text-sm font-semibold text-sky-300">
          <Brain size={16} />
          AI Review Ready
        </div>

        <div className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-4 py-2 text-sm font-semibold text-emerald-400">
          System Healthy
        </div>

        <button
          type="button"
          aria-label="Notifications"
          className="rounded-full border border-slate-700 bg-slate-900 p-2 text-slate-300 hover:text-white"
        >
          <Bell size={20} />
        </button>

        <div className="flex items-center gap-3 rounded-full border border-slate-700 bg-slate-900 px-3 py-2">
          <UserCircle
            size={24}
            className="text-sky-400"
          />

          <div className="max-w-44">
            <p className="truncate text-sm font-semibold text-white">
              {displayName}
            </p>

            <p className="text-xs text-slate-400">
              {formatRole(user?.role)}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={logout}
          className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-300 transition hover:border-red-500/40 hover:text-red-300"
        >
          <LogOut size={17} />
          Logout
        </button>
      </div>
    </header>
  );
}
