// Formatos de presentación (solo visual; no alteran los datos de la API).

const priceFormatter = new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
});

// Precio con formato es-CO ("$ 120.000"); 0 se muestra como "Gratis".
export const formatPrice = (value) => {
    const amount = Number(value);

    if (!Number.isFinite(amount) || amount <= 0) {
        return "Gratis";
    }

    return priceFormatter.format(amount);
};

export const formatDateTime = (iso) => {
    if (!iso) {
        return "-";
    }

    const date = new Date(iso);

    if (Number.isNaN(date.getTime())) {
        return iso;
    }

    return date.toLocaleString("es-CO", {
        dateStyle: "medium",
        timeStyle: "short",
    });
};

export const formatDate = (iso) => {
    if (!iso) {
        return "-";
    }

    const date = new Date(iso);

    if (Number.isNaN(date.getTime())) {
        return iso;
    }

    return date.toLocaleDateString("es-CO", { dateStyle: "long" });
};

// Iniciales para el avatar ("Ana María Pérez" -> "AP").
export const initials = (name = "") => {
    const parts = name.trim().split(/\s+/).filter(Boolean);

    if (parts.length === 0) {
        return "?";
    }

    const first = parts[0][0];
    const last = parts.length > 1 ? parts[parts.length - 1][0] : "";

    return `${first}${last}`.toUpperCase();
};

// El backend devuelve el tipo como texto ("Video bajo demanda",
// "Clase en Vivo (Videoconferencia)"). Se normaliza para el estilo.
export const courseKind = (course) => {
    const text = `${course?.type ?? course?.course_type ?? ""}`.toLowerCase();

    return text.includes("vivo") || text === "live" ? "live" : "video";
};

export const COURSE_KIND_LABEL = {
    video: "Video bajo demanda",
    live: "Clase en vivo",
};

export const ROLE_LABEL = {
    student: "Estudiante",
    instructor: "Instructor",
    admin: "Administrador",
};
