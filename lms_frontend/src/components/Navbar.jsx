import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/auth-context";
import { getMyNotifications } from "../services/notificationService";

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
                className="bell-button"
                onClick={toggle}
                aria-label={`Notificaciones (${unseen.length} nuevas)`}
            >
                Notificaciones

                {unseen.length > 0 && (
                    <span className="bell-count">
                        {unseen.length > 99 ? "99+" : unseen.length}
                    </span>
                )}
            </button>

            {open && (
                <div className="bell-panel">
                    <h4>Notificaciones</h4>

                    {failed && (
                        <p className="bell-empty error">
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

const Navbar = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate("/login");
    };

    return (
        <header className="navbar">
            <div className="navbar-logo">
                LMS
            </div>

            <div className="navbar-user">
                {user && (
                    <>
                        <NotificationBell
                            key={user.user_id}
                            user={user}
                        />

                        <span>
                            {user.full_name}
                        </span>

                        <span className="role">
                            {user.role}
                        </span>

                        <button onClick={handleLogout}>
                            Cerrar sesión
                        </button>
                    </>
                )}
            </div>
        </header>
    );
};

export default Navbar;
