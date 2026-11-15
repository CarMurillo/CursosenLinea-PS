import { useCallback, useState } from "react";

import Layout from "../../components/Layout";
import { Empty, ErrorState, Loading } from "../../components/Status";
import { IconClipboard, IconRefresh } from "../../components/icons";
import { useResource } from "../../hooks/useResource";
import { EVENT_TYPES, getAuditLog } from "../../services/adminService";
import { formatDateTime } from "../../utils/format";


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
            return (
                <Empty icon={IconClipboard}>
                    No hay eventos registrados para este filtro.
                </Empty>
            );
        }

        return (
            <div className="table-wrap table-wrap-scroll">
                <table className="users-table">
                    <caption className="sr-only">Eventos de auditoría</caption>
                    <thead>
                        <tr>
                            <th scope="col">Fecha</th>
                            <th scope="col">Evento</th>
                            <th scope="col">Usuario</th>
                            <th scope="col">Curso</th>
                            <th scope="col">Datos</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.map((entry) => (
                            <tr key={entry.event_id}>
                                <td className="cell-nowrap">{formatDateTime(entry.occurred_at)}</td>
                                <td>
                                    <span className="badge">{entry.event_type}</span>
                                </td>
                                <td className="cell-nowrap" title={entry.user_id || ""}>
                                    <code>{shortId(entry.user_id)}</code>
                                </td>
                                <td className="cell-nowrap" title={entry.course_id || ""}>
                                    <code>{shortId(entry.course_id)}</code>
                                </td>
                                <td className="cell-code">
                                    <code>{JSON.stringify(entry.payload || {}, null, 1)}</code>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    };

    return (
        <Layout
            title="Log de auditoría"
            subtitle="Eventos del dominio publicados en el bus y registrados por el observador de auditoría."
        >
            <div className="toolbar">
                <label className="sr-only" htmlFor="audit-type">
                    Filtrar por tipo de evento
                </label>
                <select
                    id="audit-type"
                    value={eventType}
                    onChange={(e) => setEventType(e.target.value)}
                >
                    <option value="">Todos los eventos</option>
                    {EVENT_TYPES.map((type) => (
                        <option key={type} value={type}>
                            {type}
                        </option>
                    ))}
                </select>

                <label className="sr-only" htmlFor="audit-limit">
                    Cantidad de eventos
                </label>
                <select
                    id="audit-limit"
                    value={limit}
                    onChange={(e) => setLimit(Number(e.target.value))}
                >
                    {[50, 100, 500].map((value) => (
                        <option key={value} value={value}>
                            Últimos {value}
                        </option>
                    ))}
                </select>

                <button type="button" className="btn btn-secondary" onClick={reload}>
                    <IconRefresh size={18} />
                    Actualizar
                </button>
            </div>

            {renderBody()}
        </Layout>
    );
};

export default AuditLog;
