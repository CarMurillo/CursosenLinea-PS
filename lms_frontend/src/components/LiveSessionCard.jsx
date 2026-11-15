import StateBadge from "./StateBadge";

const formatDate = (iso) => (iso ? new Date(iso).toLocaleString() : "-");

// Tarjeta de una clase en vivo (State: scheduled -> live -> recorded).
// `children` permite añadir acciones (iniciar / terminar) para el instructor.
const LiveSessionCard = ({ session, children }) => (
    <div className="course-card">
        <h3>{session.title}</h3>

        <div>
            <StateBadge state={session.state} />
            <span className="muted">{session.provider}</span>
        </div>

        <p className="muted">
            Programada: {formatDate(session.scheduled_at)} -{" "}
            {session.duration_minutes} min
        </p>

        {session.started_at && (
            <p className="muted">Inició: {formatDate(session.started_at)}</p>
        )}

        {session.ended_at && (
            <p className="muted">Terminó: {formatDate(session.ended_at)}</p>
        )}

        {session.state !== "recorded" && session.room_url && (
            <a href={session.room_url} target="_blank" rel="noreferrer">
                {session.state === "live" ? "Entrar a la sala" : "Enlace de la sala"}
            </a>
        )}

        {session.recording_url && (
            <a href={session.recording_url} target="_blank" rel="noreferrer">
                Ver grabación
            </a>
        )}

        {children}
    </div>
);

export default LiveSessionCard;
