import api from "./api";

// Tipos de evento del dominio (EventType en el backend).
export const EVENT_TYPES = [
    "course_published",
    "student_enrolled",
    "payment_approved",
    "lesson_completed",
    "assessment_submitted",
    "assessment_graded",
    "certificate_issued",
    "live_session_recorded",
];

// Observer: log de auditoría (solo admin). eventType opcional.
export const getAuditLog = async ({ eventType = "", limit = 100 } = {}) => {
    const params = { limit };

    if (eventType) {
        params.event_type = eventType;
    }

    const response = await api.get("/admin/audit-log", { params });
    return response.data;
};

// Estado del servicio y contadores (público).
export const getHealth = async () => {
    const response = await api.get("/health");
    return response.data;
};
