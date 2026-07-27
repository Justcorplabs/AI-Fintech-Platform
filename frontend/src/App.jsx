import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Dashboard from "./pages/Dashboard";
import Fraud from "./pages/Fraud";
import Transactions from "./pages/Transactions";
import Investigation from "./pages/Investigation";
import Analytics from "./pages/Analytics";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";
import DriftMonitoring from "./pages/DriftMonitoring";
import Recruitment from "./pages/Recruitment";
import ResumeReviewer from "./pages/ResumeReviewer";

import Sidebar from "./components/layout/Sidebar";
import TopBar from "./components/layout/TopBar";
import { Toaster } from "react-hot-toast";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-950 text-slate-50">
        <Sidebar />

        <main className="ml-72 min-h-screen">
          <TopBar />

          <section className="p-8">
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/fraud" element={<Fraud />} />
              <Route path="/transactions" element={<Transactions />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/drift" element={<DriftMonitoring />} />
              <Route path="/recruitment" element={<Recruitment />} />
              <Route path="/resume-reviewer" element={<ResumeReviewer />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/investigation/:id" element={<Investigation />} />
            </Routes>
          </section>
        </main>

        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: "#0f172a",
              color: "#f8fafc",
              border: "1px solid #1e293b",
            },
          }}
        />
      </div>
    </BrowserRouter>
  );
}