
import { useCallback, useState } from "react";
import Layout from "../../components/Layout";
import ProgressBar from "../../components/ProgressBar";
import StateBadge from "../../components/StateBadge";
import { Empty, ErrorState, Loading, Notice } from "../../components/Status";
import {
    IconActivity,
    IconBell,
    IconCard,
    IconChart,
    IconClipboard,
    IconCopy,
    IconLayers,
    IconLock,
    IconPlay,
    IconSparkle,
    IconStar
} from "../../components/icons";
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
import { getMyRecommendations, RULE_LABELS } from "../../services/recommendationService";
import { getMyPayments } from "../../services/paymentService";
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
    <ol className="lab-log">
        {steps.map((step, index) => (
            <li key={index} className={step.ok ? "ok" : "fail"}>
                <strong>{index + 1}. {step.label}</strong>
                <span className={`badge ${step.status === 200 ? "badge-success" : "badge-error"}`}>
                    {step.status === 200 ? "200 OK" : `${step.status ?? "sin respuesta"}`}
                </span>
                {step.data?.state && <StateBadge state={step.data.state} />}
                {step.detail && <span className="muted">{step.detail}</span>}
                <span className="muted lab-expected">
                    Esperado: {step.expected === "ok" ? "éxito" : step.expected}
                    {" · "}
                    {step.ok ? "cumple" : "no cumple"}
                </span>
            </li>
        ))}
    </ol>
);

// Esqueleto fijo de TemplatePaymentAdapter.process_payment (backend).
const TEMPLATE_STEPS = [
    { step: "Validar monto (> 0 y finito)", kind: "fijo" },
    { step: "Normalizar moneda a mayúsculas", kind: "fijo" },
    { step: "_prepare_amount (Stripe: centavos)", kind: "gancho" },
    { step: "_call_gateway (llamada al SDK)", kind: "abstracto" },
    { step: "_is_approved y _transaction_id", kind: "abstracto" },
    { step: "Error del SDK → rechazo, no HTTP 500", kind: "fijo" },
    { step: "_success_message / _failure_message", kind: "gancho" },
    { step: "Construir PaymentResult", kind: "fijo" },
];

const STEP_BADGE = {
    fijo: "badge-success",
    gancho: "badge-category-structural",
    abstracto: "badge-category-behavioral",
};

const CATEGORY = {
    creational: "Creacional",
    structural: "Estructural",
    behavioral: "Comportamiento",
};

