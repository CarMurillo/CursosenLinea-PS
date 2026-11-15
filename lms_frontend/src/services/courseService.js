
import api from "./api";

export const getCourses = async () => {
    const response = await api.get("/courses/");
    return response.data;
};

// El instructor se deriva del token en el backend (no se envía `instructor`).
export const createCourse = async (courseData) => {
    const response = await api.post("/courses/", courseData);
    return response.data;
};

// F3: cursos en los que el usuario autenticado está inscrito.
export const getMyEnrolledCourses = async () => {
    const response = await api.get("/courses/me/enrolled");
    return response.data;
};

// Inscripción por token, sin cuerpo. 409 si ya está inscrito; 403 si el
// curso es de pago y no hay pago aprobado.
export const enrollCourse = async (courseId) => {
    const response = await api.post(`/courses/${courseId}/enroll`);
    return response.data;
};

// Prototype: clonar un curso existente
export const cloneCourse = async (courseId, newTitle = "") => {
    const response = await api.post(
        `/courses/${courseId}/clone`,
        {
            new_title: newTitle || null,
        }
    );

    return response.data;
};

// Proxy: el acceso lo decide el backend con el token (401 / 403 / 200).
export const getCourseContent = async (courseId) => {
    const response = await api.get(
        `/courses/${courseId}/content`
    );

    return response.data;
};

// Visitor: resumen (duración total, lecciones por tipo, temario).
export const getCourseSummary = async (courseId) => {
    const response = await api.get(
        `/courses/${courseId}/content/summary`
    );

    return response.data;
};

export const addLesson = async (courseId, lessonData) => {
    const response = await api.post(
        `/courses/${courseId}/content/lessons`,
        lessonData
    );

    return response.data;
};

// Flyweight: metadatos compartidos por tipo de contenido (video, quiz, document).
export const getContentMetadata = async (contentType) => {
    const response = await api.get(
        `/courses/content-metadata/${contentType}`
    );

    return response.data;
};
