import { Link } from "react-router-dom";

import Brand from "../components/Brand";
import { IconArrowLeft } from "../components/icons";
import { useAuth } from "../context/auth-context";

const HOME_BY_ROLE = {
    student: "/student",
    instructor: "/instructor",
    admin: "/admin",
};

// Ilustración simple: un candado o una brújula sobre un círculo suave.
const Illustration = ({ kind }) => (
    <svg
        className="illustration"
        width="200"
        height="160"
        viewBox="0 0 200 160"
        aria-hidden="true"
        focusable="false"
    >
        <ellipse className="illu-shadow" cx="100" cy="146" rx="62" ry="8" />
        <circle className="illu-bg" cx="100" cy="74" r="64" />

        {kind === "lock" ? (
            <g className="illu-stroke">
                <rect x="68" y="66" width="64" height="50" rx="10" />
                <path d="M80 66V52a20 20 0 0 1 40 0v14" />
                <circle cx="100" cy="88" r="6" />
                <path d="M100 94v10" />
            </g>
        ) : (
            <g className="illu-stroke">
                <circle cx="100" cy="74" r="36" />
                <path d="m116 58-10 22-22 10 10-22z" />
                <path d="M100 30v8M100 110v8M56 74h8M136 74h8" />
            </g>
        )}

        <circle className="illu-accent" cx="150" cy="30" r="8" />
        <circle className="illu-accent-soft" cx="44" cy="40" r="5" />
    </svg>
);

const ErrorPage = ({ kind, code, title, text }) => {
    const { user } = useAuth();
    const home = HOME_BY_ROLE[user?.role] || "/login";

    return (
        <div className="error-page">
            <Link className="error-brand" to={home} aria-label="CursosenLínea, ir al inicio">
                <Brand size={32} />
            </Link>

            <div className="error-card">
                <Illustration kind={kind} />
                <p className="error-code">{code}</p>
                <h1>{title}</h1>
                <p className="page-subtitle">{text}</p>

                <Link className="btn btn-primary" to={home}>
                    <IconArrowLeft size={18} />
                    {user ? "Volver al inicio" : "Ir a iniciar sesión"}
                </Link>
            </div>
        </div>
    );
};

export const Unauthorized = () => (
    <ErrorPage
        kind="lock"
        code="403"
        title="Acceso no autorizado"
        text="No tienes permisos para acceder a esta página."
    />
);

export const NotFound = () => (
    <ErrorPage
        kind="compass"
        code="404"
        title="Página no encontrada"
        text="La dirección que buscas no existe o fue movida."
    />
);
