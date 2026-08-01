from pathlib import Path


PROJECT_ROOT = (
    Path(__file__).resolve().parents[2]
)

RESUME_FRONTEND = (
    PROJECT_ROOT
    / "frontend-resume"
)


def read_text(path: Path) -> str:
    return path.read_text(
        encoding="utf-8"
    )


def test_resume_frontend_has_login_page():
    source = read_text(
        RESUME_FRONTEND
        / "src"
        / "pages"
        / "Login.jsx"
    )

    assert "login({" in source
    assert "email" in source
    assert "password" in source
    assert "Signing in" in source


def test_resume_frontend_uses_auth_provider():
    source = read_text(
        RESUME_FRONTEND
        / "src"
        / "App.jsx"
    )

    assert "AuthProvider" in source
    assert "ProtectedRoute" in source
    assert 'path="/login"' in source
    assert "<Outlet />" in source


def test_resume_routes_are_protected():
    source = read_text(
        RESUME_FRONTEND
        / "src"
        / "App.jsx"
    )

    protected_route_index = source.index(
        "element={<ProtectedRoute />}"
    )

    reviewer_index = source.index(
        'path="/resume-reviewer"'
    )

    recruitment_index = source.index(
        'path="/recruitment"'
    )

    assert protected_route_index < reviewer_index
    assert protected_route_index < recruitment_index


def test_auth_context_restores_current_user():
    source = read_text(
        RESUME_FRONTEND
        / "src"
        / "auth"
        / "AuthContext.jsx"
    )

    assert "getAccessToken" in source
    assert "authAPI.getCurrentUser()" in source
    assert "clearAuthTokens()" in source
    assert "setUser(response.data)" in source


def test_topbar_uses_authenticated_user_and_logout():
    source = read_text(
        RESUME_FRONTEND
        / "src"
        / "components"
        / "layout"
        / "TopBar.jsx"
    )

    assert "useAuth" in source
    assert "user?.full_name" in source
    assert "user?.role" in source
    assert "onClick={logout}" in source
    assert "Recruitment Team" not in source


def test_resume_frontend_has_public_registration_route():
    source = read_text(
        RESUME_FRONTEND
        / "src"
        / "App.jsx"
    )

    assert 'path="/register"' in source
    assert "element={<Register />}" in source
    assert (
        'import Register from '
        '"./pages/Register";'
        in source
    )


def test_resume_registration_uses_safe_public_contract():
    source = read_text(
        RESUME_FRONTEND
        / "src"
        / "pages"
        / "Register.jsx"
    )

    assert "authAPI.register" in source
    assert "full_name" in source
    assert "email" in source
    assert "organisation" in source
    assert "password" in source
    assert "confirmPassword" in source

    assert "role:" not in source
    assert 'name="role"' not in source
    assert "selectRole" not in source


def test_resume_login_links_to_registration():
    source = read_text(
        RESUME_FRONTEND
        / "src"
        / "pages"
        / "Login.jsx"
    )

    assert 'to="/register"' in source
    assert "Create account" in source
    assert "registeredEmail" in source
    assert "registrationComplete" in source


def test_resume_frontend_has_password_reset_routes():
    source = read_text(
        RESUME_FRONTEND
        / "src"
        / "App.jsx"
    )

    assert (
        'path="/forgot-password"'
        in source
    )

    assert (
        "element={<ForgotPassword />}"
        in source
    )

    assert (
        'path="/reset-password"'
        in source
    )

    assert (
        "element={<ResetPassword />}"
        in source
    )


def test_resume_auth_api_supports_password_reset():
    source = read_text(
        RESUME_FRONTEND
        / "src"
        / "services"
        / "authApi.js"
    )

    assert "forgotPassword" in source
    assert '"/auth/forgot-password"' in source
    assert "resetPassword" in source
    assert '"/auth/reset-password"' in source


def test_resume_login_links_to_forgot_password():
    source = read_text(
        RESUME_FRONTEND
        / "src"
        / "pages"
        / "Login.jsx"
    )

    assert 'to="/forgot-password"' in source
    assert "Forgot password?" in source
    assert "passwordResetComplete" in source


def test_forgot_password_uses_neutral_response():
    source = read_text(
        RESUME_FRONTEND
        / "src"
        / "pages"
        / "ForgotPassword.jsx"
    )

    assert "authAPI.forgotPassword" in source
    assert "neutralMessage" in source
    assert "active account exists" in source
    assert "developmentResetUrl" in source
    assert "response.data?.reset_url" in source


def test_reset_password_uses_backend_contract():
    source = read_text(
        RESUME_FRONTEND
        / "src"
        / "pages"
        / "ResetPassword.jsx"
    )

    assert "useSearchParams" in source
    assert 'searchParams.get("token")' in source
    assert "authAPI.resetPassword" in source
    assert "new_password" in source
    assert "confirm_password" in source
    assert "getPasswordError" in source


def test_shared_password_validation_matches_backend():
    source = read_text(
        RESUME_FRONTEND
        / "src"
        / "utils"
        / "passwordValidation.js"
    )

    assert "password.length < 8" in source
    assert "/[A-Z]/" in source
    assert "/[a-z]/" in source
    assert "/[0-9]/" in source
    assert "password.trim()" in source
