export function getPasswordError(
  password
) {
  if (password !== password.trim()) {
    return (
      "Password cannot begin or end " +
      "with whitespace."
    );
  }

  if (password.length < 8) {
    return (
      "Password must contain at least " +
      "8 characters."
    );
  }

  if (password.length > 128) {
    return (
      "Password cannot exceed " +
      "128 characters."
    );
  }

  if (!/[A-Z]/.test(password)) {
    return (
      "Password must contain an " +
      "uppercase letter."
    );
  }

  if (!/[a-z]/.test(password)) {
    return (
      "Password must contain a " +
      "lowercase letter."
    );
  }

  if (!/[0-9]/.test(password)) {
    return (
      "Password must contain a number."
    );
  }

  return null;
}

export const passwordRequirements = [
  "At least 8 characters",
  "One uppercase letter",
  "One lowercase letter",
  "One number",
  "No leading or trailing spaces",
];
