import httpClient from "./httpClient";

export const fraudAPI = {
  predict: (data) =>
    httpClient.post(
      "/fraud/predict",
      data
    ),

  getTransactions: (params) =>
    httpClient.get(
      "/fraud/transactions",
      { params }
    ),

  getTransaction: (id) =>
    httpClient.get(
      `/fraud/transactions/${id}`
    ),

  reviewTransaction: (id, data) =>
    httpClient.patch(
      `/fraud/transactions/${id}/review`,
      data
    ),

  getStats: () =>
    httpClient.get(
      "/fraud/stats"
    ),

  getModelMetadata: () =>
    httpClient.get(
      "/fraud/model/metadata"
    ),
};
