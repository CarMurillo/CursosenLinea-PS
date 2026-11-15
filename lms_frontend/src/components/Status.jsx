import { getErrorMessage } from "../services/errors";

// Estados reutilizables de carga, vacío, error y mensajes de acción.

export const Loading = ({ text = "Cargando..." }) => (
    <p className="status status-loading">{text}</p>
);

export const Empty = ({ children }) => (
    <div className="status status-empty">{children}</div>
);

export const ErrorState = ({ error, fallback, onRetry }) => (
    <div className="status status-error">
        <p>{getErrorMessage(error, fallback)}</p>

        {onRetry && (
            <button
                type="button"
                className="btn-secondary"
                onClick={onRetry}
            >
                Reintentar
            </button>
        )}
    </div>
);

// Mensaje de resultado de una acción: { type: "success" | "error", text }.
export const Notice = ({ notice }) => {
    if (!notice?.text) {
        return null;
    }

    return (
        <p className={`alert ${notice.type}`} role="status">
            {notice.text}
        </p>
    );
};
