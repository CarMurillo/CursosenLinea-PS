import { useCallback, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import Layout from "../../components/Layout";
import { Empty, ErrorState, Loading, Notice } from "../../components/Status";
import { IconPlus, IconSearch, IconUsers } from "../../components/icons";
import { useResource } from "../../hooks/useResource";
import { createUser, getUsers, setUserStatus } from "../../services/userService";
import { getErrorMessage } from "../../services/errors";
import { formatDate, initials } from "../../utils/format";

const TABS = [
    { key: "students", role: "student", label: "Estudiantes", singular: "estudiante" },
    { key: "instructors", role: "instructor", label: "Instructores", singular: "instructor" },
];

const EMPTY_FORM = { firstName: "", lastName: "", email: "", password: "" };

const loadUsers = async () => {
    const [students, instructors] = await Promise.all([
        getUsers("student"),
        getUsers("instructor"),
    ]);
    return { students, instructors };
};

// Formulario de registro hecho por el admin (estudiante o instructor).
const RegisterForm = ({ tab, onCreated, onCancel }) => {
    const [form, setForm] = useState(EMPTY_FORM);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");

    const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

    const submit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError("");
        try {
            const user = await createUser({ ...form, role: tab.role });
            setForm(EMPTY_FORM);
            onCreated(user);
        } catch (err) {
            setError(getErrorMessage(err, "No se pudo registrar el usuario."));
        } finally {
            setSaving(false);
        }
    };

    return (
        <form className="panel admin-register" onSubmit={submit}>
            <h2 className="form-section-title">Registrar {tab.singular}</h2>

            {error && <Notice notice={{ type: "error", text: error }} />}

            <div className="field-row">
                <div className="field">
                    <label className="field-label" htmlFor="new-first">Nombre</label>
                    <input id="new-first" required value={form.firstName}
                        onChange={update("firstName")} />
                </div>
                <div className="field">
                    <label className="field-label" htmlFor="new-last">Apellido</label>
                    <input id="new-last" required value={form.lastName}
                        onChange={update("lastName")} />
                </div>
            </div>

            <div className="field-row">
                <div className="field">
                    <label className="field-label" htmlFor="new-email">Correo</label>
                    <input id="new-email" type="email" required value={form.email}
                        onChange={update("email")} />
                </div>
                <div className="field">
                    <label className="field-label" htmlFor="new-password">
                        Contraseña inicial
                    </label>
                    <input id="new-password" type="password" required minLength={8}
                        value={form.password} onChange={update("password")}
                        aria-describedby="new-password-hint" />
                    <span className="field-hint" id="new-password-hint">
                        Mínimo 8 caracteres. Compártela con el usuario.
                    </span>
                </div>
            </div>

            <div className="form-actions">
                <button type="button" className="btn btn-secondary btn-sm" onClick={onCancel}>
                    Cancelar
                </button>
                <button type="submit"
                    className={`btn btn-primary btn-sm${saving ? " is-loading" : ""}`}
                    disabled={saving} aria-busy={saving}>
                    Registrar
                </button>
            </div>
        </form>
    );
};

