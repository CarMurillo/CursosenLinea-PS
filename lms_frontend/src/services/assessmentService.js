import api from "./api";

// State: draft -> published -> closed. Las transiciones inválidas responden 409.

export const getCourseAssessments = async (courseId) => {
    const response = await api.get(`/courses/${courseId}/assessments`);
    return response.data;
};

export const getAssessment = async (assessmentId) => {
    const response = await api.get(`/assessments/${assessmentId}`);
    return response.data;
};

// El listado por curso no incluye intentos: se pide el detalle de cada una
// (trae `attempts` para dueño/admin y `my_attempts` para el estudiante).
export const getCourseAssessmentsWithAttempts = async (courseId) => {
    const list = await getCourseAssessments(courseId);

    return Promise.all(
        list.map((assessment) =>
            getAssessment(assessment.id).catch(() => assessment)
        )
    );
};

export const createAssessment = async (assessmentData) => {
    const response = await api.post("/assessments", assessmentData);
    return response.data;
};

export const addQuestion = async (assessmentId, questionData) => {
    const response = await api.post(
        `/assessments/${assessmentId}/questions`,
        questionData
    );
    return response.data;
};

export const publishAssessment = async (assessmentId) => {
    const response = await api.post(`/assessments/${assessmentId}/publish`);
    return response.data;
};

export const closeAssessment = async (assessmentId) => {
    const response = await api.post(`/assessments/${assessmentId}/close`);
    return response.data;
};

// answers: { [question_id]: índice de opción }
export const submitAttempt = async (assessmentId, answers) => {
    const response = await api.post(
        `/assessments/${assessmentId}/attempts`,
        { answers }
    );
    return response.data;
};
