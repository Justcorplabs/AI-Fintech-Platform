import axios from "axios";

import {
  clearAuthTokens,
  getAccessToken,
} from "./authStorage";

const apiOrigin = (
  import.meta.env.VITE_API_BASE_URL || ""
).replace(/\/+$/, "");

const apiBaseURL = `${apiOrigin}/api/v1`;

const httpClient = axios.create({
  baseURL: apiBaseURL,
  headers: {
    "Content-Type": "application/json",
  },
});

httpClient.interceptors.request.use(
  (config) => {
    const token = getAccessToken();

    if (token) {
      config.headers.Authorization =
        `Bearer ${token}`;
    }

    return config;
  }
);

httpClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearAuthTokens();

      if (
        typeof window !== "undefined" &&
        window.location.pathname !==
          "/login"
      ) {
        window.location.assign(
          "/login"
        );
      }
    }

    return Promise.reject(error);
  }
);

export default httpClient;
