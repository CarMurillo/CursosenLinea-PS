import api from "./api";

// Visitor: progreso del usuario autenticado en un curso.
export const getMyProgress = async (courseId) => {
    const response = await api.get(`/courses/${courseId}/progress/me`);
    return response.data;
};

// Marca una lección como completada. Devuelve { already_completed, progress }.
export const completeLesson = async (courseId, lessonId) => {
    const response = await api.post(
        `/courses/${courseId}/lessons/${lessonId}/complete`
    );
    return response.data;
};
