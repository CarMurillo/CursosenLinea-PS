import { useCallback, useState } from "react";
import { Link, useParams } from "react-router-dom";

import Layout from "../../components/Layout";
import { StatCard } from "../../components/StatCard";
import { Empty, ErrorState, Loading, Notice } from "../../components/Status";
import {
    IconArrowLeft,
    IconAward,
    IconBook,
    IconCheckCircle,
    IconLayers,
    IconPlay,
    IconUsers,
} from "../../components/icons";
import { useResource } from "../../hooks/useResource";
import { getUserDetail, setUserStatus } from "../../services/userService";
import { getErrorMessage } from "../../services/errors";
import { formatDate, formatDateTime, formatPrice, initials, ROLE_LABEL } from "../../utils/format";

const STATUS = {
    sin_iniciar: { label: "Sin iniciar", badge: "badge-draft" },
    iniciado: { label: "Iniciado", badge: "badge-category-structural" },
    terminado: { label: "Terminado", badge: "badge-success" },
};

const MiniProgress = ({ value }) => (
    <div className={`progress-block${value >= 100 ? " is-complete" : ""}`}>
        <div className="progress-head">
            <span className="progress-value">{value}%</span>
        </div>
        <div className="progress" role="progressbar" aria-valuenow={value}
            aria-valuemin={0} aria-valuemax={100}>
            <div className="progress-bar" style={{ width: `${Math.min(100, value)}%` }} />
        </div>
    </div>
);

