import { useEffect, useState } from "react";
import Navbar from "../../components/Navbar";
import Sidebar from "../../components/Sidebar";
import CourseCard from "../../components/CourseCard";

import {
    getCourses,
    enrollCourse
} from "../../services/courseService";

import { useAuth } from "../../context/AuthContext";

const StudentMyCourses = () => {

    const [courses, setCourses] = useState([]);
    const [error, setError] = useState("");

    const { user } = useAuth();

    useEffect(() => {

        loadCourses();

    }, []);

    const loadCourses = async () => {

        try {

            const data = await getCourses();

            setCourses(data);

        } catch (error) {

            console.error(error);

            setError(
                "No se pudieron cargar los cursos"
            );
        }
    };

    const handleEnroll = async (course) => {

        try {

            await enrollCourse(
                course.id,
                user.full_name
            );

            alert(
                `Te has inscrito en ${course.title}`
            );

        } catch (error) {

            console.error(error);

            alert(
                error.response?.data?.detail ||
                "No se pudo realizar la inscripción"
            );
        }
    };

    return (
        <div className="layout">

            <Navbar />

            <div className="content-wrapper">

                <Sidebar />

                <main className="main-content">

                    <h1>
                        Cursos Matriculados
                    </h1>

                    {error && (
                        <p className="error">
                            {error}
                        </p>
                    )}

                    <div className="course-grid">

                        {courses.map((course) => (

                            <CourseCard
                                key={course.id}
                                course={course}
                                showEnroll={true}
                                onEnroll={handleEnroll}
                            />

                        ))}

                    </div>

                </main>

            </div>

        </div>
    );
};

export default StudentMyCourses;