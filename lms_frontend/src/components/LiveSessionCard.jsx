import StateBadge from "./StateBadge";
import { formatDateTime } from "../utils/format";
import { IconBroadcast, IconClock, IconExternal, IconPlay } from "./icons";

// Tarjeta de una clase en vivo (State: scheduled -> live -> recorded).
// `children` permite añadir acciones (iniciar / terminar) para el instructor.
const LiveSessionCard = ({ session, children }) => (
    <article className={`card session-card session-${session.state}`}>
        <div className="card-head">
            <StateBadge state={session.state} />
            {session.provider && (
                <span className="muted">{session.provider}</span>
            )}
        </div>

        <h3 className="card-title">{session.title}</h3>

        <ul className="meta-list">
            <li>
                <IconClock size={16} />
                {formatDateTime(session.scheduled_at)} · {session.duration_minutes} min
            </li>

            {session.started_at && (
                <li>
                    <IconBroadcast size={16} />
                    Inició: {formatDateTime(session.started_at)}
                </li>
            )}

            {session.ended_at && (
                <li>
                    <IconClock size={16} />
                    Terminó: {formatDateTime(session.ended_at)}
                </li>
            )}
        </ul>

        {(session.room_url || session.recording_url) && (
            <div className="card-links">
                {session.state !== "recorded" && session.room_url && (
                    <a
                        className={`btn btn-sm ${session.state === "live" ? "btn-primary" : "btn-secondary"}`}
                        href={session.room_url}
                        target="_blank"
                        rel="noreferrer"
                    >
                        <IconExternal size={16} />
                        {session.state === "live" ? "Entrar a la sala" : "Enlace de la sala"}
                    </a>
                )}

                {session.recording_url && (
                    <a
                        className="btn btn-secondary btn-sm"
                        href={session.recording_url}
                        target="_blank"
                        rel="noreferrer"
                    >
                        <IconPlay size={16} />
                        Ver grabación
                    </a>
                )}
            </div>
        )}

        {children}
    </article>
);

export default LiveSessionCard;
