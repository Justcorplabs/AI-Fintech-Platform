import { useEffect, useMemo, useState } from "react";
import { fraudAPI } from "../services/fraudApi";
import {
  BarChart3,
  CreditCard,
  DollarSign,
  Store,
  TrendingUp,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function Analytics() {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);

  async function loadAnalytics() {
    try {
      setLoading(true);
      const res = await fraudAPI.getTransactions({ limit: 300 });
      setTransactions(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAnalytics();
  }, []);

  const analytics = useMemo(() => {
    const total = transactions.length;
    const highRisk = transactions.filter((tx) => (tx.fraud_score || 0) >= 0.6);
    const mediumRisk = transactions.filter(
      (tx) => (tx.fraud_score || 0) >= 0.4 && (tx.fraud_score || 0) < 0.6
    );
    const lowRisk = transactions.filter((tx) => (tx.fraud_score || 0) < 0.4);

    const totalAmount = transactions.reduce(
      (sum, tx) => sum + Number(tx.amount || 0),
      0
    );

    const highRiskAmount = highRisk.reduce(
      (sum, tx) => sum + Number(tx.amount || 0),
      0
    );

    const riskDistribution = [
      { name: "Low Risk", value: lowRisk.length },
      { name: "Medium Risk", value: mediumRisk.length },
      { name: "High Risk", value: highRisk.length },
    ];

    const amountBands = [
      { band: "0-100", count: transactions.filter((tx) => tx.amount <= 100).length },
      {
        band: "101-500",
        count: transactions.filter((tx) => tx.amount > 100 && tx.amount <= 500).length,
      },
      {
        band: "501-1000",
        count: transactions.filter((tx) => tx.amount > 500 && tx.amount <= 1000).length,
      },
      {
        band: "1001-5000",
        count: transactions.filter((tx) => tx.amount > 1000 && tx.amount <= 5000).length,
      },
      { band: "5000+", count: transactions.filter((tx) => tx.amount > 5000).length },
    ];

    const riskTrend = transactions
      .slice()
      .reverse()
      .map((tx, index) => ({
        name: `TX-${index + 1}`,
        risk: Number(((tx.fraud_score || 0) * 100).toFixed(2)),
      }));

    return {
      total,
      highRisk,
      mediumRisk,
      lowRisk,
      totalAmount,
      highRiskAmount,
      riskDistribution,
      amountBands,
      riskTrend,
    };
  }, [transactions]);

  if (loading) {
    return <p className="text-slate-400">Loading analytics...</p>;
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-white">Fraud Analytics</h1>
        <p className="mt-1 text-slate-400">
          Management-level fraud intelligence, risk trends, and transaction behaviour analysis.
        </p>
      </div>

      <div className="mb-6 grid grid-cols-4 gap-5">
        <AnalyticsCard
          title="Transactions Analysed"
          value={analytics.total}
          icon={BarChart3}
          subtitle="Loaded from fraud database"
        />

        <AnalyticsCard
          title="High Risk Cases"
          value={analytics.highRisk.length}
          icon={TrendingUp}
          subtitle="Risk score above 60%"
          danger
        />

        <AnalyticsCard
          title="Total Value Scored"
          value={`USD ${analytics.totalAmount.toFixed(0)}`}
          icon={DollarSign}
          subtitle="Total transaction exposure"
        />

        <AnalyticsCard
          title="High-Risk Exposure"
          value={`USD ${analytics.highRiskAmount.toFixed(0)}`}
          icon={CreditCard}
          subtitle="Potential value requiring review"
          danger
        />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <ChartCard
          title="Risk Trend"
          subtitle="Fraud probability across recent transactions"
          icon={TrendingUp}
        >
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analytics.riskTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="name" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="risk" fill="#38bdf8" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Risk Distribution"
          subtitle="Low, medium, and high-risk case mix"
          icon={CreditCard}
        >
          <div className="grid grid-cols-[1.2fr_1fr] items-center gap-6">
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={analytics.riskDistribution}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={65}
                    outerRadius={105}
                    paddingAngle={5}
                  >
                    <Cell fill="#22c55e" />
                    <Cell fill="#eab308" />
                    <Cell fill="#ef4444" />
                  </Pie>
                  <Tooltip contentStyle={tooltipStyle} />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="space-y-3">
              <Legend label="Low" value={analytics.lowRisk.length} color="bg-emerald-500" />
              <Legend label="Medium" value={analytics.mediumRisk.length} color="bg-yellow-500" />
              <Legend label="High" value={analytics.highRisk.length} color="bg-red-500" />
            </div>
          </div>
        </ChartCard>

        <ChartCard
          title="Transaction Amount Bands"
          subtitle="Transaction volume by value range"
          icon={DollarSign}
        >
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analytics.amountBands}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="band" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="count" fill="#22c55e" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Fraud Operations Insight"
          subtitle="Current operational interpretation"
          icon={Store}
        >
          <div className="space-y-4 text-slate-300">
            <Insight
              title="Main Risk Pattern"
              text="High-risk cases are concentrated among demo fraud profiles and flagged transactions requiring analyst review."
            />
            <Insight
              title="Operational Priority"
              text="Fraud analysts should prioritise high-risk flagged cases before reviewing medium-risk pending transactions."
            />
            <Insight
              title="Model Explainability"
              text="Each reviewed case includes SHAP-based explanations, analyst notes, and a persistent audit timeline."
            />
            <Insight
              title="Live Monitoring"
              text="WebSocket monitoring is active, allowing new fraud alerts to update the dashboard without manual refresh."
            />
          </div>
        </ChartCard>
      </div>
    </div>
  );
}

const tooltipStyle = {
  background: "#020617",
  border: "1px solid #1e293b",
  color: "#f8fafc",
};

function AnalyticsCard({ title, value, subtitle, icon: Icon, danger }) {
  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
      <div className="mb-5 flex items-center justify-between">
        <p className="text-sm text-slate-400">{title}</p>
        <Icon size={22} className={danger ? "text-red-400" : "text-sky-400"} />
      </div>
      <h2 className="break-words text-3xl font-semibold text-white">{value}</h2>
      <p className="mt-2 text-sm text-slate-500">{subtitle}</p>
    </div>
  );
}

function ChartCard({ title, subtitle, icon: Icon, children }) {
  return (
    <div className="min-h-[430px] rounded-3xl border border-slate-800 bg-slate-900 p-6">
      <div className="mb-5 flex items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-white">{title}</h2>
          <p className="text-sm text-slate-400">{subtitle}</p>
        </div>
        <Icon className="shrink-0 text-sky-400" />
      </div>
      {children}
    </div>
  );
}

function Legend({ label, value, color }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
      <div className="flex items-center gap-2">
        <span className={`h-3 w-3 rounded-full ${color}`} />
        <span className="text-sm text-slate-400">{label}</span>
      </div>
      <p className="mt-1 text-2xl font-semibold text-white">{value}</p>
    </div>
  );
}

function Insight({ title, text }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
      <p className="font-semibold text-white">{title}</p>
      <p className="mt-1 text-sm text-slate-400">{text}</p>
    </div>
  );
}
