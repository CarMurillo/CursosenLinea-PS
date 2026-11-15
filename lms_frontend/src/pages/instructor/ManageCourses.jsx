import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import Layout from "../../components/Layout";
import CourseCard from "../../components/CourseCard";
import { Empty, ErrorState, Loading, Notice } from "../../components/Status";
import { IconBroadcast, IconLayers, IconPlus, IconQuiz } from "../../components/icons";
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
            return <Loading text="Cargando cursos..." variant="cards" />;
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
                <Empty
                    icon={IconLayers}
                    title="Aún no has creado cursos"
                    action={
                        <Link className="btn btn-primary btn-sm" to="/instructor/create-course">
                            Crear curso
                        </Link>
                    }
                >
                    Crea tu primer curso y agrégale contenido.
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
                        contentLabel="Contenido"
                        onClone={handleClone}
                        onContent={(selected) =>
                            navigate(
                                `/instructor/course/${selected.id}/content`
                            )
                        }
                    >
                        <div className="actions">
                            <Link
                                className="btn-link"
                                to={`/instructor/course/${course.id}/assessments`}
                            >
                                <IconQuiz size={16} />
                                Evaluaciones
                            </Link>

                            <Link
                                className="btn-link"
                                to={`/instructor/course/${course.id}/live`}
                            >
                                <IconBroadcast size={16} />
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
            actions={
                <Link className="btn btn-primary" to="/instructor/create-course">
                    <IconPlus size={18} />
                    Crear curso
                </Link>
            }
        >
            <Notice notice={notice} />

            {renderBody()}
        </Layout>
    );
};


export default ManageCourses;
