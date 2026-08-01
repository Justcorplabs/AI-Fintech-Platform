import {
  ArrowLeft,
  KeyRound,
  LoaderCircle,
  Mail,
  ScanSearch,
} from "lucide-react";
import {
  useState,
} from "react";
import {
  Link,
} from "react-router";
import toast from "react-hot-toast";

import {
  authAPI,
} from "../services/authApi";

const neutralMessage =
  "If an active account exists for this " +
  "email, password-reset instructions " +
  "have been created.";

function getErrorMessage(error) {
  const detail =
    error.response?.data?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  return (
    "The password-reset request could " +
    "not be processed. Try again later."
  );
}

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] =
    useState(false);

  const [submitted, setSubmitted] =
    useState(false);

  const [message, setMessage] =
    useState(neutralMessage);

  const [developmentResetUrl,
    setDevelopmentResetUrl] =
    useState(null);

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);

    try {
      const response =
        await authAPI.forgotPassword({
          email:
            email.trim().toLowerCase(),
        });

      setMessage(
        response.data?.message ||
        neutralMessage
      );

      setDevelopmentResetUrl(
        response.data?.reset_url || null
      );

      setSubmitted(true);

      toast.success(
        "Password-reset request processed."
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

        <div className="mb-6 flex h-11 w-11 items-center justify-center rounded-xl bg-sky-500/10 text-sky-300">
          <KeyRound size={23} />
        </div>

        <h2 className="text-2xl font-semibold">
          Forgot password?
        </h2>

        <p className="mt-2 text-sm text-slate-400">
          Enter your email address to request
          password-reset instructions.
        </p>

        {!submitted ? (
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

              <div className="relative">
                <Mail
                  size={18}
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500"
                />

                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(event) =>
                    setEmail(event.target.value)
                  }
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 py-3 pl-11 pr-4 text-slate-100 outline-none transition focus:border-violet-500"
                  placeholder="name@example.com"
                />
              </div>
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
                  Processing request...
                </>
              ) : (
                <>
                  <KeyRound size={19} />
                  Request reset link
                </>
              )}
            </button>
          </form>
        ) : (
          <div className="mt-8">
            <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-4 text-sm leading-6 text-emerald-300">
              {message}
            </div>

            {developmentResetUrl && (
              <div className="mt-4 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-4 text-sm text-amber-200">
                <p className="font-semibold">
                  Development reset link
                </p>

                <p className="mt-1 text-xs leading-5 text-amber-200/80">
                  This link is shown only because
                  the backend is not running in
                  production mode.
                </p>

                <a
                  href={developmentResetUrl}
                  className="mt-3 inline-block break-all font-medium underline"
                >
                  Open password-reset page
                </a>
              </div>
            )}

            <button
              type="button"
              onClick={() => {
                setSubmitted(false);
                setDevelopmentResetUrl(null);
              }}
              className="mt-5 w-full rounded-lg border border-slate-700 px-4 py-3 text-sm font-semibold text-slate-300 transition hover:bg-slate-800"
            >
              Submit another email
            </button>
          </div>
        )}

        <Link
          to="/login"
          className="mt-7 flex items-center justify-center gap-2 text-sm font-semibold text-violet-300 hover:text-violet-200"
        >
          <ArrowLeft size={17} />
          Back to sign in
        </Link>
      </div>
    </div>
  );
}
