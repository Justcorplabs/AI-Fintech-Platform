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
