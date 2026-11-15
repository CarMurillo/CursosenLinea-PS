import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/auth-context";
import { getMyNotifications } from "../services/notificationService";
import { initials, ROLE_LABEL } from "../utils/format";
import Brand from "./Brand";
import {
    IconBell,
    IconChevronDown,
    IconClose,
    IconLogout,
    IconMenu
} from "./icons";

const HOME_BY_ROLE = {
    student: "/student",
    instructor: "/instructor",
    admin: "/admin",
};

// Polling suave: se recarga al navegar y cada 30 s mientras la página está abierta.
const POLL_MS = 30000;

const seenKey = (user) => `notifications_seen_${user?.user_id || "anon"}`;

const formatDate = (iso) => {
    try {
        return new Date(iso).toLocaleString();
    } catch {
        return iso;
    }
};

// Campana de notificaciones (Observer: InAppNotificationObserver en el backend).
const NotificationBell = ({ user }) => {
    const location = useLocation();
    const [notifications, setNotifications] = useState([]);
    const [failed, setFailed] = useState(false);
    const [open, setOpen] = useState(false);
    const [lastSeen, setLastSeen] = useState(
        () => localStorage.getItem(seenKey(user)) || ""
    );
    const panelRef = useRef(null);

    useEffect(() => {
        let active = true;

        const load = () => {
            getMyNotifications().then(
                (data) => {
                    if (active) {
                        setNotifications(Array.isArray(data) ? data : []);
                        setFailed(false);
                    }
                },
                () => {
                    if (active) {
                        setFailed(true);
                    }
                }
            );
        };

        load();
        const timer = setInterval(load, POLL_MS);

        return () => {
            active = false;
            clearInterval(timer);
        };
    }, [location.pathname]);

    useEffect(() => {
        if (!open) {
            return undefined;
        }

        const handleClick = (event) => {
            if (panelRef.current && !panelRef.current.contains(event.target)) {
                setOpen(false);
            }
        };

        document.addEventListener("mousedown", handleClick);

        return () => document.removeEventListener("mousedown", handleClick);
    }, [open]);

    // El backend no expone "marcar como leída": se cuenta como no vista toda
    // notificación no leída posterior a la última apertura de la campana.
    const unseen = notifications.filter(
        (item) => !item.read && (!lastSeen || item.created_at > lastSeen)
    );

    const toggle = () => {
        if (!open && notifications.length > 0) {
            const newest = notifications[0].created_at;
            localStorage.setItem(seenKey(user), newest);
            setLastSeen(newest);
        }

        setOpen(!open);
    };

    return (
        <div className="bell" ref={panelRef}>
            <button
                type="button"
                className="icon-button bell-button"
                onClick={toggle}
                aria-expanded={open}
                aria-label={`Notificaciones (${unseen.length} nuevas)`}
            >
                <IconBell size={20} />

                {unseen.length > 0 && (
                    <span className="bell-count" aria-hidden="true">
                        {unseen.length > 99 ? "99+" : unseen.length}
                    </span>
                )}
            </button>

            {open && (
                <div className="dropdown bell-panel">
                    <h4 className="dropdown-title">Notificaciones</h4>

                    {failed && (
                        <p className="bell-empty bell-error">
                            No se pudieron cargar las notificaciones.
                        </p>
                    )}

                    {!failed && notifications.length === 0 && (
                        <p className="bell-empty">
                            No tienes notificaciones.
                        </p>
                    )}

                    {notifications.map((item) => (
                        <div
                            key={item.notification_id}
                            className={`bell-item ${
                                !item.read && unseen.includes(item)
                                    ? "unread"
                                    : ""
                            }`}
                        >
                            <strong>{item.title}</strong>
                            <span>{item.message}</span>
                            <span className="muted">
                                {formatDate(item.created_at)}
                            </span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

// Menú de usuario: avatar con iniciales, nombre, rol y cierre de sesión.
const UserMenu = ({ user, onLogout }) => {
    const [open, setOpen] = useState(false);
    const menuRef = useRef(null);

    useEffect(() => {
        if (!open) {
            return undefined;
        }

        const handleClick = (event) => {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setOpen(false);
            }
        };

        const handleKey = (event) => {
            if (event.key === "Escape") {
                setOpen(false);
            }
        };

        document.addEventListener("mousedown", handleClick);
        document.addEventListener("keydown", handleKey);

        return () => {
            document.removeEventListener("mousedown", handleClick);
            document.removeEventListener("keydown", handleKey);
        };
    }, [open]);

    return (
        <div className="user-menu" ref={menuRef}>
            <button
                type="button"
                className="user-button"
                onClick={() => setOpen(!open)}
                aria-expanded={open}
                aria-haspopup="menu"
            >
                <span className="avatar" aria-hidden="true">
                    {initials(user.full_name)}
                </span>

                <span className="user-meta">
                    <span className="user-name">{user.full_name}</span>
                    <span className={`role-badge role-${user.role}`}>
                        {ROLE_LABEL[user.role] || user.role}
                    </span>
                </span>

                <IconChevronDown size={16} className="user-chevron" />
            </button>

            {open && (
                <div className="dropdown user-dropdown" role="menu">
                    <div className="user-dropdown-head">
                        <strong>{user.full_name}</strong>
                        {user.email && <span className="muted">{user.email}</span>}
                    </div>

                    <button
                        type="button"
                        role="menuitem"
                        className="dropdown-item"
                        onClick={onLogout}
                    >
                        <IconLogout size={18} />
                        Cerrar sesión
                    </button>
                </div>
            )}
        </div>
    );
};

const Navbar = ({ menuOpen = false, onToggleMenu }) => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate("/login");
    };

    return (
        <header className="navbar">
            <div className="navbar-start">
                {user && onToggleMenu && (
                    <button
                        type="button"
                        className="icon-button menu-toggle"
                        onClick={onToggleMenu}
                        aria-expanded={menuOpen}
                        aria-controls="menu-lateral"
                        aria-label={menuOpen ? "Cerrar menú" : "Abrir menú"}
                    >
                        {menuOpen ? <IconClose size={22} /> : <IconMenu size={22} />}
                    </button>
                )}

                <Link
                    className="navbar-logo"
                    to={HOME_BY_ROLE[user?.role] || "/login"}
                    aria-label="CursosenLínea, ir al inicio"
                >
                    <Brand size={32} />
                </Link>
            </div>

            <div className="navbar-user">
                {user && (
                    <>
                        <NotificationBell
                            key={user.user_id}
                            user={user}
                        />

                        <UserMenu user={user} onLogout={handleLogout} />
                    </>
                )}
            </div>
        </header>
    );
};

export default Navbar;
