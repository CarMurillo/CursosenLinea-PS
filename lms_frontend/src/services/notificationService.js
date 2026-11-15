import api from "./api";

// Observer: bandeja de notificaciones in-app (recientes primero).
export const getMyNotifications = async () => {
    const response = await api.get("/notifications/me");
    return response.data;
};
