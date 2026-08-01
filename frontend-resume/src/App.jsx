import {
  BrowserRouter,
  Navigate,
  Outlet,
  Route,
  Routes,
} from "react-router";
import { Toaster } from "react-hot-toast";

import {
  AuthProvider,
} from "./auth/AuthContext";
import ProtectedRoute from "./components/auth/ProtectedRoute";
import Sidebar from "./components/layout/Sidebar";
import TopBar from "./components/layout/TopBar";
import ForgotPassword from "./pages/ForgotPassword";
import Login from "./pages/Login";
import Recruitment from "./pages/Recruitment";
import Register from "./pages/Register";
import ResetPassword from "./pages/ResetPassword";
import ResumeReviewer from "./pages/ResumeReviewer";

function ProtectedLayout() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-50">
      <Sidebar />

      <main className="ml-72 min-h-screen">
        <TopBar />

        <section className="p-8">
          <Outlet />
        </section>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route
            path="/login"
            element={<Login />}
          />

          <Route
            path="/register"
            element={<Register />}
          />

          <Route
            path="/forgot-password"
            element={<ForgotPassword />}
          />

          <Route
            path="/reset-password"
            element={<ResetPassword />}
          />

          <Route
            element={<ProtectedRoute />}
          >
            <Route
              element={<ProtectedLayout />}
            >
              <Route
                index
                element={
                  <Navigate
                    to="/resume-reviewer"
                    replace
                  />
                }
              />

              <Route
                path="/resume-reviewer"
                element={<ResumeReviewer />}
              />

              <Route
                path="/recruitment"
                element={<Recruitment />}
              />
            </Route>
          </Route>

          <Route
            path="*"
            element={
              <Navigate
                to="/"
                replace
              />
            }
          />
        </Routes>

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
      </AuthProvider>
    </BrowserRouter>
  );
}