const StudentSection = ({ data }) => (
    <>
        <div className="stat-grid">
            <StatCard icon={IconBook} label="Cursos inscritos" value={data.enrolled_count} />
            <StatCard icon={IconPlay} label="Iniciados" value={data.in_progress_count} tone="accent" />
            <StatCard icon={IconCheckCircle} label="Terminados" value={data.completed_count} tone="success" />
            <StatCard icon={IconAward} label="Certificados" value={data.certificate_count} tone="violet" />
        </div>

        <section className="panel">
            <h2 className="form-section-title">Cursos inscritos</h2>
            {data.courses.length === 0 ? (
                <Empty icon={IconBook}>No está inscrito en ningún curso.</Empty>
            ) : (
                <div className="table-wrap table-wrap-scroll">
                    <table className="users-table">
                        <thead>
                            <tr>
                                <th scope="col">Curso</th>
                                <th scope="col">Instructor</th>
                                <th scope="col">Estado</th>
                                <th scope="col">Avance</th>
                                <th scope="col">Certificado</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.courses.map((c) => (
                                <tr key={c.course_id}>
                                    <td><strong>{c.title}</strong></td>
                                    <td>{c.instructor || "-"}</td>
                                    <td>
                                        <span className={`badge ${STATUS[c.status]?.badge || ""}`}>
                                            {STATUS[c.status]?.label || c.status}
                                        </span>
                                    </td>
                                    <td><MiniProgress value={c.progress} /></td>
                                    <td>{c.has_certificate ? "Sí" : "No"}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </section>

        <section className="panel">
            <h2 className="form-section-title">Certificaciones</h2>
            {data.certificates.length === 0 ? (
                <Empty icon={IconAward}>Aún no tiene certificaciones.</Empty>
            ) : (
                <ul className="lab-log">
                    {data.certificates.map((c) => (
                        <li className="ok" key={c.certificate_id}>
                            <strong>{c.course_title || c.course_id}</strong>
                            <span className="badge badge-success">Puntaje {c.score ?? "-"}</span>
                            <span className="muted">
                                Código <code>{c.verification_code}</code> · emitido {formatDate(c.issued_at)}
                            </span>
                        </li>
                    ))}
                </ul>
            )}
        </section>

        <section className="panel">
            <h2 className="form-section-title">Pagos</h2>
            {data.payments.length === 0 ? (
                <p className="muted">Sin pagos registrados.</p>
            ) : (
                <div className="table-wrap">
                    <table className="users-table">
                        <thead>
                            <tr>
                                <th scope="col">Fecha</th>
                                <th scope="col">Pasarela</th>
                                <th scope="col">Monto</th>
                                <th scope="col">Estado</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.payments.map((p) => (
                                <tr key={p.payment_id}>
                                    <td>{formatDateTime(p.created_at)}</td>
                                    <td><code>{p.gateway}</code></td>
                                    <td>{p.amount} {p.currency}</td>
                                    <td>
                                        <span className={`badge ${p.status === "approved" ? "badge-success" : "badge-error"}`}>
                                            {p.status === "approved" ? "Aprobado" : "Rechazado"}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </section>
    </>
);

const InstructorSection = ({ data }) => (
    <>
        <div className="stat-grid">
            <StatCard icon={IconLayers} label="Cursos que dicta" value={data.course_count} />
            <StatCard icon={IconUsers} label="Estudiantes inscritos" value={data.student_count} tone="accent" />
        </div>

        <section className="panel">
            <h2 className="form-section-title">Cursos</h2>
            {data.courses.length === 0 ? (
                <Empty icon={IconLayers}>Aún no ha creado cursos.</Empty>
            ) : (
                <div className="table-wrap table-wrap-scroll">
                    <table className="users-table">
                        <thead>
                            <tr>
                                <th scope="col">Curso</th>
                                <th scope="col">Tipo</th>
                                <th scope="col">Precio</th>
                                <th scope="col">Beneficios</th>
                                <th scope="col">Estudiantes</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.courses.map((c) => (
                                <tr key={c.course_id}>
                                    <td><strong>{c.title}</strong></td>
                                    <td>{c.type === "live" ? "En vivo" : "Video"}</td>
                                    <td>{formatPrice(c.price)}</td>
                                    <td>
                                        {[c.premium && "Premium", c.certificate && "Certificado"]
                                            .filter(Boolean).join(" · ") || "-"}
                                    </td>
                                    <td>{c.student_count}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </section>
    </>
);

const UserDetail = () => {
    const { userId } = useParams();
    const load = useCallback(() => getUserDetail(userId), [userId]);
    const { data: user, error, loading, reload } = useResource(load);
    const [busy, setBusy] = useState(false);
    const [notice, setNotice] = useState(null);

    const toggleStatus = async () => {
        const action = user.is_active ? "suspender" : "reactivar";
        if (!window.confirm(`¿Seguro que quieres ${action} a ${user.full_name}?`)) {
            return;
        }
        setBusy(true);
        setNotice(null);
        try {
            await setUserStatus(user.user_id, !user.is_active);
            setNotice({
                type: "success",
                text: user.is_active ? "Usuario suspendido." : "Usuario reactivado.",
            });
            await reload();
        } catch (err) {
            setNotice({ type: "error", text: getErrorMessage(err, "No se pudo cambiar el estado.") });
        } finally {
            setBusy(false);
        }
    };

    const back = (
        <Link className="btn btn-secondary btn-sm"
            to={`/admin/users?tab=${user?.role === "instructor" ? "instructors" : "students"}`}>
            <IconArrowLeft size={16} />
            Volver a usuarios
        </Link>
    );

    if (loading && !user) {
        return <Layout title="Detalle de usuario"><Loading /></Layout>;
    }
    if (error) {
        return (
            <Layout title="Detalle de usuario">
                {back}
                <ErrorState error={error} fallback="No se pudo cargar el usuario." onRetry={reload} />
            </Layout>
        );
    }

    const manageable = user.role === "student" || user.role === "instructor";

    return (
        <Layout title={user.full_name} subtitle={user.email}>
            <div className="admin-back">
                {back}
            </div>

            <section className="panel user-header">
                <span className="cell-user">
                    <span className="avatar" aria-hidden="true">{initials(user.full_name)}</span>
                    <span>
                        <strong>{user.full_name}</strong>
                        <span className="muted"> · registrado {formatDate(user.created_at)}</span>
                    </span>
                </span>
                <span className="row-actions">
                    <span className={`badge role-${user.role}`}>{ROLE_LABEL[user.role] || user.role}</span>
                    <span className={`badge ${user.is_active ? "badge-success" : "badge-error"}`}>
                        {user.is_active ? "Activo" : "Suspendido"}
                    </span>
                    {manageable && (
                        <button type="button"
                            className={`btn btn-sm ${user.is_active ? "btn-danger" : "btn-primary"}${busy ? " is-loading" : ""}`}
                            disabled={busy} aria-busy={busy} onClick={toggleStatus}>
                            {user.is_active ? "Suspender" : "Reactivar"}
                        </button>
                    )}
                </span>
            </section>

            {notice && <Notice notice={notice} />}

            {user.student && <StudentSection data={user.student} />}
            {user.instructor && <InstructorSection data={user.instructor} />}
        </Layout>
    );
};

export default UserDetail;
