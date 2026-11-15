import { useCallback, useState } from "react";
import { Link, useParams } from "react-router-dom";

import Layout from "../../components/Layout";
import LiveSessionCard from "../../components/LiveSessionCard";
import { Empty, ErrorState, Loading, Notice } from "../../components/Status";
import { useResource } from "../../hooks/useResource";
import {
    createLiveSession,
    endLiveSession,
    getCourseLiveSessions,
    startLiveSession
} from "../../services/liveSessionService";
import { getErrorMessage, getErrorStatus } from "../../services/errors";

const EMPTY_FORM = {
    title: "",
    scheduled_at: "",
    duration_minutes: 60,
};

const ManageLiveSessions = () => {

    const { courseId } = useParams();

    const loader = useCallback(
        () => getCourseLiveSessions(courseId),
        [courseId]
    );

    const { data, error, loading, reload } = useResource(loader);

    const [form, setForm] = useState(EMPTY_FORM);
    const [notice, setNotice] = useState(null);
    const [busyId, setBusyId] = useState(null);

    const handleChange = (e) =>
        setForm({ ...form, [e.target.name]: e.target.value });

    const handleCreate = async (e) => {
        e.preventDefault();
        setNotice(null);
        setBusyId("new");

        const payload = {
            course_id: courseId,
            title: form.title,
            duration_minutes: Number(form.duration_minutes),
        };

        if (form.scheduled_at) {
            // datetime-local no trae zona horaria: se envía en ISO (UTC).
            payload.scheduled_at = new Date(form.scheduled_at).toISOString();
        }

        try {
            const created = await createLiveSession(payload);

            setNotice({
                type: "success",
                text: `Clase "${created.title}" programada.`,
            });
            setForm(EMPTY_FORM);
            reload();

        } catch (err) {
            setNotice({
                type: "error",
                text: getErrorMessage(err, "No se pudo programar la clase."),
            });
        } finally {
            setBusyId(null);
        }
    };

    // State: scheduled -> live -> recorded. El backend responde 409 si no aplica.
    const runTransition = async (session, action, label) => {
        setNotice(null);
        setBusyId(session.id);

        try {
            const updated = await action(session.id);

            setNotice({
                type: "success",
                text: `${label}: "${updated.title}" ahora está en estado "${updated.state}".`,
            });
            reload();

        } catch (err) {
            setNotice({
                type: "error",
                text:
                    (getErrorStatus(err) === 409 ? "Transición no permitida: " : "") +
                    getErrorMessage(err, "No se pudo cambiar el estado de la clase."),
            });
        } finally {
            setBusyId(null);
        }
    };

    const renderList = () => {
        if (loading && !data) {
            return <Loading text="Cargando clases..." />;
        }

        if (error) {
            return (
                <ErrorState
                    error={error}
                    fallback="No se pudieron cargar las clases."
                    onRetry={reload}
                />
            );
        }

        if (!data || data.length === 0) {
            return <Empty>No hay clases programadas para este curso.</Empty>;
        }

        return (
            <div className="course-grid">
                {data.map((session) => (
                    <LiveSessionCard key={session.id} session={session}>
                        <div className="actions">
                            <button
                                type="button"
                                className="btn-primary"
                                disabled={busyId === session.id || session.state !== "scheduled"}
                                onClick={() =>
                                    runTransition(session, startLiveSession, "Iniciada")
                                }
                            >
                                Iniciar
                            </button>

                            <button
                                type="button"
                                className="btn-danger"
                                disabled={busyId === session.id || session.state !== "live"}
                                onClick={() =>
                                    runTransition(session, endLiveSession, "Terminada")
                                }
                            >
                                Terminar
                            </button>
                        </div>
                    </LiveSessionCard>
                ))}
            </div>
        );
    };

    return (
        <Layout
            title="Clases en vivo"
            subtitle="Videoconferencia simulada. Al terminar, la clase queda grabada y se notifica a los inscritos."
        >
            <div className="actions">
                <Link to="/instructor/courses">Volver a mis cursos</Link>
                <Link to={`/instructor/course/${courseId}/content`}>Contenido</Link>
                <Link to={`/instructor/course/${courseId}/assessments`}>Evaluaciones</Link>
            </div>

            <Notice notice={notice} />

            <form className="course-form" onSubmit={handleCreate}>
                <h3>Programar clase</h3>

                <label>Título</label>
                <input
                    name="title"
                    value={form.title}
                    onChange={handleChange}
                    required
                />

                <label>Fecha y hora (opcional)</label>
                <input
                    name="scheduled_at"
                    type="datetime-local"
                    value={form.scheduled_at}
                    onChange={handleChange}
                />

                <label>Duración (minutos)</label>
                <input
                    name="duration_minutes"
                    type="number"
                    min="1"
                    value={form.duration_minutes}
                    onChange={handleChange}
                />

                <button
                    type="submit"
                    className="btn-primary"
                    disabled={busyId === "new"}
                >
                    Programar
                </button>
            </form>

            {renderList()}
        </Layout>
    );
};

export default ManageLiveSessions;
