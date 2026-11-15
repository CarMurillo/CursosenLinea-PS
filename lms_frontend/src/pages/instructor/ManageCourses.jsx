import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import Layout from "../../components/Layout";
import CourseCard from "../../components/CourseCard";
import { Empty, ErrorState, Loading, Notice } from "../../components/Status";
import { useAuth } from "../../context/auth-context";
import { useResource } from "../../hooks/useResource";
import { cloneCourse, getCourses } from "../../services/courseService";
import { getErrorMessage } from "../../services/errors";


const ManageCourses = () => {

    const { user } = useAuth();
    const navigate = useNavigate();

    const { data, error, loading, reload, mutate } = useResource(getCourses);

    const [notice, setNotice] = useState(null);
    const [busyId, setBusyId] = useState(null);

    // El instructor gestiona sus propios cursos (el backend exige ser dueño o admin).
    const courses = (data || []).filter(
        (course) =>
            user?.role === "admin" || course.instructor_id === user?.user_id
    );

    const handleClone = async (course) => {

        setNotice(null);

        const newTitle = window.prompt(
            "Ingrese el nombre para la copia:",
            `${course.title} (Copia)`
        );

        if (newTitle === null) {
            return;
        }

        setBusyId(course.id);

        try {

            const clonedCourse = await cloneCourse(
                course.id,
                newTitle
            );

            mutate((previous) => [...(previous || []), clonedCourse]);

            setNotice({
                type: "success",
                text: `Curso "${course.title}" clonado correctamente.`,
            });

        } catch (err) {

            setNotice({
                type: "error",
                text: getErrorMessage(err, "No se pudo clonar el curso"),
            });

        } finally {
            setBusyId(null);
        }
    };

    const renderBody = () => {
        if (loading && !data) {
            return <Loading text="Cargando cursos..." />;
        }

        if (error) {
            return (
                <ErrorState
                    error={error}
                    fallback="No se pudieron cargar los cursos"
                    onRetry={reload}
                />
            );
        }

        if (courses.length === 0) {
            return (
                <Empty>
                    Aún no has creado cursos.{" "}
                    <Link to="/instructor/create-course">Crear curso</Link>
                </Empty>
            );
        }

        return (
            <div className="course-grid">

                {courses.map((course) => (

                    <CourseCard
                        key={course.id}
                        course={course}
                        busy={busyId === course.id}
                        showClone={true}
                        showContent={true}
                        onClone={handleClone}
                        onContent={(selected) =>
                            navigate(
                                `/instructor/course/${selected.id}/content`
                            )
                        }
                    >
                        <div className="actions">
                            <Link to={`/instructor/course/${course.id}/assessments`}>
                                Evaluaciones
                            </Link>

                            <Link to={`/instructor/course/${course.id}/live`}>
                                Clases en vivo
                            </Link>
                        </div>
                    </CourseCard>

                ))}

            </div>
        );
    };


    return (
        <Layout
            title="Gestionar cursos"
            subtitle="Contenido, evaluaciones, clases en vivo y clonación de tus cursos."
        >
            <Notice notice={notice} />

            {renderBody()}
        </Layout>
    );
};


export default ManageCourses;
