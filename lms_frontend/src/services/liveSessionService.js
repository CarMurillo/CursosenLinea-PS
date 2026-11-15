import api from "./api";

// State: scheduled -> live -> recorded. Transiciones inválidas => 409.

export const getCourseLiveSessions = async (courseId) => {
    const response = await api.get(`/courses/${courseId}/live-sessions`);
    return response.data;
};

export const getLiveSession = async (sessionId) => {
    const response = await api.get(`/live-sessions/${sessionId}`);
    return response.data;
};

// { course_id, title, scheduled_at?, duration_minutes? }
export const createLiveSession = async (sessionData) => {
    const response = await api.post("/live-sessions", sessionData);
    return response.data;
};

export const startLiveSession = async (sessionId) => {
    const response = await api.post(`/live-sessions/${sessionId}/start`);
    return response.data;
};

export const endLiveSession = async (sessionId) => {
    const response = await api.post(`/live-sessions/${sessionId}/end`);
    return response.data;
};
