import {
  setAuthTokens,
} from "./authStorage";

import httpClient from "./httpClient";

export const authAPI = {
  login: async (data) => {
    const response =
      await httpClient.post(
        "/auth/login",
        data
      );

    setAuthTokens(response.data);

    return response;
  },

  register: (data) =>
    httpClient.post(
      "/auth/register",
      data
    ),

  forgotPassword: (data) =>
    httpClient.post(
      "/auth/forgot-password",
      data
    ),

  resetPassword: (data) =>
    httpClient.post(
      "/auth/reset-password",
      data
    ),

  getCurrentUser: () =>
    httpClient.get("/auth/me"),
};
