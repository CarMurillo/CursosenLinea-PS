import { useEffect, useState } from "react";

import Navbar from "../../components/Navbar";
import Sidebar from "../../components/Sidebar";
import CourseCard from "../../components/CourseCard";

import {
    getCourses,
    cloneCourse
} from "../../services/courseService";


const ManageCourses = () => {

    const [courses, setCourses] = useState([]);
    const [error, setError] = useState("");
    const [message, setMessage] = useState("");

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


    const handleClone = async (course) => {

        setError("");
        setMessage("");

        const newTitle = window.prompt(
            "Ingrese el nombre para la copia:",
            `${course.title} (Copia)`
        );

        if (newTitle === null) {
            return;
        }

        try {

            const clonedCourse = await cloneCourse(
                course.id,
                newTitle
            );

            setCourses((previousCourses) => [
                ...previousCourses,
                clonedCourse
            ]);

            setMessage(
                `Curso "${course.title}" clonado correctamente.`
            );

        } catch (error) {

            console.error(error);

            setError(
                error.response?.data?.detail ||
                "No se pudo clonar el curso"
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
                        Gestionar cursos
                    </h1>

                    <p>
                        Desde aquí puedes consultar y clonar
                        los cursos existentes.
                    </p>


                    {message && (
                        <p className="success">
                            {message}
                        </p>
                    )}


                    {error && (
                        <p className="error">
                            {error}
                        </p>
                    )}


                    <div className="course-grid">

                        {courses.length === 0 ? (

                            <p>
                                No hay cursos disponibles.
                            </p>

                        ) : (

                            courses.map((course) => (

                                <CourseCard
                                    key={course.id}
                                    course={course}
                                    showClone={true}
                                    onClone={handleClone}
                                />

                            ))

                        )}

                    </div>

                </main>

            </div>

        </div>
    );
};


export default ManageCourses;