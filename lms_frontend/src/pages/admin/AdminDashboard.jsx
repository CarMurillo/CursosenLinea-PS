import Layout from "../../components/Layout";
import { QuickLink, StatCard } from "../../components/StatCard";
import { ErrorState, Loading } from "../../components/Status";
import {
    IconActivity,
    IconAward,
    IconBell,
    IconBook,
    IconBroadcast,
    IconCard,
    IconClipboard,
    IconFlask,
    IconLayers,
    IconQuiz,
    IconRefresh,
    IconUsers
} from "../../components/icons";
import { useResource } from "../../hooks/useResource";
import { getHealth } from "../../services/adminService";
import { getUsers } from "../../services/userService";

const COUNTER_LABELS = {
    courses: "Cursos",
    enrollments: "Inscripciones",
    payments: "Pagos",
    assessments: "Evaluaciones",
    live_sessions: "Clases en vivo",
    certificates: "Certificados",
    notifications: "Notificaciones",
    audit_events: "Eventos auditados",
    event_observers: "Observadores registrados",
};

const COUNTER_ICONS = {
    courses: IconLayers,
    enrollments: IconBook,
    payments: IconCard,
    assessments: IconQuiz,
    live_sessions: IconBroadcast,
    certificates: IconAward,
    notifications: IconBell,
    audit_events: IconClipboard,
    event_observers: IconActivity,
};

const AdminDashboard = () => {

    const { data: health, error, loading, reload } = useResource(getHealth);
    const { data: users, loading: loadingUsers } = useResource(getUsers);

    const renderHealth = () => {
        if (loading && !health) {
            return <Loading text="Consultando estado del servicio..." />;
        }

        if (error) {
            return (
                <ErrorState
                    error={error}
                    fallback="No se pudo consultar /health."
                    onRetry={reload}
                />
            );
        }

        const healthy = health.status === "ok";

        return (
            <div className="panel">
                <div className="card-head">
                    <div className="health-title">
                        <h2>Estado del servicio</h2>
                        <span className={`badge ${healthy ? "badge-success" : "badge-error"}`}>
                            {healthy ? "Operativo" : health.status}
                        </span>
                    </div>

                    <button type="button" className="btn btn-secondary btn-sm" onClick={reload}>
                        <IconRefresh size={16} />
                        Actualizar
                    </button>
                </div>

                <p className="muted">
                    {health.app} v{health.version} · BD: {String(health.database)} ·
                    activo hace {Math.round(health.uptime_seconds)} s
                </p>

                <div className="stat-grid">
                    {Object.entries(health.counters || {}).map(([key, value]) => (
                        <StatCard
                            key={key}
                            icon={COUNTER_ICONS[key] || IconActivity}
                            label={COUNTER_LABELS[key] || key}
                            value={value}
                        />
                    ))}
                </div>
            </div>
        );
    };

    const totalCourses = health?.counters?.courses;

    return (
        <Layout
            title="Panel de administración"
            subtitle="Administración general del LMS."
        >
            <section className="section" aria-labelledby="indicadores">
                <h2 id="indicadores" className="sr-only">Indicadores</h2>

                <div className="stat-grid">
                    <StatCard
                        icon={IconUsers}
                        label="Usuarios registrados"
                        value={loadingUsers && !users ? "…" : users?.length}
                    />
                    <StatCard
                        icon={IconLayers}
                        tone="violet"
                        label="Cursos"
                        value={loading && !health ? "…" : totalCourses}
                    />
                    <StatCard
                        icon={IconBook}
                        tone="success"
                        label="Inscripciones"
                        value={loading && !health ? "…" : health?.counters?.enrollments}
                    />
                </div>
            </section>

            <section className="section" aria-labelledby="accesos">
                <h2 id="accesos">Accesos rápidos</h2>

                <div className="quick-grid">
                    <QuickLink
                        to="/admin/users"
                        icon={IconUsers}
                        title="Usuarios"
                        text="Gestionar usuarios registrados."
                    />
                    <QuickLink
                        to="/admin/courses"
                        icon={IconLayers}
                        tone="violet"
                        title="Cursos"
                        text="Consultar cursos del sistema."
                    />
                    <QuickLink
                        to="/admin/audit-log"
                        icon={IconClipboard}
                        title="Auditoría"
                        text="Eventos del dominio registrados por el Observer."
                    />
                    <QuickLink
                        to="/patterns"
                        icon={IconFlask}
                        tone="accent"
                        title="Laboratorio de patrones"
                        text="Demostraciones contra la API real."
                    />
                </div>
            </section>

            <section className="section" aria-label="Actividad del sistema">
                {renderHealth()}
            </section>
        </Layout>
    );
};

export default AdminDashboard;
