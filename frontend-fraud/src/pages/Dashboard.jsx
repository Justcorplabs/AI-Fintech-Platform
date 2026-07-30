import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import toast from "react-hot-toast";
import { fraudAPI } from "../services/fraudApi";
import {
  AlertTriangle,
  Activity,
  ShieldCheck,
  TrendingUp,
  Database,
  Brain,
  Eye,
  Wifi,
  Zap,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

export default function Dashboard() {
  const navigate = useNavigate();

  const [stats, setStats] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [liveConnected, setLiveConnected] = useState(false);
  const [simulating, setSimulating] = useState(false);

  async function loadDashboard() {
    try {
      setLoading(true);

      const [statsRes, txRes, metadataRes] = await Promise.all([
        fraudAPI.getStats(),
        fraudAPI.getTransactions({ limit: 50 }),
        fraudAPI.getModelMetadata(),
      ]);

      setStats(statsRes.data);
      setTransactions(txRes.data);
      setMetadata(metadataRes.data);
    } catch (err) {
      console.error(err);
      toast.error("Failed to load dashboard data.");
    } finally {
      setLoading(false);
    }
  }

  async function simulateHighRiskAlert() {
    try {
      setSimulating(true);

      await fraudAPI.predict({
        transaction_ref: `LIVE-DEMO-${Date.now()}`,
        amount: 3500,
        currency: "USD",
        merchant_name: "Foreign Digital Merchant",
        merchant_category: "C",
        card_type: "credit",
        transaction_hour: 3,
        distance_from_home: 500,
        is_foreign: true,
        demo_profile: "high",
      });

      toast.success("Live high-risk alert generated.");
    } catch (err) {
      console.error(err);
      toast.error("Failed to simulate alert.");
    } finally {
      setSimulating(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(
      `${protocol}://${window.location.host}/api/v1/fraud/ws/alerts`
    );

    socket.onopen = () => {
      setLiveConnected(true);
      toast.success("Live fraud monitoring connected.");
    };

    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === "fraud_prediction") {
        const score = ((message.fraud_score || 0) * 100).toFixed(2);

        toast(
          message.is_fraud
            ? `🚨 High Risk Alert: ${message.transaction_ref} (${score}%)`
            : `✅ Transaction scored: ${message.transaction_ref} (${score}%)`
        );

        loadDashboard();
      }

      if (message.type === "transaction_review") {
        toast.success(
          `Case updated: ${message.transaction_ref} → ${message.status}`
        );

        loadDashboard();
      }
    };

    socket.onclose = () => setLiveConnected(false);
    socket.onerror = () => setLiveConnected(false);

    return () => socket.close();
  }, []);

  if (loading) {
    return <p className="text-slate-400">Loading dashboard...</p>;
  }

  const highRiskAlerts = transactions.filter((tx) => (tx.fraud_score || 0) >= 0.6);
  const lowRisk = transactions.filter((tx) => (tx.fraud_score || 0) < 0.4).length;
  const mediumRisk = transactions.filter(
    (tx) => (tx.fraud_score || 0) >= 0.4 && (tx.fraud_score || 0) < 0.6
  ).length;
  const highRisk = highRiskAlerts.length;

  const riskData = [
    { name: "Low Risk", value: lowRisk },
    { name: "Medium Risk", value: mediumRisk },
    { name: "High Risk", value: highRisk },
  ];

  const trendData = transactions
    .slice()
    .reverse()
    .map((tx, index) => ({
      name: `TX-${index + 1}`,
      risk: Number(((tx.fraud_score || 0) * 100).toFixed(2)),
    }));

  return (
    <div>
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">
            Sentinel AI Dashboard
          </h1>
          <p className="mt-1 text-slate-400">
            Executive fraud intelligence overview powered by the production AI model.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={simulateHighRiskAlert}
            disabled={simulating}
            className="flex items-center gap-2 rounded-full border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm font-bold text-red-400 hover:bg-red-500/20 disabled:opacity-60"
          >
            <Zap size={16} />
            {simulating ? "Generating..." : "Simulate High-Risk Alert"}
          </button>

          <div
            className={`flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-bold ${
              liveConnected
                ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                : "border-red-500/30 bg-red-500/10 text-red-400"
            }`}
          >
            <Wifi size={16} />
            {liveConnected ? "Live Monitoring Active" : "Live Monitoring Offline"}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-5">
        <StatCard
          title="Total Transactions"
          value={stats?.total_transactions ?? 0}
          icon={Database}
          subtitle="Scored by SentinelAI"
        />
        <StatCard
          title="Fraud Alerts"
          value={stats?.flagged_count ?? 0}
          icon={AlertTriangle}
          subtitle="Requires analyst review"
          danger
        />
        <StatCard
          title="Fraud Rate"
          value={`${stats?.fraud_rate ?? 0}%`}
          icon={TrendingUp}
          subtitle="Current detection ratio"
        />
        <StatCard
          title="Model Health"
          value={`${((metadata?.roc_auc || 0) * 100).toFixed(2)}%`}
          icon={Brain}
          subtitle={metadata?.model_version || "Champion model"}
          success
        />
      </div>

      <div className="mt-6 grid grid-cols-2 gap-6">
        <div className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-white">Fraud Risk Trend</h2>
              <p className="text-sm text-slate-400">Recent prediction scores over time</p>
            </div>
            <Activity className="text-sky-400" />
          </div>

          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <XAxis dataKey="name" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip
                  contentStyle={{
                    background: "#020617",
                    border: "1px solid #1e293b",
                    color: "#f8fafc",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="risk"
                  stroke="#38bdf8"
                  strokeWidth={3}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-white">Risk Distribution</h2>
              <p className="text-sm text-slate-400">Low, medium and high risk mix</p>
            </div>
            <ShieldCheck className="text-emerald-400" />
          </div>

          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={riskData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={70}
                  outerRadius={105}
                  paddingAngle={4}
                >
                  <Cell fill="#22c55e" />
                  <Cell fill="#eab308" />
                  <Cell fill="#ef4444" />
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: "#020617",
                    border: "1px solid #1e293b",
                    color: "#f8fafc",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-3 gap-3 text-sm">
            <RiskLegend label="Low" value={lowRisk} color="bg-emerald-500" />
            <RiskLegend label="Medium" value={mediumRisk} color="bg-yellow-500" />
            <RiskLegend label="High" value={highRisk} color="bg-red-500" />
          </div>
        </div>
      </div>

      <div className="mt-6 rounded-3xl border border-slate-800 bg-slate-900 p-6">
        <div className="mb-5 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">Recent High-Risk Alerts</h2>
            <p className="text-sm text-slate-400">Transactions requiring analyst attention</p>
          </div>
          <AlertTriangle className="text-red-400" />
        </div>

        {highRiskAlerts.length === 0 ? (
          <p className="text-slate-400">No high-risk alerts found.</p>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-slate-800">
            <table className="w-full border-collapse">
              <thead className="bg-slate-950 text-left text-sm text-slate-400">
                <tr>
                  <th className="p-4">Reference</th>
                  <th className="p-4">Amount</th>
                  <th className="p-4">Risk Score</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Action</th>
                </tr>
              </thead>
              <tbody>
                {highRiskAlerts.slice(0, 6).map((tx) => (
                  <tr key={tx.id} className="border-t border-slate-800 hover:bg-slate-800/40">
                    <td className="p-4 font-medium text-white">{tx.transaction_ref}</td>
                    <td className="p-4 text-slate-300">
                      {tx.currency} {tx.amount}
                    </td>
                    <td className="p-4 text-red-400">
                      {((tx.fraud_score || 0) * 100).toFixed(2)}%
                    </td>
                    <td className="p-4">
                      <span className="rounded-full bg-red-500/10 px-3 py-1 text-sm font-semibold text-red-400">
                        {tx.status}
                      </span>
                    </td>
                    <td className="p-4">
                      <button
                        onClick={() => navigate(`/investigation/${tx.id}`)}
                        className="flex items-center gap-2 rounded-xl border border-sky-500/40 bg-sky-500/10 px-3 py-2 text-sm font-bold text-sky-300 hover:bg-sky-500/20"
                      >
                        <Eye size={16} />
                        Review
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ title, value, subtitle, icon: Icon, danger, success }) {
  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
      <div className="mb-5 flex items-center justify-between">
        <p className="text-sm text-slate-400">{title}</p>
        <Icon
          size={22}
          className={
            danger ? "text-red-400" : success ? "text-emerald-400" : "text-sky-400"
          }
        />
      </div>

      <h2 className="text-4xl font-semibold text-white">{value}</h2>
      <p className="mt-2 break-words text-sm text-slate-500">{subtitle}</p>
    </div>
  );
}

function RiskLegend({ label, value, color }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950 p-3">
      <div className="flex items-center gap-2">
        <span className={`h-3 w-3 rounded-full ${color}`} />
        <span className="text-slate-400">{label}</span>
      </div>
      <p className="mt-1 text-xl font-semibold text-white">{value}</p>
    </div>
  );
}
