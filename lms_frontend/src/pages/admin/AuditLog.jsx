import { useCallback, useState } from "react";

import Layout from "../../components/Layout";
import { Empty, ErrorState, Loading } from "../../components/Status";
import { useResource } from "../../hooks/useResource";
import { EVENT_TYPES, getAuditLog } from "../../services/adminService";


const shortId = (id) => (id ? `${String(id).slice(0, 8)}...` : "-");

// Log de auditoría alimentado por AuditLogObserver (patrón Observer).
const AuditLog = () => {

    const [eventType, setEventType] = useState("");
    const [limit, setLimit] = useState(100);

    const loader = useCallback(
        () => getAuditLog({ eventType, limit }),
        [eventType, limit]
    );

    const { data, error, loading, reload } = useResource(loader);

    const renderBody = () => {
        if (loading) {
            return <Loading text="Cargando eventos..." />;
        }

        if (error) {
            return (
                <ErrorState
                    error={error}
                    fallback="No se pudo cargar el log de auditoría."
                    onRetry={reload}
                />
            );
        }

        if (!data || data.length === 0) {
            return <Empty>No hay eventos registrados para este filtro.</Empty>;
        }

        return (
            <table className="users-table">
                <thead>
                    <tr>
                        <th>Fecha</th>
                        <th>Evento</th>
                        <th>Usuario</th>
                        <th>Curso</th>
                        <th>Datos</th>
                    </tr>
                </thead>
                <tbody>
                    {data.map((entry) => (
                        <tr key={entry.event_id}>
                            <td>{new Date(entry.occurred_at).toLocaleString()}</td>
                            <td>
                                <span className="badge">{entry.event_type}</span>
                            </td>
                            <td title={entry.user_id || ""}>{shortId(entry.user_id)}</td>
                            <td title={entry.course_id || ""}>{shortId(entry.course_id)}</td>
                            <td>
                                <code>{JSON.stringify(entry.payload || {})}</code>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        );
    };

    return (
        <Layout
            title="Log de auditoría"
            subtitle="Eventos del dominio publicados en el bus y registrados por el observador de auditoría."
        >
            <div className="actions">
                <select
                    value={eventType}
                    onChange={(e) => setEventType(e.target.value)}
                    aria-label="Filtrar por tipo de evento"
                >
                    <option value="">Todos los eventos</option>
                    {EVENT_TYPES.map((type) => (
                        <option key={type} value={type}>
                            {type}
                        </option>
                    ))}
                </select>

                <select
                    value={limit}
                    onChange={(e) => setLimit(Number(e.target.value))}
                    aria-label="Cantidad de eventos"
                >
                    {[50, 100, 500].map((value) => (
                        <option key={value} value={value}>
                            Últimos {value}
                        </option>
                    ))}
                </select>

                <button type="button" className="btn-secondary" onClick={reload}>
                    Actualizar
                </button>
            </div>

            {renderBody()}
        </Layout>
    );
};

export default AuditLog;
