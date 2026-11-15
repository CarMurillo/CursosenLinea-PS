import { useCallback, useState } from "react";
import { Link, useParams } from "react-router-dom";

import Layout from "../../components/Layout";
import { Empty, ErrorState, Loading, Notice } from "../../components/Status";
import { useResource } from "../../hooks/useResource";
import {
    addLesson,
    getCourseContent,
    getCourseSummary
} from "../../services/courseService";
import { getErrorMessage } from "../../services/errors";


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

    const renderItems = (items) =>
        items.map((item, index) =>
            item.lesson_id ? (
                <p key={item.lesson_id}>
                    {item.title}
                    {" - "}
                    {item.label || item.type}
                    {" - "}
                    {item.duration_minutes ?? 0} min
                    {" - "}
                    {item.provider}
                </p>
            ) : (
                <div
                    className="dashboard-card"
                    key={`${item.title}-${index}`}
                >
                    <h3>{item.title}</h3>
                    {renderItems(item.items || [])}
                </div>
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
                    <h2>Resumen del curso (Visitor)</h2>

                    <p>
                        {summary.total_modules} módulos -{" "}
                        {summary.total_lessons} lecciones -{" "}
                        {summary.total_minutes} min en total
                    </p>

                    <p className="muted">
                        Por tipo:{" "}
                        {Object.entries(summary.lessons_by_type || {})
                            .map(([type, count]) => `${type}: ${count}`)
                            .join(", ") || "sin lecciones"}
                    </p>

                    {summary.syllabus_markdown && (
                        <details>
                            <summary>Temario (Markdown)</summary>
                            <pre className="code-block">
                                {summary.syllabus_markdown}
                            </pre>
                        </details>
                    )}
                </div>

                <h2 style={{ marginTop: 25 }}>
                    Contenido actual
                </h2>

                {!content.items || content.items.length === 0 ? (
                    <Empty>El curso aún no tiene lecciones.</Empty>
                ) : (
                    <div className="dashboard-cards">
                        {renderItems(content.items)}
                    </div>
                )}
            </>
        );
    };


    return (

        <Layout title="Administrar contenido">

            <div className="actions">
                <Link to="/instructor/courses">Volver a mis cursos</Link>
                <Link to={`/instructor/course/${courseId}/assessments`}>
                    Evaluaciones
                </Link>
                <Link to={`/instructor/course/${courseId}/live`}>
                    Clases en vivo
                </Link>
            </div>

            <Notice notice={notice} />

            <form
                className="course-form"
                onSubmit={
                    handleSubmit
                }
            >

                <label>
                    Módulo
                </label>

                <input
                    name="module_title"
                    value={
                        form.module_title
                    }
                    onChange={
                        handleChange
                    }
                    required
                />


                <label>
                    Nombre de la lección
                </label>

                <input
                    name="title"
                    value={
                        form.title
                    }
                    onChange={
                        handleChange
                    }
                    required
                />


                <label>
                    ID multimedia
                </label>

                <input
                    name="media_id"
                    value={
                        form.media_id
                    }
                    onChange={
                        handleChange
                    }
                    required
                />


                <label>
                    Duración (minutos)
                </label>

                <input
                    name="duration_minutes"
                    type="number"
                    min="1"
                    value={form.duration_minutes}
                    onChange={handleChange}
                    placeholder="Opcional"
                />


                <label>
                    Proveedor
                </label>

                <select
                    name="provider"
                    value={
                        form.provider
                    }
                    onChange={
                        handleChange
                    }
                >

                    <option value="vimeo">
                        Vimeo
                    </option>

                    <option value="s3">
                        AWS S3
                    </option>

                </select>


                <label>
                    Tipo de contenido
                </label>

                <select
                    name="lesson_type"
                    value={
                        form.lesson_type
                    }
                    onChange={
                        handleChange
                    }
                >

                    <option value="video">
                        Video
                    </option>

                    <option value="quiz">
                        Quiz
                    </option>

                </select>


                <button
                    type="submit"
                    className="btn-primary"
                    disabled={sending}
                >
                    Agregar lección
                </button>

            </form>

            {renderContent()}

        </Layout>
    );
};


export default ManageContent;
