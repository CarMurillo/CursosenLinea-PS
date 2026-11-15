import api from "./api";

// Recomendaciones por reglas, cada una con su motivo (`reason`).
export const getMyRecommendations = async () => {
    const response = await api.get("/recommendations/me");
    return response.data;
};
