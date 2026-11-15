import { Link } from "react-router-dom";

import Layout from "../../components/Layout";
import { ErrorState, Loading } from "../../components/Status";
import { useResource } from "../../hooks/useResource";
import { getHealth } from "../../services/adminService";

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

const AdminDashboard = () => {

    const { data: health, error, loading, reload } = useResource(getHealth);

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

        return (
            <div className="panel">
                <h2>
                    Estado del servicio:{" "}
                    <span className={health.status === "ok" ? "success" : "error"}>
                        {health.status}
                    </span>
                </h2>

                <p className="muted">
                    {health.app} v{health.version} - BD: {String(health.database)} -
                    activo hace {Math.round(health.uptime_seconds)} s
                </p>

                <div className="dashboard-cards">
                    {Object.entries(health.counters || {}).map(([key, value]) => (
                        <div className="dashboard-card" key={key}>
                            <h3>{value}</h3>
                            <p>{COUNTER_LABELS[key] || key}</p>
                        </div>
                    ))}
                </div>

                <button type="button" className="btn-secondary" onClick={reload}>
                    Actualizar
                </button>
            </div>
        );
    };

    return (
        <Layout
            title="Panel de administración"
            subtitle="Administración general del LMS."
        >
            <div className="dashboard-cards">

                <div className="dashboard-card">
                    <h3>Usuarios</h3>
                    <p>
                        Gestionar usuarios registrados.
                    </p>
                    <Link to="/admin/users">Ver usuarios</Link>
                </div>

                <div className="dashboard-card">
                    <h3>Cursos</h3>
                    <p>
                        Consultar cursos del sistema.
                    </p>
                    <Link to="/admin/courses">Ver cursos</Link>
                </div>

                <div className="dashboard-card">
                    <h3>Auditoría</h3>
                    <p>
                        Eventos del dominio registrados por el Observer.
                    </p>
                    <Link to="/admin/audit-log">Ver log</Link>
                </div>

            </div>

            {renderHealth()}
        </Layout>
    );
};

export default AdminDashboard;