// Tarjeta de un patrón: nombre, categoría GoF, descripción, acción y resultado.
const PatternCard = ({ name, category, icon: Icon, children }) => (
    <section className="card pattern-card" aria-labelledby={`patron-${name}`}>
        <div className="pattern-head">
            <span className="stat-icon" aria-hidden="true">
                <Icon size={22} />
            </span>
            <div className="pattern-name">
                <h2 id={`patron-${name}`}>{name}</h2>
                <span className={`badge badge-category-${category}`}>
                    {CATEGORY[category]}
                </span>
            </div>
        </div>
        {children}
    </section>
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

    // Strategy
    const [strategy, setStrategy] = useState(null);

    // Template Method
    const [payments, setPayments] = useState(null);

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

    // Strategy: el motor combina reglas intercambiables; se agrupa por regla.
    const runStrategyDemo = () =>
        withBusy("strategy", async () => {
            setStrategy(null);
            try {
                const items = await getMyRecommendations();
                const byRule = {};
                items.forEach((item) => {
                    (byRule[item.rule] ||= []).push(item);
                });
                setStrategy({ total: items.length, byRule });
            } catch (err) {
                setStrategy({ error: getErrorMessage(err, "No se pudieron calcular las recomendaciones.") });
            }
        });

    // Template Method: resultados reales producidos por el método plantilla.
    const runTemplateDemo = () =>
        withBusy("template", async () => {
            setPayments(null);
            try {
                setPayments({ items: await getMyPayments() });
            } catch (err) {
                setPayments({ error: getErrorMessage(err, "No se pudo cargar el historial de pagos.") });
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
    const noCourse = !selected;

    return (
        <Layout
            title="Laboratorio de patrones GoF"
            subtitle="Cada demostración llama a los endpoints reales del backend."
        >
            <section className="panel lab-course">
                <div className="field">
                    <label className="field-label" htmlFor="lab-course">
                        Curso de trabajo
                    </label>

                    {myCourses.length === 0 ? (
                        <Empty icon={IconLayers}>
                            Necesitas un curso propio para las demostraciones de
                            Observer, State y Visitor.
                        </Empty>
                    ) : (
                        <select
                            id="lab-course"
                            value={selected?.id || ""}
                            onChange={(e) => setCourseId(e.target.value)}
                        >
                            {myCourses.map((course) => (
                                <option key={course.id} value={course.id}>
                                    {course.title}
                                </option>
                            ))}
                        </select>
                    )}
                </div>
            </section>

            <div className="pattern-grid">

                <PatternCard name="Observer" category="behavioral" icon={IconBell}>
                    <p className="muted">
                        Programa, inicia y termina una clase en vivo. Al terminar se
                        publica <code>live_session_recorded</code> en el bus único;
                        los observadores de auditoría y notificaciones reaccionan sin
                        que el caso de uso los conozca.
                    </p>

                    <div>
                        <button
                            type="button"
                            className={`btn btn-primary btn-sm${busy === "observer" ? " is-loading" : ""}`}
                            disabled={noCourse || busy !== ""}
                            aria-busy={busy === "observer"}
                            onClick={runObserverDemo}
                        >
                            <IconPlay size={16} />
                            Ejecutar demostración
                        </button>
                    </div>

                    {observer?.error && (
                        <Notice notice={{ type: "error", text: observer.error }} />
                    )}

                    {observer && !observer.error && (
                        <div className="lab-result">
                            <p className="lab-result-line">
                                Clase <strong>{observer.session.title}</strong>
                                <StateBadge state={observer.session.state} />
                                {observer.session.recording_url && (
                                    <a
                                        href={observer.session.recording_url}
                                        target="_blank"
                                        rel="noreferrer"
                                    >
                                        Ver grabación
                                    </a>
                                )}
                            </p>

                            <div className="table-wrap">
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
                                                <td><code>{key}</code></td>
                                                <td>{observer.before?.[key]}</td>
                                                <td>
                                                    <strong>{observer.after?.[key]}</strong>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            <h3 className="lab-subtitle">Notificaciones nuevas para ti</h3>
                            {observer.newNotifications.length === 0 ? (
                                <p className="muted">Ninguna.</p>
                            ) : (
                                <ul className="lab-log">
                                    {observer.newNotifications.map((item) => (
                                        <li className="ok" key={item.notification_id}>
                                            <strong>{item.title}</strong>
                                            <span>{item.message}</span>
                                            <span className="badge">{item.event_type}</span>
                                        </li>
                                    ))}
                                </ul>
                            )}

                            {observer.audit && (
                                <>
                                    <h3 className="lab-subtitle">
                                        Auditoría (últimos live_session_recorded)
                                    </h3>
                                    <pre className="code-block">
                                        {JSON.stringify(
                                            observer.audit.map((entry) => ({
                                                fecha: new Date(entry.occurred_at).toLocaleString(),
                                                evento: entry.event_type,
                                                datos: entry.payload,
                                            })),
                                            null,
                                            2
                                        )}
                                    </pre>
                                </>
                            )}
                        </div>
                    )}
                </PatternCard>

                <PatternCard name="State" category="behavioral" icon={IconActivity}>
                    <p className="muted">
                        Crea una evaluación y prueba transiciones válidas e inválidas.
                        Cada estado (borrador, publicada, cerrada) decide qué
                        operaciones permite; las inválidas responden 409.
                    </p>

                    <div>
                        <button
                            type="button"
                            className={`btn btn-primary btn-sm${busy === "state" ? " is-loading" : ""}`}
                            disabled={noCourse || busy !== ""}
                            aria-busy={busy === "state"}
                            onClick={runStateDemo}
                        >
                            <IconPlay size={16} />
                            Ejecutar demostración
                        </button>
                    </div>

                    {stateSteps.length > 0 && (
                        <div className="lab-result">
                            <StepLog steps={stateSteps} />
                        </div>
                    )}
                </PatternCard>

                <PatternCard name="Visitor" category="behavioral" icon={IconLayers}>
                    <p className="muted">
                        Los visitantes recorren el árbol Composite (módulos y
                        lecciones) para calcular duración, resumen por tipo, temario
                        y progreso sin modificar las clases del contenido.
                    </p>

                    <div>
                        <button
                            type="button"
                            className={`btn btn-primary btn-sm${busy === "visitor" ? " is-loading" : ""}`}
                            disabled={noCourse || busy !== ""}
                            aria-busy={busy === "visitor"}
                            onClick={runVisitorDemo}
                        >
                            <IconChart size={16} />
                            Calcular resumen
                        </button>
                    </div>

                    {visitor?.error && (
                        <Notice notice={{ type: "error", text: visitor.error }} />
                    )}

                    {visitor?.summary && (
                        <div className="lab-result">
                            <p>
                                <strong>{visitor.summary.title}</strong>
                            </p>

                            <p className="meta-inline">
                                <span>{visitor.summary.total_modules} módulos</span>
                                <span>{visitor.summary.total_lessons} lecciones</span>
                                <span>{visitor.summary.total_minutes} min</span>
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
                        </div>
                    )}
                </PatternCard>

                <PatternCard name="Strategy" category="behavioral" icon={IconSparkle}>
                    <p className="muted">
                        El motor de recomendaciones combina reglas intercambiables
                        (refuerzo, siguiente nivel, afinidad, gratis para empezar,
                        popular). Cada recomendación indica qué estrategia la generó;
                        si dos reglas sugieren el mismo curso, gana el mayor puntaje.
                    </p>

                    <div>
                        <button
                            type="button"
                            className={`btn btn-primary btn-sm${busy === "strategy" ? " is-loading" : ""}`}
                            disabled={busy !== ""}
                            aria-busy={busy === "strategy"}
                            onClick={runStrategyDemo}
                        >
                            <IconPlay size={16} />
                            Calcular recomendaciones
                        </button>
                    </div>

                    {strategy?.error && (
                        <Notice notice={{ type: "error", text: strategy.error }} />
                    )}

                    {strategy && !strategy.error && (
                        <div className="lab-result">
                            {strategy.total === 0 ? (
                                <p className="muted">
                                    Ninguna regla produjo sugerencias (se excluyen tus
                                    cursos propios y en los que ya estás inscrito).
                                </p>
                            ) : (
                                <ul className="lab-log">
                                    {Object.entries(strategy.byRule).map(([rule, items]) => (
                                        <li className="ok" key={rule}>
                                            <strong>{RULE_LABELS[rule] || rule}</strong>
                                            <span className="badge">{rule}</span>
                                            {items.map((item) => (
                                                <span className="muted" key={item.course_id}>
                                                    {item.title} · puntaje {item.score} · {item.reason}
                                                </span>
                                            ))}
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>
                    )}
                </PatternCard>

                <PatternCard name="Template Method" category="behavioral" icon={IconCard}>
                    <p className="muted">
                        Todas las pasarelas (Stripe, Wompi) siguen el mismo algoritmo
                        de cobro, definido una sola vez en{" "}
                        <code>TemplatePaymentAdapter.process_payment</code>. Cada
                        pasarela solo implementa los pasos abstractos y, si quiere,
                        los ganchos.
                    </p>

                    <ol className="lab-log">
                        {TEMPLATE_STEPS.map(({ step, kind }, index) => (
                            <li className="ok" key={step}>
                                <strong>{index + 1}. {step}</strong>
                                <span className={`badge ${STEP_BADGE[kind]}`}>{kind}</span>
                            </li>
                        ))}
                    </ol>

                    <div>
                        <button
                            type="button"
                            className={`btn btn-primary btn-sm${busy === "template" ? " is-loading" : ""}`}
                            disabled={busy !== ""}
                            aria-busy={busy === "template"}
                            onClick={runTemplateDemo}
                        >
                            <IconPlay size={16} />
                            Ver pagos procesados
                        </button>
                    </div>

                    {payments?.error && (
                        <Notice notice={{ type: "error", text: payments.error }} />
                    )}

                    {payments && !payments.error && (
                        <div className="lab-result">
                            {payments.items.length === 0 ? (
                                <p className="muted">
                                    Aún no tienes pagos. Inicia sesión como estudiante y
                                    paga un curso desde el catálogo: el resultado lo
                                    construye el método plantilla.
                                </p>
                            ) : (
                                <div className="table-wrap">
                                    <table className="users-table">
                                        <thead>
                                            <tr>
                                                <th>Pasarela</th>
                                                <th>Estado</th>
                                                <th>Monto</th>
                                                <th>Mensaje</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {payments.items.map((p) => (
                                                <tr key={p.payment_id}>
                                                    <td><code>{p.gateway}</code></td>
                                                    <td>
                                                        <span className={`badge ${p.status === "approved" ? "badge-success" : "badge-error"}`}>
                                                            {p.status}
                                                        </span>
                                                    </td>
                                                    <td>{p.amount} {p.currency}</td>
                                                    <td>{p.message}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    )}
                </PatternCard>

                <PatternCard name="Proxy" category="structural" icon={IconLock}>
                    <p className="muted">
                        El acceso al contenido de un curso Premium lo
                        decide el proxy en el backend según el usuario
                        autenticado y su inscripción. Elige un curso:
                    </p>

                    {data.courses.length === 0 && (
                        <p className="muted">No hay cursos creados.</p>
                    )}

                    <div className="chip-list">
                        {data.courses.map((course) => (
                            <button
                                key={course.id}
                                type="button"
                                className="btn btn-secondary btn-sm"
                                disabled={busy !== ""}
                                onClick={() => checkAccess(course)}
                            >
                                {course.premium && <IconStar size={14} />}
                                {course.title}
                                {course.premium && <span className="sr-only"> (Premium)</span>}
                            </button>
                        ))}
                    </div>

                    {busy === "proxy" && <Loading text="Consultando..." />}

                    {proxyResult && (
                        proxyResult.ok ? (
                            <Notice
                                notice={{
                                    type: "success",
                                    text: `Acceso permitido: ${proxyResult.course} (${proxyResult.modules} módulos)`,
                                }}
                            />
                        ) : (
                            <Notice
                                notice={{
                                    type: "error",
                                    text: `Acceso denegado a ${proxyResult.course}: ${proxyResult.text}`,
                                }}
                            />
                        )
                    )}
                </PatternCard>

                <PatternCard name="Flyweight" category="structural" icon={IconCopy}>
                    <p className="muted">
                        Todas las lecciones del mismo tipo comparten un
                        único objeto de metadatos en el backend.
                    </p>

                    {data.metadata.length === 0 ? (
                        <p className="muted">No se pudieron cargar los metadatos.</p>
                    ) : (
                        <pre className="code-block">
                            {JSON.stringify(data.metadata, null, 2)}
                        </pre>
                    )}
                </PatternCard>

                <PatternCard name="Facade" category="structural" icon={IconClipboard}>
                    <p className="muted">
                        La gestión de cursos utiliza una fachada en el
                        backend para listar, crear, clonar e inscribir
                        estudiantes. Puedes verificarlo desde la sección
                        de gestión de cursos.
                    </p>
                </PatternCard>

            </div>
        </Layout>
    );
}

