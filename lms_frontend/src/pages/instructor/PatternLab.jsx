
import { useCallback, useState } from "react";
import Layout from "../../components/Layout";
import ProgressBar from "../../components/ProgressBar";
import StateBadge from "../../components/StateBadge";
import { Empty, ErrorState, Loading } from "../../components/Status";
import { useAuth } from "../../context/auth-context";
import { useResource } from "../../hooks/useResource";
import {
    getCourses,
    getCourseContent,
    getContentMetadata,
    getCourseSummary
} from "../../services/courseService";
import {
    addQuestion,
    closeAssessment,
    createAssessment,
    publishAssessment
} from "../../services/assessmentService";
import {
    createLiveSession,
    endLiveSession,
    startLiveSession
} from "../../services/liveSessionService";
import { getMyNotifications } from "../../services/notificationService";
import { getAuditLog, getHealth } from "../../services/adminService";
import { getMyProgress } from "../../services/progressService";
import { getErrorMessage, getErrorStatus } from "../../services/errors";

const CONTENT_TYPES = ["video", "quiz", "document"];

const loadLab = async () => {
    const [courses, metadata] = await Promise.all([
        getCourses(),
        // Flyweight: los datos vienen de la fábrica del backend.
        Promise.all(CONTENT_TYPES.map(getContentMetadata)).catch(() => []),
    ]);

    return { courses, metadata };
};

// Ejecuta un paso contra la API y lo registra con el resultado esperado.
const runStep = async (label, expected, action) => {
    try {
        const data = await action();
        return { label, expected, status: 200, ok: expected === "ok", data, detail: "" };
    } catch (err) {
        const status = getErrorStatus(err);
        return {
            label,
            expected,
            status,
            ok: expected === status,
            data: null,
            detail: getErrorMessage(err, "Error"),
        };
    }
};

const StepLog = ({ steps }) => (
    <ul className="lab-log">
        {steps.map((step, index) => (
            <li key={index} className={step.ok ? "ok" : "fail"}>
                <strong>{index + 1}. {step.label}</strong>
                {" -> "}
                {step.status === 200 ? "200 OK" : `${step.status ?? "sin respuesta"}`}
                {step.data?.state && (
                    <>
                        {" "}<StateBadge state={step.data.state} />
                    </>
                )}
                {step.detail && <span className="muted"> {step.detail}</span>}
                <span className="muted">
                    {" "}(esperado: {step.expected === "ok" ? "éxito" : step.expected})
                </span>
            </li>
        ))}
    </ul>
);

