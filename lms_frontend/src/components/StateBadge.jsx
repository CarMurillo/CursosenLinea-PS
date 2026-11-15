const LABELS = {
    draft: "Borrador",
    published: "Publicada",
    closed: "Cerrada",
    scheduled: "Programada",
    live: "En vivo",
    recorded: "Grabada",
};

// Muestra el estado (patrón State) tal como lo devuelve el backend.
const StateBadge = ({ state }) => (
    <span className={`badge badge-${state}`}>
        {LABELS[state] || state}
    </span>
);

export default StateBadge;
