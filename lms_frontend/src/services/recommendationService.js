import api from "./api";

// Nombre visible de cada regla (estrategia del patrón Strategy en el backend).
export const RULE_LABELS = {
    refuerzo: "Refuerzo",
    siguiente_nivel: "Siguiente nivel",
    afinidad: "Afinidad",
    gratis_para_empezar: "Gratis para empezar",
    popular: "Popular",
};

// Recomendaciones por reglas, cada una con su motivo (`reason`).
export const getMyRecommendations = async () => {
    const response = await api.get("/recommendations/me");
    return response.data;
};
