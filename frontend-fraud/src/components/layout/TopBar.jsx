import { useEffect, useState } from "react";
import { Bell, UserCircle, Brain } from "lucide-react";
import { fraudAPI } from "../../services/fraudApi";

export default function TopBar() {
  const [metadata, setMetadata] = useState(null);

  useEffect(() => {
    async function loadMetadata() {
      try {
        const res = await fraudAPI.getModelMetadata();
        setMetadata(res.data);
      } catch (err) {
        console.error("Failed to load model metadata", err);
      }
    }

    loadMetadata();
  }, []);

  return (
    <header className="sticky top-0 z-20 flex h-20 items-center justify-between border-b border-slate-800 bg-slate-950/90 px-8 backdrop-blur">
      <div>
        <h2 className="text-xl font-semibold text-white">
          JustCorp Sentinel AI
        </h2>
        <p className="mt-1 text-sm text-slate-400">
          Production model active · {metadata?.model_version || "loading model..."} · SHAP enabled
        </p>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 rounded-full border border-sky-500/30 bg-sky-500/10 px-4 py-2 text-sm font-semibold text-sky-300">
          <Brain size={16} />
          ROC-AUC {metadata?.roc_auc ? `${(metadata.roc_auc * 100).toFixed(2)}%` : "—"}
        </div>

        <div className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-4 py-2 text-sm font-semibold text-emerald-400">
          ● System Healthy
        </div>

        <button className="rounded-full border border-slate-700 bg-slate-900 p-2 text-slate-300 hover:text-white">
          <Bell size={20} />
        </button>

        <div className="flex items-center gap-3 rounded-full border border-slate-700 bg-slate-900 px-3 py-2">
          <UserCircle size={24} className="text-sky-400" />
          <div>
            <p className="text-sm font-semibold text-white">Joseph</p>
            <p className="text-xs text-slate-400">Fraud Analyst</p>
          </div>
        </div>
      </div>
    </header>
  );
}
