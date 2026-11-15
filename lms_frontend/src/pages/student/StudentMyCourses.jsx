import { Link } from "react-router-dom";

import Layout from "../../components/Layout";
import CourseCard from "../../components/CourseCard";
import ProgressBar from "../../components/ProgressBar";
import { Empty, ErrorState, Loading } from "../../components/Status";
import { useResource } from "../../hooks/useResource";
import { getMyEnrolledCourses } from "../../services/courseService";
import { getMyProgress } from "../../services/progressService";

// F3: solo los cursos inscritos, cada uno con su progreso (Visitor).
const loadMyCourses = async () => {
    const courses = await getMyEnrolledCourses();

    const progress = await Promise.all(
        courses.map((course) =>
            getMyProgress(course.id).catch(() => null)
        )
    );

    return courses.map((course, index) => ({
        course,
        progress: progress[index],
    }));
};

const StudentMyCourses = () => {

    const { data, error, loading, reload } = useResource(loadMyCourses);

    const renderBody = () => {
        if (loading && !data) {
            return <Loading text="Cargando tus cursos..." />;
        }

        if (error) {
            return (
                <ErrorState
                    error={error}
                    fallback="No se pudieron cargar tus cursos."
                    onRetry={reload}
                />
            );
        }

        if (!data || data.length === 0) {
            return (
                <Empty>
                    Aún no estás inscrito en ningún curso.{" "}
                    <Link to="/student/courses">Explorar cursos</Link>
                </Empty>
            );
        }

        return (
            <div className="course-grid">

                {data.map(({ course, progress }) => (

                    <CourseCard
                        key={course.id}
                        course={course}
                    >
                        {progress ? (
                            <ProgressBar progress={progress} />
                        ) : (
                            <span className="muted">
                                Progreso no disponible.
                            </span>
                        )}

                        <div className="actions">
                            <Link
                                className="btn-link"
                                to={`/student/course/${course.id}/content`}
                            >
                                Contenido
                            </Link>

                            <Link
                                className="btn-link"
                                to={`/student/course/${course.id}/assessments`}
                            >
                                Evaluaciones
                            </Link>

                            <Link
                                className="btn-link"
                                to={`/student/course/${course.id}/live`}
                            >
                                Clases en vivo
                            </Link>
                        </div>
                    </CourseCard>

                ))}

            </div>
        );
    };

    return (
        <Layout title="Mis cursos">
            {renderBody()}
        </Layout>
    );
};

export default StudentMyCourses;
