import {
  LoaderCircle,
  ScanSearch,
  UserPlus,
} from "lucide-react";
import {
  useState,
} from "react";
import {
  Link,
  useNavigate,
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
    "Account creation failed. " +
    "Review the form and try again."
  );
}

export default function Register() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    full_name: "",
    email: "",
    organisation: "",
    password: "",
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
        form.password
      );

    if (passwordError) {
      toast.error(passwordError);
      return;
    }

    if (
      form.password !==
      form.confirmPassword
    ) {
      toast.error(
        "The passwords do not match."
      );

      return;
    }

    setSubmitting(true);

    try {
      const email =
        form.email.trim().toLowerCase();

      await authAPI.register({
        full_name:
          form.full_name.trim(),
        email,
        password: form.password,
        organisation:
          form.organisation.trim() ||
          null,
      });

      toast.success(
        "Account created successfully."
      );

      navigate(
        "/login",
        {
          replace: true,
          state: {
            registrationComplete: true,
            registeredEmail: email,
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

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-6 py-12 text-slate-50">
      <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900 p-8 shadow-2xl">
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
          Create account
        </h2>

        <p className="mt-2 text-sm text-slate-400">
          Create a secure account to access
          the resume review platform.
        </p>

        <form
          onSubmit={handleSubmit}
          className="mt-8 space-y-5"
        >
          <div>
            <label
              htmlFor="full_name"
              className="mb-2 block text-sm font-medium text-slate-300"
            >
              Full name
            </label>

            <input
              id="full_name"
              name="full_name"
              type="text"
              minLength={2}
              maxLength={120}
              autoComplete="name"
              required
              value={form.full_name}
              onChange={updateField}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 outline-none transition focus:border-violet-500"
              placeholder="Your full name"
            />
          </div>

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
              htmlFor="organisation"
              className="mb-2 block text-sm font-medium text-slate-300"
            >
              Organisation
              <span className="ml-2 text-slate-500">
                Optional
              </span>
            </label>

            <input
              id="organisation"
              name="organisation"
              type="text"
              maxLength={150}
              autoComplete="organization"
              value={form.organisation}
              onChange={updateField}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 outline-none transition focus:border-violet-500"
              placeholder="Company or institution"
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
              minLength={8}
              maxLength={128}
              autoComplete="new-password"
              required
              value={form.password}
              onChange={updateField}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 outline-none transition focus:border-violet-500"
              placeholder="Minimum 8 characters"
            />

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

          <div>
            <label
              htmlFor="confirmPassword"
              className="mb-2 block text-sm font-medium text-slate-300"
            >
              Confirm password
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
              placeholder="Repeat your password"
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
                Creating account...
              </>
            ) : (
              <>
                <UserPlus size={19} />
                Create account
              </>
            )}
          </button>
        </form>

        <p className="mt-7 text-center text-sm text-slate-400">
          Already have an account?{" "}
          <Link
            to="/login"
            className="font-semibold text-violet-300 hover:text-violet-200"
          >
            Sign in
          </Link>
        </p>

        <p className="mt-4 text-center text-xs text-slate-500">
          New accounts receive standard viewer
          access. Additional permissions are
          assigned by an administrator.
        </p>
      </div>
    </div>
  );
}
