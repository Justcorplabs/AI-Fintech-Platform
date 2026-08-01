import {
  ArrowLeft,
  KeyRound,
  LoaderCircle,
  ScanSearch,
} from "lucide-react";
import {
  useState,
} from "react";
import {
  Link,
  useNavigate,
  useSearchParams,
} from "react-router";
import toast from "react-hot-toast";

import {
  authAPI,
} from "../services/authApi";
import {
  getPasswordError,
  passwordRequirements,
} from "../utils/passwordValidation";

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
    "The password could not be reset. " +
    "The link may be invalid or expired."
  );
}

export default function ResetPassword() {
  const navigate = useNavigate();

  const [searchParams] =
    useSearchParams();

  const token =
    searchParams.get("token")?.trim() ||
    "";

  const [form, setForm] = useState({
    newPassword: "",
    confirmPassword: "",
  });

  const [submitting, setSubmitting] =
    useState(false);

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

    const passwordError =
      getPasswordError(
        form.newPassword
      );

    if (passwordError) {
      toast.error(passwordError);
      return;
    }

    if (
      form.newPassword !==
      form.confirmPassword
    ) {
      toast.error(
        "The passwords do not match."
      );

      return;
    }

    setSubmitting(true);

    try {
      await authAPI.resetPassword({
        token,
        new_password:
          form.newPassword,
        confirm_password:
          form.confirmPassword,
      });

      toast.success(
        "Password reset successfully."
      );

      navigate(
        "/login",
        {
          replace: true,
          state: {
            passwordResetComplete: true,
          },
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

  if (!token) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 px-6 text-slate-50">
        <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-8 text-center shadow-2xl">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-red-500/10 text-red-300">
            <KeyRound size={24} />
          </div>

          <h1 className="mt-6 text-2xl font-semibold">
            Invalid reset link
          </h1>

          <p className="mt-3 text-sm leading-6 text-slate-400">
            This password-reset link does not
            contain a valid token. Request a new
            password-reset link.
          </p>

          <Link
            to="/forgot-password"
            className="mt-7 inline-flex items-center gap-2 rounded-lg bg-violet-600 px-5 py-3 font-semibold text-white hover:bg-violet-500"
          >
            Request a new link
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-6 py-12 text-slate-50">
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
          Reset password
        </h2>

        <p className="mt-2 text-sm text-slate-400">
          Enter and confirm your new secure
          password.
        </p>

        <form
          onSubmit={handleSubmit}
          className="mt-8 space-y-5"
        >
          <div>
            <label
              htmlFor="newPassword"
              className="mb-2 block text-sm font-medium text-slate-300"
            >
              New password
            </label>

            <input
              id="newPassword"
              name="newPassword"
              type="password"
              minLength={8}
              maxLength={128}
              autoComplete="new-password"
              required
              value={form.newPassword}
              onChange={updateField}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 outline-none transition focus:border-violet-500"
              placeholder="Enter a new password"
            />
          </div>

          <div>
            <label
              htmlFor="confirmPassword"
              className="mb-2 block text-sm font-medium text-slate-300"
            >
              Confirm new password
            </label>

            <input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              minLength={8}
              maxLength={128}
              autoComplete="new-password"
              required
              value={form.confirmPassword}
              onChange={updateField}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 outline-none transition focus:border-violet-500"
              placeholder="Repeat the new password"
            />
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-950/70 px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              Password requirements
            </p>

            <ul className="mt-2 space-y-1 text-xs text-slate-500">
              {passwordRequirements.map(
                (requirement) => (
                  <li key={requirement}>
                    ? {requirement}
                  </li>
                )
              )}
            </ul>
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
                Resetting password...
              </>
            ) : (
              <>
                <KeyRound size={19} />
                Reset password
              </>
            )}
          </button>
        </form>

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
