const ACCESS_TOKEN_KEY =
  "justcorp.resume.access_token";

const REFRESH_TOKEN_KEY =
  "justcorp.resume.refresh_token";

function getStorage() {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage;
}

export function getAccessToken() {
  return (
    getStorage()?.getItem(
      ACCESS_TOKEN_KEY
    ) ?? null
  );
}

export function getRefreshToken() {
  return (
    getStorage()?.getItem(
      REFRESH_TOKEN_KEY
    ) ?? null
  );
}

export function setAuthTokens(tokens = {}) {
  const storage = getStorage();

  if (!storage) {
    return;
  }

  const accessToken =
    tokens.access_token ??
    tokens.accessToken ??
    tokens.token ??
    null;

  const refreshToken =
    tokens.refresh_token ??
    tokens.refreshToken ??
    null;

  if (accessToken) {
    storage.setItem(
      ACCESS_TOKEN_KEY,
      accessToken
    );
  }

  if (refreshToken) {
    storage.setItem(
      REFRESH_TOKEN_KEY,
      refreshToken
    );
  }
}

export function clearAuthTokens() {
  const storage = getStorage();

  if (!storage) {
    return;
  }

  storage.removeItem(
    ACCESS_TOKEN_KEY
  );

  storage.removeItem(
    REFRESH_TOKEN_KEY
  );
}

export {
  ACCESS_TOKEN_KEY,
  REFRESH_TOKEN_KEY,
};