export default function PatternLab() {
    const { user } = useAuth();
    const isAdmin = user?.role === "admin";

    const { data, error, loading, reload } = useResource(loadLab);

    const [courseId, setCourseId] = useState("");
    const [busy, setBusy] = useState("");

    // Proxy
    const [proxyResult, setProxyResult] = useState(null);

    // Observer
    const [observer, setObserver] = useState(null);

    // State
    const [stateSteps, setStateSteps] = useState([]);

    // Visitor
    const [visitor, setVisitor] = useState(null);

    // Instructor: solo sus cursos (el backend exige ser dueño). Admin: todos.
    const myCourses = (data?.courses || []).filter(
        (course) => isAdmin || course.instructor_id === user?.user_id
    );
    const selected = myCourses.find((course) => course.id === courseId) || myCourses[0];

    const withBusy = useCallback(async (key, fn) => {
        setBusy(key);
        try {
            await fn();
        } finally {
            setBusy("");
        }
    }, []);

    // Proxy: el backend decide con el token del usuario autenticado.
    const checkAccess = (course) =>
        withBusy("proxy", async () => {
            setProxyResult(null);
            try {
                const content = await getCourseContent(course.id);
                setProxyResult({ ok: true, course: course.title, modules: content.items?.length ?? 0 });
            } catch (err) {
                setProxyResult({
                    ok: false,
                    course: course.title,
                    text: getErrorMessage(err, "No fue posible consultar el contenido."),
                });
            }
        });

    // Observer: una acción publica LIVE_SESSION_RECORDED en el bus; se compara
    // el estado de los observadores (auditoría, notificaciones) antes y después.
    const runObserverDemo = () =>
        withBusy("observer", async () => {
            setObserver(null);

            if (!selected) {
                return;
            }

            try {
                const [healthBefore, notificationsBefore] = await Promise.all([
                    getHealth(),
                    getMyNotifications(),
                ]);

                const session = await createLiveSession({
                    course_id: selected.id,
                    title: `Demo Observer ${new Date().toLocaleTimeString()}`,
                    duration_minutes: 30,
                });
                await startLiveSession(session.id);
                const ended = await endLiveSession(session.id);

                const [healthAfter, notificationsAfter, audit] = await Promise.all([
                    getHealth(),
                    getMyNotifications(),
                    isAdmin
                        ? getAuditLog({ eventType: "live_session_recorded", limit: 5 })
                        : Promise.resolve(null),
                ]);

                const previousIds = new Set(
                    notificationsBefore.map((item) => item.notification_id)
                );

                setObserver({
                    session: ended,
                    before: healthBefore.counters,
                    after: healthAfter.counters,
                    newNotifications: notificationsAfter.filter(
                        (item) => !previousIds.has(item.notification_id)
                    ),
                    audit,
                });
            } catch (err) {
                setObserver({ error: getErrorMessage(err, "Falló la demostración.") });
            }
        });

    // State: transiciones válidas e inválidas de una evaluación nueva.
    const runStateDemo = () =>
        withBusy("state", async () => {
            setStateSteps([]);

            if (!selected) {
                return;
            }

            const steps = [];
            const push = (step) => {
                steps.push(step);
                setStateSteps([...steps]);
            };

            const created = await runStep("Crear evaluación (borrador)", "ok", () =>
                createAssessment({
                    course_id: selected.id,
                    title: `Demo State ${new Date().toLocaleTimeString()}`,
                    description: "Creada por el laboratorio de patrones",
                    passing_score: 60,
                    max_attempts: 1,
                })
            );
            push(created);

            if (!created.data) {
                return;
            }

            const id = created.data.id;

            push(await runStep("Publicar sin preguntas", 409, () => publishAssessment(id)));
            push(await runStep("Cerrar en borrador", 409, () => closeAssessment(id)));
            push(await runStep("Agregar pregunta en borrador", "ok", () =>
                addQuestion(id, {
                    text: "¿Qué patrón cambia el comportamiento según el estado?",
                    options: ["Observer", "State", "Visitor"],
                    correct_option: 1,
                    points: 1,
                })
            ));
            push(await runStep("Publicar", "ok", () => publishAssessment(id)));
            push(await runStep("Agregar pregunta ya publicada", 409, () =>
                addQuestion(id, {
                    text: "Pregunta tardía",
                    options: ["Sí", "No"],
                    correct_option: 0,
                })
            ));
            push(await runStep("Publicar de nuevo", 409, () => publishAssessment(id)));
            push(await runStep("Cerrar", "ok", () => closeAssessment(id)));
            push(await runStep("Cerrar de nuevo", 409, () => closeAssessment(id)));
            push(await runStep("Publicar cerrada", 409, () => publishAssessment(id)));
        });

    // Visitor: duración, resumen por tipo y progreso sobre el Composite.
    const runVisitorDemo = () =>
        withBusy("visitor", async () => {
            setVisitor(null);

            if (!selected) {
                return;
            }

            try {
                const [summary, progress] = await Promise.all([
                    getCourseSummary(selected.id),
                    getMyProgress(selected.id).catch(() => null),
                ]);
                setVisitor({ summary, progress });
            } catch (err) {
                setVisitor({ error: getErrorMessage(err, "No se pudo calcular el resumen.") });
            }
        });

    if (loading && !data) {
        return (
            <Layout title="Laboratorio de patrones GoF">
                <Loading />
            </Layout>
        );
    }

    if (error) {
        return (
            <Layout title="Laboratorio de patrones GoF">
                <ErrorState error={error} onRetry={reload} />
            </Layout>
        );
    }

    const counterKeys = ["audit_events", "notifications", "live_sessions"];

    return (
        <Layout
            title="Laboratorio de patrones GoF"
            subtitle="Cada demostración llama a los endpoints reales del backend."
        >
            <section className="panel">
                <h2>Curso de trabajo</h2>

                {myCourses.length === 0 ? (
                    <Empty>
                        Necesitas un curso propio para las demostraciones de
                        Observer, State y Visitor.
                    </Empty>
                ) : (
                    <select
                        value={selected?.id || ""}
                        onChange={(e) => setCourseId(e.target.value)}
                        aria-label="Curso para las demostraciones"
                    >
                        {myCourses.map((course) => (
                            <option key={course.id} value={course.id}>
                                {course.title}
                            </option>
                        ))}
                    </select>
                )}
            </section>

            <section className="panel">
                <h2>Observer: eventos del dominio</h2>
                <p>
                    Programa, inicia y termina una clase en vivo. Al terminar se
                    publica <code>live_session_recorded</code> en el bus único;
                    los observadores de auditoría y notificaciones reaccionan sin
                    que el caso de uso los conozca.
                </p>

                <button
                    type="button"
                    className="btn-primary"
                    disabled={!selected || busy !== ""}
                    onClick={runObserverDemo}
                >
                    {busy === "observer" ? "Ejecutando..." : "Ejecutar demostración"}
                </button>

                {observer?.error && <p className="error">{observer.error}</p>}

                {observer && !observer.error && (
                    <>
                        <p>
                            Clase <strong>{observer.session.title}</strong>:{" "}
                            <StateBadge state={observer.session.state} />
                            {observer.session.recording_url && (
                                <a
                                    href={observer.session.recording_url}
                                    target="_blank"
                                    rel="noreferrer"
                                >
                                    grabación
                                </a>
                            )}
                        </p>

                        <table className="users-table">
                            <thead>
                                <tr>
                                    <th>Contador (/health)</th>
                                    <th>Antes</th>
                                    <th>Después</th>
                                </tr>
                            </thead>
                            <tbody>
                                {counterKeys.map((key) => (
                                    <tr key={key}>
                                        <td>{key}</td>
                                        <td>{observer.before?.[key]}</td>
                                        <td>{observer.after?.[key]}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>

                        <h3>Notificaciones nuevas para ti</h3>
                        {observer.newNotifications.length === 0 ? (
                            <p className="muted">Ninguna.</p>
                        ) : (
                            <ul className="lab-log">
                                {observer.newNotifications.map((item) => (
                                    <li className="ok" key={item.notification_id}>
                                        <strong>{item.title}</strong>: {item.message}{" "}
                                        <span className="muted">({item.event_type})</span>
                                    </li>
                                ))}
                            </ul>
                        )}

                        {observer.audit && (
                            <>
                                <h3>Auditoría (últimos live_session_recorded)</h3>
                                <ul className="lab-log">
                                    {observer.audit.map((entry) => (
                                        <li key={entry.event_id}>
                                            {new Date(entry.occurred_at).toLocaleString()} -{" "}
                                            {entry.event_type} -{" "}
                                            <code>{JSON.stringify(entry.payload)}</code>
                                        </li>
                                    ))}
                                </ul>
                            </>
                        )}
                    </>
                )}
            </section>

            <section className="panel">
                <h2>State: ciclo de vida de una evaluación</h2>
                <p>
                    Crea una evaluación y prueba transiciones válidas e inválidas.
                    Cada estado (borrador, publicada, cerrada) decide qué
                    operaciones permite; las inválidas responden 409.
                </p>

                <button
                    type="button"
                    className="btn-primary"
                    disabled={!selected || busy !== ""}
                    onClick={runStateDemo}
                >
                    {busy === "state" ? "Ejecutando..." : "Ejecutar demostración"}
                </button>

                {stateSteps.length > 0 && <StepLog steps={stateSteps} />}
            </section>

            <section className="panel">
                <h2>Visitor: operaciones sobre el contenido</h2>
                <p>
                    Los visitantes recorren el árbol Composite (módulos y
                    lecciones) para calcular duración, resumen por tipo, temario
                    y progreso sin modificar las clases del contenido.
                </p>

                <button
                    type="button"
                    className="btn-primary"
                    disabled={!selected || busy !== ""}
                    onClick={runVisitorDemo}
                >
                    {busy === "visitor" ? "Calculando..." : "Calcular resumen"}
                </button>

                {visitor?.error && <p className="error">{visitor.error}</p>}

                {visitor?.summary && (
                    <>
                        <p>
                            <strong>{visitor.summary.title}</strong>:{" "}
                            {visitor.summary.total_modules} módulos -{" "}
                            {visitor.summary.total_lessons} lecciones -{" "}
                            {visitor.summary.total_minutes} min
                        </p>

                        <p className="muted">
                            Lecciones por tipo:{" "}
                            {Object.entries(visitor.summary.lessons_by_type || {})
                                .map(([type, count]) => `${type}: ${count}`)
                                .join(", ") || "ninguna"}
                        </p>

                        {visitor.progress ? (
                            <ProgressBar progress={visitor.progress} />
                        ) : (
                            <p className="muted">Sin progreso registrado.</p>
                        )}

                        {visitor.summary.syllabus_markdown && (
                            <pre className="code-block">
                                {visitor.summary.syllabus_markdown}
                            </pre>
                        )}
                    </>
                )}
            </section>

            <section className="panel">
                <h2>Proxy: control de acceso</h2>
                <p>
                    El acceso al contenido de un curso Premium lo
                    decide el proxy en el backend según el usuario
                    autenticado y su inscripción. Elige un curso:
                </p>

                {data.courses.length === 0 && <p>No hay cursos creados.</p>}

                <div className="actions">
                    {data.courses.map((course) => (
                        <button
                            key={course.id}
                            type="button"
                            className="btn-secondary"
                            disabled={busy !== ""}
                            onClick={() => checkAccess(course)}
                        >
                            {course.title}
                            {course.premium ? " (Premium)" : ""}
                        </button>
                    ))}
                </div>

                {busy === "proxy" && <p>Consultando...</p>}

                {proxyResult && (
                    proxyResult.ok ? (
                        <p className="success">
                            Acceso permitido: {proxyResult.course} ({proxyResult.modules} módulos)
                        </p>
                    ) : (
                        <p className="error">
                            Acceso denegado a {proxyResult.course}: {proxyResult.text}
                        </p>
                    )
                )}
            </section>

            <section className="panel">
                <h2>Flyweight: tipos de contenido</h2>
                <p>
                    Todas las lecciones del mismo tipo comparten un
                    único objeto de metadatos en el backend.
                </p>

                <div className="course-grid">
                    {data.metadata.map((item) => (
                        <article
                            className="course-card"
                            key={item.content_type}
                        >
                            <h3>{item.label}</h3>
                            <p>Tipo: {item.content_type}</p>
                            <p>Icono: {item.icon}</p>
                        </article>
                    ))}
                </div>
            </section>

            <section className="panel">
                <h2>Facade: operaciones centralizadas</h2>
                <p>
                    La gestión de cursos utiliza una fachada en el
                    backend para listar, crear, clonar e inscribir
                    estudiantes. Puedes verificarlo desde la sección
                    de gestión de cursos.
                </p>
            </section>
        </Layout>
    );
}
