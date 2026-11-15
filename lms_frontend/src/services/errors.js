// Traduce un error de axios a un mensaje legible usando `detail` del backend.
// FastAPI devuelve `detail` como texto (400/403/404/409) o como lista (422).
export const getErrorMessage = (error, fallback = "Ocurrió un error.") => {
    const detail = error?.response?.data?.detail;

    if (typeof detail === "string" && detail) {
        return detail;
    }

    if (Array.isArray(detail) && detail.length > 0) {
        return detail
            .map((item) => {
                const field = Array.isArray(item.loc)
                    ? item.loc.filter((part) => part !== "body").join(".")
                    : "";
                return field ? `${field}: ${item.msg}` : item.msg;
            })
            .join(" | ");
    }

    if (!error?.response) {
        return "No hay conexión con el servidor.";
    }

    return fallback;
};

export const getErrorStatus = (error) => error?.response?.status ?? null;
