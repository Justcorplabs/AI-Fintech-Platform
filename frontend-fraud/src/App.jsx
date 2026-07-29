import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";
import { Toaster } from "react-hot-toast";

import Analytics from "./pages/Analytics";
import Dashboard from "./pages/Dashboard";
import DriftMonitoring from "./pages/DriftMonitoring";
import Fraud from "./pages/Fraud";
import Investigation from "./pages/Investigation";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";
import Transactions from "./pages/Transactions";

import Sidebar from "./components/layout/Sidebar";
import TopBar from "./components/layout/TopBar";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-950 text-slate-50">
        <Sidebar />

        <main className="ml-72 min-h-screen">
          <TopBar />

          <section className="p-8">
            <Routes>
              <Route
                path="/"
                element={
                  <Navigate
                    to="/dashboard"
                    replace
                  />
                }
              />

              <Route
                path="/dashboard"
                element={<Dashboard />}
              />

              <Route
                path="/fraud"
                element={<Fraud />}
              />

              <Route
                path="/transactions"
                element={<Transactions />}
              />

              <Route
                path="/investigation/:id"
                element={<Investigation />}
              />

              <Route
                path="/analytics"
                element={<Analytics />}
              />

              <Route
                path="/reports"
                element={<Reports />}
              />

              <Route
                path="/drift"
                element={<DriftMonitoring />}
              />

              <Route
                path="/settings"
                element={<Settings />}
              />

              <Route
                path="*"
                element={
                  <Navigate
                    to="/dashboard"
                    replace
                  />
                }
              />
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
