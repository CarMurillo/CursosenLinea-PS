import { useCallback, useState } from "react";
import { useParams } from "react-router-dom";

import Layout from "../../components/Layout";
import CourseTabs from "../../components/CourseTabs";
import { Empty, ErrorState, Loading, Notice } from "../../components/Status";
import {
    IconBook,
    IconChevronDown,
    IconClock,
    IconDocument,
    IconLayers,
    IconQuiz,
    IconVideo
} from "../../components/icons";
import { useResource } from "../../hooks/useResource";
import {
    addLesson,
    getCourseContent,
    getCourseSummary
} from "../../services/courseService";
import { getErrorMessage } from "../../services/errors";

const LESSON_ICONS = {
    video: IconVideo,
    quiz: IconQuiz,
    document: IconDocument,
};

const LessonIcon = ({ type }) => {
    const Icon = LESSON_ICONS[type] || IconDocument;
    return <Icon size={16} />;
};


const ManageContent = () => {

    const { courseId } = useParams();

    // Composite (contenido) + Visitor (resumen: duración, lecciones por tipo).
    const loader = useCallback(async () => {
        const [content, summary] = await Promise.all([
            getCourseContent(courseId),
            getCourseSummary(courseId),
        ]);

        return { content, summary };
    }, [courseId]);

    const { data, error, loading, reload } = useResource(loader);

    const [form, setForm] = useState({
        module_title: "Módulo 1",
        title: "",
        media_id: "",
        provider: "vimeo",
        lesson_type: "video",
        duration_minutes: ""
    });

    const [notice, setNotice] = useState(null);
    const [sending, setSending] = useState(false);


    const handleChange = (e) => {

        setForm({
            ...form,
            [e.target.name]:
                e.target.value
        });
    };


    const handleSubmit = async (e) => {

        e.preventDefault();

        setNotice(null);
        setSending(true);

        const payload = { ...form };

        if (payload.duration_minutes === "") {
            delete payload.duration_minutes;
        } else {
            payload.duration_minutes = Number(payload.duration_minutes);
        }

        try {

            await addLesson(
                courseId,
                payload
            );

            setNotice({
                type: "success",
                text: "Lección agregada correctamente.",
            });

            setForm({
                ...form,
                title: "",
                media_id: "",
                duration_minutes: ""
            });

            reload();

        } catch (err) {

            setNotice({
                type: "error",
                text: getErrorMessage(err, "No se pudo agregar la lección."),
            });

        } finally {
            setSending(false);
        }
    };

    // Árbol del Composite: módulos (acordeón) y lecciones (filas).
    const renderItems = (items) =>
        items.map((item, index) =>
            item.lesson_id ? (
                <li className="tree-lesson" key={item.lesson_id}>
                    <LessonIcon type={item.type} />
                    <span className="tree-lesson-title">{item.title}</span>
                    <span className="muted tree-lesson-meta">
                        {item.label || item.type} · {item.duration_minutes ?? 0} min · {item.provider}
                    </span>
                </li>
            ) : (
                <li key={`${item.title}-${index}`}>
                    <details className="disclosure" open>
                        <summary>
                            <span className="module-title">
                                <IconLayers size={16} />
                                {item.title}
                            </span>
                            <IconChevronDown size={16} className="chevron" />
                        </summary>
                        <ul className="tree">
                            {renderItems(item.items || [])}
                        </ul>
                    </details>
                </li>
            )
        );

    const renderContent = () => {
        if (loading && !data) {
            return <Loading text="Cargando contenido..." />;
        }

        if (error) {
            return (
                <ErrorState
                    error={error}
                    fallback="No se pudo cargar el contenido."
                    onRetry={reload}
                />
            );
        }

        const { content, summary } = data;

        return (
            <>
                <div className="panel">
                    <h2>Resumen del curso</h2>
                    <span className="badge badge-category-behavioral fit">Visitor</span>

                    <p className="meta-inline">
                        <span>
                            <IconLayers size={16} />
                            {summary.total_modules} módulos
                        </span>
                        <span>
                            <IconBook size={16} />
                            {summary.total_lessons} lecciones
                        </span>
                        <span>
                            <IconClock size={16} />
                            {summary.total_minutes} min en total
                        </span>
                    </p>

                    <p className="muted">
                        Por tipo:{" "}
                        {Object.entries(summary.lessons_by_type || {})
                            .map(([type, count]) => `${type}: ${count}`)
                            .join(", ") || "sin lecciones"}
                    </p>

                    {summary.syllabus_markdown && (
                        <details className="disclosure">
                            <summary>
                                Temario (Markdown)
                                <IconChevronDown size={16} className="chevron" />
                            </summary>
                            <div className="disclosure-body">
                                <pre className="code-block">
                                    {summary.syllabus_markdown}
                                </pre>
                            </div>
                        </details>
                    )}
                </div>

                <div className="panel">
                    <h2>Contenido actual</h2>

                    {!content.items || content.items.length === 0 ? (
                        <Empty icon={IconBook}>El curso aún no tiene lecciones.</Empty>
                    ) : (
                        <ul className="tree tree-root">
                            {renderItems(content.items)}
                        </ul>
                    )}
                </div>
            </>
        );
    };


    return (

        <Layout
            title="Administrar contenido"
            subtitle="Agrega lecciones por módulo. La vista previa muestra el árbol del curso."
            back={{ to: "/instructor/courses", label: "Mis cursos" }}
        >

            <CourseTabs courseId={courseId} />

            <Notice notice={notice} />

            <div className="split">

                <form
                    className="form-card"
                    onSubmit={
                        handleSubmit
                    }
                >
                    <section className="form-section">
                        <h2 className="form-section-title">Ubicación</h2>

                        <div className="field">
                            <label className="field-label" htmlFor="lesson-module">
                                Módulo
                            </label>
                            <input
                                id="lesson-module"
                                name="module_title"
                                value={form.module_title}
                                onChange={handleChange}
                                required
                            />
                            <span className="field-hint">
                                Si el módulo no existe, se crea.
                            </span>
                        </div>
                    </section>

                    <section className="form-section">
                        <h2 className="form-section-title">Lección</h2>

                        <div className="field">
                            <label className="field-label" htmlFor="lesson-title">
                                Nombre de la lección
                            </label>
                            <input
                                id="lesson-title"
                                name="title"
                                value={form.title}
                                onChange={handleChange}
                                required
                            />
                        </div>

                        <div className="field-row">
                            <div className="field">
                                <label className="field-label" htmlFor="lesson-type">
                                    Tipo de contenido
                                </label>
                                <select
                                    id="lesson-type"
                                    name="lesson_type"
                                    value={form.lesson_type}
                                    onChange={handleChange}
                                >
                                    <option value="video">
                                        Video
                                    </option>
                                    <option value="quiz">
                                        Quiz
                                    </option>
                                </select>
                            </div>

                            <div className="field">
                                <label className="field-label" htmlFor="lesson-duration">
                                    Duración (minutos)
                                </label>
                                <input
                                    id="lesson-duration"
                                    name="duration_minutes"
                                    type="number"
                                    min="1"
                                    value={form.duration_minutes}
                                    onChange={handleChange}
                                    placeholder="Opcional"
                                />
                            </div>
                        </div>
                    </section>

                    <section className="form-section">
                        <h2 className="form-section-title">Multimedia</h2>

                        <div className="field-row">
                            <div className="field">
                                <label className="field-label" htmlFor="lesson-provider">
                                    Proveedor
                                </label>
                                <select
                                    id="lesson-provider"
                                    name="provider"
                                    value={form.provider}
                                    onChange={handleChange}
                                >
                                    <option value="vimeo">
                                        Vimeo
                                    </option>
                                    <option value="s3">
                                        AWS S3
                                    </option>
                                </select>
                            </div>

                            <div className="field">
                                <label className="field-label" htmlFor="lesson-media">
                                    ID multimedia
                                </label>
                                <input
                                    id="lesson-media"
                                    name="media_id"
                                    value={form.media_id}
                                    onChange={handleChange}
                                    required
                                />
                            </div>
                        </div>
                    </section>

                    <div className="form-footer">
                        <button
                            type="submit"
                            className={`btn btn-primary${sending ? " is-loading" : ""}`}
                            disabled={sending}
                            aria-busy={sending}
                        >
                            Agregar lección
                        </button>
                    </div>

                </form>

                <aside className="split-aside" aria-label="Vista previa del curso">
                    {renderContent()}
                </aside>

            </div>

        </Layout>
    );
};


export default ManageContent;
