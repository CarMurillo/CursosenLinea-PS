const LABELS = {
    draft: "Borrador",
    published: "Publicada",
    closed: "Cerrada",
    scheduled: "Programada",
    live: "En vivo",
    ended: "Finalizada",
    finished: "Finalizada",
    recorded: "Grabada",
};

// Muestra el estado (patrón State) tal como lo devuelve el backend.
// El texto siempre acompaña al color; "En vivo" lleva un punto animado.
const StateBadge = ({ state }) => (
    <span className={`badge badge-state badge-${state}`}>
        {state === "live" && <span className="live-dot" aria-hidden="true" />}
        {LABELS[state] || state}
    </span>
);

export default StateBadge;
