import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";
import { Toaster } from "react-hot-toast";

import Recruitment from "./pages/Recruitment";
import ResumeReviewer from "./pages/ResumeReviewer";

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

              <Route
                path="*"
                element={
                  <Navigate
                    to="/resume-reviewer"
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