const Users = () => {
    const { data, error, loading, reload } = useResource(loadUsers);
    const [params, setParams] = useSearchParams();
    const tab = TABS.find((t) => t.key === params.get("tab")) || TABS[0];

    const [query, setQuery] = useState("");
    const [statusFilter, setStatusFilter] = useState("all");
    const [showForm, setShowForm] = useState(false);
    const [busyId, setBusyId] = useState("");
    const [notice, setNotice] = useState(null);

    const selectTab = (key) => {
        setParams({ tab: key });
        setShowForm(false);
        setQuery("");
    };

    const users = useMemo(() => {
        const list = data?.[tab.key] || [];
        const q = query.trim().toLowerCase();
        return list.filter((u) =>
            (!q || u.full_name.toLowerCase().includes(q) || u.email.includes(q)) &&
            (statusFilter === "all" || (statusFilter === "active") === u.is_active)
        );
    }, [data, tab, query, statusFilter]);

    const toggleStatus = useCallback(async (user) => {
        const action = user.is_active ? "suspender" : "reactivar";
        if (!window.confirm(`¿Seguro que quieres ${action} a ${user.full_name}?`)) {
            return;
        }
        setBusyId(user.user_id);
        setNotice(null);
        try {
            await setUserStatus(user.user_id, !user.is_active);
            setNotice({
                type: "success",
                text: user.is_active
                    ? `${user.full_name} fue suspendido: ya no puede iniciar sesión.`
                    : `${user.full_name} fue reactivado.`,
            });
            await reload();
        } catch (err) {
            setNotice({ type: "error", text: getErrorMessage(err, "No se pudo cambiar el estado.") });
        } finally {
            setBusyId("");
        }
    }, [reload]);

    const onCreated = async (user) => {
        setShowForm(false);
        setNotice({ type: "success", text: `${user.full_name} (${user.email}) fue registrado.` });
        await reload();
    };

    const renderTable = () => {
        if (users.length === 0) {
            return (
                <Empty icon={IconUsers}>
                    {query || statusFilter !== "all"
                        ? "Ningún usuario coincide con el filtro."
                        : `No hay ${tab.label.toLowerCase()} registrados.`}
                </Empty>
            );
        }

        return (
            <>
                <p className="result-count">
                    {users.length === 1 ? `1 ${tab.singular}` : `${users.length} ${tab.label.toLowerCase()}`}
                </p>

                <div className="table-wrap table-wrap-scroll">
                    <table className="users-table">
                        <caption className="sr-only">{tab.label} registrados</caption>
                        <thead>
                            <tr>
                                <th scope="col">Nombre</th>
                                <th scope="col">Email</th>
                                <th scope="col">Estado</th>
                                <th scope="col">Registro</th>
                                <th scope="col">Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map((user) => (
                                <tr key={user.user_id}>
                                    <td>
                                        <span className="cell-user">
                                            <span className="avatar" aria-hidden="true">
                                                {initials(user.full_name)}
                                            </span>
                                            <strong>{user.full_name}</strong>
                                        </span>
                                    </td>
                                    <td>{user.email}</td>
                                    <td>
                                        <span className={`badge ${user.is_active ? "badge-success" : "badge-error"}`}>
                                            {user.is_active ? "Activo" : "Suspendido"}
                                        </span>
                                    </td>
                                    <td>{formatDate(user.created_at)}</td>
                                    <td>
                                        <span className="row-actions">
                                            <Link className="btn btn-secondary btn-sm"
                                                to={`/admin/users/${user.user_id}`}>
                                                Ver detalle
                                            </Link>
                                            <button type="button"
                                                className={`btn btn-sm ${user.is_active ? "btn-danger" : "btn-primary"}${busyId === user.user_id ? " is-loading" : ""}`}
                                                disabled={busyId !== ""}
                                                aria-busy={busyId === user.user_id}
                                                onClick={() => toggleStatus(user)}>
                                                {user.is_active ? "Suspender" : "Reactivar"}
                                            </button>
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </>
        );
    };

    const renderBody = () => {
        if (loading && !data) {
            return <Loading text="Cargando usuarios..." />;
        }
        if (error) {
            return <ErrorState error={error} fallback="No se pudieron cargar los usuarios." onRetry={reload} />;
        }

        return (
            <>
                <div className="tabs" role="tablist" aria-label="Tipo de usuario">
                    {TABS.map((t) => (
                        <button key={t.key} type="button" role="tab"
                            aria-selected={t.key === tab.key}
                            className={`tab${t.key === tab.key ? " active" : ""}`}
                            onClick={() => selectTab(t.key)}>
                            {t.label}
                            <span className="badge">{data?.[t.key]?.length ?? 0}</span>
                        </button>
                    ))}
                </div>

                {notice && <Notice notice={notice} />}

                <div className="toolbar">
                    <label className="search">
                        <span className="sr-only">Buscar</span>
                        <IconSearch size={18} />
                        <input type="search" placeholder="Buscar por nombre o correo"
                            value={query} onChange={(e) => setQuery(e.target.value)} />
                    </label>
                    <select aria-label="Filtrar por estado" value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}>
                        <option value="all">Todos</option>
                        <option value="active">Activos</option>
                        <option value="suspended">Suspendidos</option>
                    </select>
                    <button type="button" className="btn btn-primary btn-sm"
                        onClick={() => setShowForm((v) => !v)}>
                        <IconPlus size={16} />
                        Registrar {tab.singular}
                    </button>
                </div>

                {showForm && (
                    <RegisterForm tab={tab} onCreated={onCreated} onCancel={() => setShowForm(false)} />
                )}

                {renderTable()}
            </>
        );
    };

    return (
        <Layout title="Usuarios"
            subtitle="Estudiantes e instructores: detalle, registro y suspensión.">
            {renderBody()}
        </Layout>
    );
};

export default Users;
