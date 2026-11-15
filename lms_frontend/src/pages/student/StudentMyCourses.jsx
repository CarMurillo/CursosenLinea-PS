import { Link, useNavigate } from "react-router-dom";

import Layout from "../../components/Layout";
import CourseCard from "../../components/CourseCard";
import ProgressBar from "../../components/ProgressBar";
import { Empty, ErrorState, Loading } from "../../components/Status";
import { useResource } from "../../hooks/useResource";
import { getMyEnrolledCourses } from "../../services/courseService";
import { getMyProgress } from "../../services/progressService";
import { IconBook, IconBroadcast, IconQuiz } from "../../components/icons";

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

    const navigate = useNavigate();

    const renderBody = () => {
        if (loading && !data) {
            return <Loading text="Cargando tus cursos..." variant="cards" />;
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
                <Empty
                    icon={IconBook}
                    title="Aún no estás inscrito en ningún curso"
                    action={
                        <Link className="btn btn-primary btn-sm" to="/student/courses">
                            Explorar cursos
                        </Link>
                    }
                >
                    Inscríbete en un curso gratuito o adquiere uno Premium para empezar.
                </Empty>
            );
        }

        return (
            <div className="course-grid">

                {data.map(({ course, progress }) => (

                    <CourseCard
                        key={course.id}
                        course={course}
                        enrolled
                        showContent
                        contentLabel={
                            (progress?.percentage ?? 0) >= 100
                                ? "Repasar"
                                : (progress?.percentage ?? 0) > 0
                                    ? "Continuar"
                                    : "Empezar"
                        }
                        onContent={(selected) =>
                            navigate(`/student/course/${selected.id}/content`)
                        }
                    >
                        {progress ? (
                            <ProgressBar progress={progress} compact />
                        ) : (
                            <span className="muted">
                                Progreso no disponible.
                            </span>
                        )}

                        <div className="actions">
                            <Link
                                className="btn-link"
                                to={`/student/course/${course.id}/assessments`}
                            >
                                <IconQuiz size={16} />
                                Evaluaciones
                            </Link>

                            <Link
                                className="btn-link"
                                to={`/student/course/${course.id}/live`}
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
            title="Mis cursos"
            subtitle="Retoma tus cursos y revisa tu avance."
        >
            {renderBody()}
        </Layout>
    );
};

export default StudentMyCourses;
