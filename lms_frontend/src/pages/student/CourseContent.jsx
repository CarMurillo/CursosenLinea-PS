import { useCallback, useState } from "react";
import { Link, useParams } from "react-router-dom";

import Layout from "../../components/Layout";
import ProgressBar from "../../components/ProgressBar";
import { Empty, ErrorState, Loading, Notice } from "../../components/Status";
import { useResource } from "../../hooks/useResource";
import { getCourseContent, getCourseSummary } from "../../services/courseService";
import { completeLesson, getMyProgress } from "../../services/progressService";
import { getErrorMessage, getErrorStatus } from "../../services/errors";

const CourseContent = () => {

    const { courseId } = useParams();

    // Proxy: el backend decide el acceso (403 si es de pago y no está inscrito).
    // Visitor: resumen (duración) y progreso del estudiante.
    const loader = useCallback(async () => {
        const [content, summary, progress] = await Promise.all([
            getCourseContent(courseId),
            getCourseSummary(courseId),
            getMyProgress(courseId).catch(() => null),
        ]);

        return { content, summary, progress };
    }, [courseId]);

    const { data, error, loading, reload, mutate } = useResource(loader);

    const [notice, setNotice] = useState(null);
    const [busyLesson, setBusyLesson] = useState(null);

    const completed = new Set(data?.progress?.completed_lesson_ids || []);

    const handleComplete = async (lesson) => {
        setNotice(null);
        setBusyLesson(lesson.lesson_id);

        try {
            const result = await completeLesson(courseId, lesson.lesson_id);

            mutate((previous) => ({
                ...previous,
                progress: { ...previous.progress, ...result.progress },
            }));

            setNotice({
                type: "success",
                text: result.already_completed
                    ? `"${lesson.title}" ya estaba completada.`
                    : `Lección "${lesson.title}" completada.`,
            });

        } catch (err) {
            setNotice({
                type: "error",
                text: getErrorMessage(err, "No se pudo marcar la lección."),
            });
        } finally {
            setBusyLesson(null);
        }
    };

    const renderLesson = (lesson) => {
        const done = completed.has(lesson.lesson_id);

        return (
            <div className="lesson-row" key={lesson.lesson_id}>
                <div>
                    <h3>{lesson.title}</h3>

                    <p className="muted">
                        {lesson.label || lesson.type}
                        {lesson.icon && ` (${lesson.icon})`}
                        {" - "}
                        {lesson.duration_minutes ?? 0} min
                        {" - "}
                        {lesson.provider}
                    </p>

                    {lesson.url && (
                        <a
                            href={lesson.url}
                            target="_blank"
                            rel="noreferrer"
                        >
                            Abrir contenido
                        </a>
                    )}
                </div>

                {done ? (
                    <span className="lesson-done">Completada</span>
                ) : (
                    <button
                        type="button"
                        className="btn-primary"
                        disabled={busyLesson === lesson.lesson_id}
                        onClick={() => handleComplete(lesson)}
                    >
                        Marcar como completada
                    </button>
                )}
            </div>
        );
    };

    // El contenido es un Composite: módulos con `items` (lecciones o submódulos).
    const renderItems = (items) =>
        items.map((item, index) =>
            item.lesson_id ? (
                renderLesson(item)
            ) : (
                <div className="panel" key={`${item.title}-${index}`}>
                    <h2>{item.title}</h2>
                    {renderItems(item.items || [])}
                </div>
            )
        );

    const renderBody = () => {
        if (loading && !data) {
            return <Loading text="Cargando contenido..." />;
        }

        if (error) {
            if (getErrorStatus(error) === 403) {
                return (
                    <div className="status status-error">
                        <p>
                            {getErrorMessage(error, "No tienes acceso a este curso.")}
                        </p>
                        <p>
                            Este curso requiere pago o inscripción.{" "}
                            <Link to="/student/courses">Ir al catálogo</Link>
                        </p>
                    </div>
                );
            }

            return (
                <ErrorState
                    error={error}
                    fallback="No se pudo cargar el contenido."
                    onRetry={reload}
                />
            );
        }

        const { content, summary, progress } = data;

        return (
            <>
                <div className="panel">
                    <h2>{summary?.title || content.title}</h2>

                    <p className="muted">
                        {summary?.total_modules ?? 0} módulos -{" "}
                        {summary?.total_lessons ?? 0} lecciones -{" "}
                        {summary?.total_minutes ?? 0} min en total
                    </p>

                    {progress ? (
                        <ProgressBar progress={progress} />
                    ) : (
                        <p className="muted">
                            Inscríbete para registrar tu progreso.
                        </p>
                    )}

                    <div className="actions">
                        <Link to={`/student/course/${courseId}/assessments`}>
                            Evaluaciones
                        </Link>
                        <Link to={`/student/course/${courseId}/live`}>
                            Clases en vivo
                        </Link>
                    </div>
                </div>

                <Notice notice={notice} />

                {!content.items || content.items.length === 0 ? (
                    <Empty>Este curso todavía no tiene lecciones.</Empty>
                ) : (
                    renderItems(content.items)
                )}
            </>
        );
    };

    return (
        <Layout title="Contenido del curso">
            {renderBody()}
        </Layout>
    );
};

export default CourseContent;
