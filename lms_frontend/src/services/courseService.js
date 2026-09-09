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
