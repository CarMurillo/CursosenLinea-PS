import { useCallback, useState } from "react";
import { Link, useParams } from "react-router-dom";

import Layout from "../../components/Layout";
import ProgressBar from "../../components/ProgressBar";
import { Empty, ErrorState, Loading, Notice } from "../../components/Status";
import { useResource } from "../../hooks/useResource";
import { getCourseContent, getCourseSummary } from "../../services/courseService";
import { completeLesson, getMyProgress } from "../../services/progressService";
import { getErrorMessage, getErrorStatus } from "../../services/errors";
import {
    IconBook,
    IconBroadcast,
    IconCheck,
    IconChevronDown,
    IconClock,
    IconDocument,
    IconExternal,
    IconLayers,
    IconLock,
    IconPlay,
    IconQuiz,
    IconStar,
    IconVideo
} from "../../components/icons";

const LESSON_ICONS = {
    video: IconVideo,
    quiz: IconQuiz,
    document: IconDocument,
};

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
        const busy = busyLesson === lesson.lesson_id;
        const LessonIcon = LESSON_ICONS[lesson.type] || IconDocument;

        return (
            <li
                className={`lesson-row${done ? " is-done" : ""}`}
                key={lesson.lesson_id}
            >
                <span className={`lesson-icon lesson-icon-${lesson.type}`} aria-hidden="true">
                    <LessonIcon size={20} />
                </span>

                <div className="lesson-body">
                    <h4 className="lesson-title">{lesson.title}</h4>

                    <p className="meta-inline">
                        <span>{lesson.label || lesson.type}</span>
                        <span>
                            <IconClock size={14} />
                            {lesson.duration_minutes ?? 0} min
                        </span>
                        {lesson.provider && <span>{lesson.provider}</span>}
                    </p>
                </div>

                <div className="lesson-actions">
                    {lesson.url && (
                        <a
                            className="btn btn-ghost btn-sm"
                            href={lesson.url}
                            target="_blank"
                            rel="noreferrer"
                        >
                            <IconExternal size={16} />
                            Abrir contenido
                        </a>
                    )}

                    {done ? (
                        <span className="badge badge-enrolled">
                            <IconCheck size={14} />
                            Completada
                        </span>
                    ) : (
                        <button
                            type="button"
                            className={`btn btn-secondary btn-sm${busy ? " is-loading" : ""}`}
                            disabled={busy}
                            aria-busy={busy}
                            onClick={() => handleComplete(lesson)}
                        >
                            <IconCheck size={16} />
                            Marcar como completada
                        </button>
                    )}
                </div>
            </li>
        );
    };

    // El contenido es un Composite: módulos con `items` (lecciones o submódulos).
    // Las lecciones se agrupan en una lista; los módulos se muestran como acordeón.
    const renderItems = (items) => {
        const lessons = items.filter((item) => item.lesson_id);
        const modules = items.filter((item) => !item.lesson_id);

        return (
            <>
                {lessons.length > 0 && (
                    <ul className="lesson-list">{lessons.map(renderLesson)}</ul>
                )}

                {modules.map((item, index) => {
                    const moduleLessons = (item.items || []).filter((child) => child.lesson_id);
                    const doneCount = moduleLessons.filter((child) =>
                        completed.has(child.lesson_id)
                    ).length;

                    return (
                        <details
                            className="disclosure module"
                            key={`${item.title}-${index}`}
                            open
                        >
                            <summary>
                                <span className="module-title">
                                    <IconLayers size={18} />
                                    {item.title}
                                </span>
                                <span className="module-meta">
                                    <span className="muted">
                                        {doneCount}/{moduleLessons.length} completadas
                                    </span>
                                    <IconChevronDown size={18} className="chevron" />
                                </span>
                            </summary>

                            <div className="disclosure-body">
                                {renderItems(item.items || [])}
                            </div>
                        </details>
                    );
                })}
            </>
        );
    };

    const renderBody = () => {
        if (loading && !data) {
            return <Loading text="Cargando contenido..." />;
        }

        if (error) {
            if (getErrorStatus(error) === 403) {
                return (
                    <div className="lock-panel">
                        <span className="lock-icon" aria-hidden="true">
                            <IconLock size={32} />
                        </span>

                        <h2>Contenido bloqueado</h2>

                        <p>
                            {getErrorMessage(error, "No tienes acceso a este curso.")}
                        </p>

                        <p className="muted">
                            Este curso requiere pago o inscripción.
                        </p>

                        <Link className="btn btn-premium" to="/student/courses">
                            <IconStar size={18} />
                            Adquirir en el catálogo
                        </Link>
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
                <section className="course-hero">
                    <div className="course-hero-main">
                        <h1>{summary?.title || content.title}</h1>

                        {content.instructor && (
                            <p className="course-hero-instructor">
                                {content.instructor}
                            </p>
                        )}

                        <p className="meta-inline">
                            <span>
                                <IconLayers size={16} />
                                {summary?.total_modules ?? 0} módulos
                            </span>
                            <span>
                                <IconPlay size={16} />
                                {summary?.total_lessons ?? 0} lecciones
                            </span>
                            <span>
                                <IconClock size={16} />
                                {summary?.total_minutes ?? 0} min en total
                            </span>
                        </p>

                        <div className="actions">
                            <Link
                                className="btn btn-secondary btn-sm"
                                to={`/student/course/${courseId}/assessments`}
                            >
                                <IconQuiz size={16} />
                                Evaluaciones
                            </Link>
                            <Link
                                className="btn btn-secondary btn-sm"
                                to={`/student/course/${courseId}/live`}
                            >
                                <IconBroadcast size={16} />
                                Clases en vivo
                            </Link>
                        </div>
                    </div>

                    <div className="course-hero-progress">
                        <h2 className="course-hero-label">Tu progreso</h2>
                        {progress ? (
                            <ProgressBar progress={progress} compact />
                        ) : (
                            <p className="muted">
                                Inscríbete para registrar tu progreso.
                            </p>
                        )}
                    </div>
                </section>

                <Notice notice={notice} />

                {!content.items || content.items.length === 0 ? (
                    <Empty icon={IconBook}>Este curso todavía no tiene lecciones.</Empty>
                ) : (
                    <section className="section" aria-label="Temario">
                        {renderItems(content.items)}
                    </section>
                )}
            </>
        );
    };

    return (
        <Layout
            title={data && !error ? undefined : "Contenido del curso"}
            back={{ to: "/student/my-courses", label: "Mis cursos" }}
        >
            {renderBody()}
        </Layout>
    );
};

export default CourseContent;
