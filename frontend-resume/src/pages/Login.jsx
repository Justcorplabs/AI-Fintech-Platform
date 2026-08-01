import {
  LoaderCircle,
  LogIn,
  ScanSearch,
} from "lucide-react";
import {
  useEffect,
  useState,
} from "react";
import {
  useLocation,
  useNavigate,
} from "react-router";
import toast from "react-hot-toast";

import {
  useAuth,
} from "../auth/AuthContext";

function getErrorMessage(error) {
  const detail =
    error.response?.data?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => item.msg)
      .filter(Boolean)
      .join(", ");
  }

  return (
    "Login failed. Check your email " +
    "and password."
  );
}

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();

  const {
    user,
    loading,
    login,
  } = useAuth();

  const [form, setForm] = useState({
    email: "",
    password: "",
  });

  const [submitting, setSubmitting] =
    useState(false);

  const destination =
    location.state?.from?.pathname ||
    "/resume-reviewer";

  useEffect(() => {
    if (!loading && user) {
      navigate(
        destination,
        {
          replace: true,
        }
      );
    }
  }, [
    destination,
    loading,
    navigate,
    user,
  ]);

  function updateField(event) {
    const {
      name,
      value,
    } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);

    try {
      await login({
        email: form.email.trim(),
        password: form.password,
      });

      toast.success(
        "Signed in successfully."
      );

      navigate(
        destination,
        {
          replace: true,
        }
      );
    } catch (error) {
      toast.error(
        getErrorMessage(error)
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-6 text-slate-50">
      <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-8 shadow-2xl">
        <div className="mb-8 flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-violet-500/15 text-violet-300">
            <ScanSearch size={26} />
          </div>

          <div>
            <h1 className="text-xl font-semibold">
              JustCorp Talent AI
            </h1>

            <p className="text-sm text-slate-400">
              Resume Intelligence
            </p>
          </div>
        </div>

        <h2 className="text-2xl font-semibold">
          Sign in
        </h2>

        <p className="mt-2 text-sm text-slate-400">
          Use your JustCorp account to access
          resume review and recruitment tools.
        </p>

        <form
          onSubmit={handleSubmit}
          className="mt-8 space-y-5"
        >
          <div>
            <label
              htmlFor="email"
              className="mb-2 block text-sm font-medium text-slate-300"
            >
              Email address
            </label>

            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={form.email}
              onChange={updateField}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 outline-none transition focus:border-violet-500"
              placeholder="name@example.com"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="mb-2 block text-sm font-medium text-slate-300"
            >
              Password
            </label>

            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              value={form.password}
              onChange={updateField}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 outline-none transition focus:border-violet-500"
              placeholder="Enter your password"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-violet-600 px-4 py-3 font-semibold text-white transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? (
              <>
                <LoaderCircle
                  size={19}
                  className="animate-spin"
                />
                Signing in...
              </>
            ) : (
              <>
                <LogIn size={19} />
                Sign in
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
