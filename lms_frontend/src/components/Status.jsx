import { getErrorMessage } from "../services/errors";
import {
    IconAlert,
    IconCheckCircle,
    IconInbox,
    IconInfo,
    IconRefresh
} from "./icons";

// Estados reutilizables de carga, vacío, error y mensajes de acción.

// `variant="cards"` muestra un esqueleto de tarjetas en lugar del spinner.
export const Loading = ({ text = "Cargando...", variant = "spinner", count = 3 }) => {
    if (variant === "cards") {
        return (
            <div className="course-grid" role="status" aria-live="polite">
                <span className="sr-only">{text}</span>
                {Array.from({ length: count }, (_, index) => (
                    <div className="skeleton-card" key={index} aria-hidden="true">
                        <div className="skeleton skeleton-header" />
                        <div className="skeleton-body">
                            <div className="skeleton skeleton-line" />
                            <div className="skeleton skeleton-line short" />
                            <div className="skeleton skeleton-line shorter" />
                        </div>
                    </div>
                ))}
            </div>
        );
    }

    return (
        <div className="status status-loading" role="status" aria-live="polite">
            <span className="spinner" aria-hidden="true" />
            <span>{text}</span>
        </div>
    );
};

export const Empty = ({ children, title, icon: Icon = IconInbox, action }) => (
    <div className="status status-empty">
        <span className="status-icon" aria-hidden="true">
            <Icon size={28} />
        </span>
        {title && <h3 className="status-title">{title}</h3>}
        <div className="status-text">{children}</div>
        {action && <div className="status-action">{action}</div>}
    </div>
);

export const ErrorState = ({ error, fallback, onRetry }) => (
    <div className="alert alert-error" role="alert">
        <IconAlert className="alert-icon" />
        <div className="alert-body">
            <p>{getErrorMessage(error, fallback)}</p>

            {onRetry && (
                <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={onRetry}
                >
                    <IconRefresh size={16} />
                    Reintentar
                </button>
            )}
        </div>
    </div>
);

const NOTICE_ICONS = {
    success: IconCheckCircle,
    error: IconAlert,
    warning: IconAlert,
    info: IconInfo,
};

// Mensaje de resultado de una acción: { type: "success" | "error" | "warning" | "info", text }.
export const Notice = ({ notice }) => {
    if (!notice?.text) {
        return null;
    }

    const type = NOTICE_ICONS[notice.type] ? notice.type : "info";
    const Icon = NOTICE_ICONS[type];

    return (
        <div
            className={`alert alert-${type}`}
            role={type === "error" ? "alert" : "status"}
        >
            <Icon className="alert-icon" />
            <p className="alert-body">{notice.text}</p>
        </div>
    );
};
