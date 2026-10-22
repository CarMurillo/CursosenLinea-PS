import api from "./api";

export const getCourses = async () => {
    const response = await api.get("/courses/");
    return response.data;
};

export const createCourse = async (courseData) => {
    const response = await api.post("/courses/", courseData);
    return response.data;
};

export const enrollCourse = async (courseId, studentName) => {
    const response = await api.post(
        `/courses/${courseId}/enroll`,
        {
            student_name: studentName,
        }
    );

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

export const getCourseContent = async (
    courseId
) => {

    const response = await api.get(
        `/courses/${courseId}/content`
    );

    return response.data;
};


export const addLesson = async (
    courseId,
    lessonData
) => {

    const response = await api.post(
        `/courses/${courseId}/content/lessons`,
        lessonData
    );

    return response.data;
};