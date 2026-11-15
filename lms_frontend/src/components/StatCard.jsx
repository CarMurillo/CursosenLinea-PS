import { Link } from "react-router-dom";
import { IconArrowRight } from "./icons";

// Indicador numérico del dashboard. `tone`: primary | accent | violet | success.
export const StatCard = ({ icon: Icon, label, value, tone = "primary" }) => (
    <div className="stat-card">
        <span className={`stat-icon stat-icon-${tone}`} aria-hidden="true">
            <Icon size={22} />
        </span>

        <div className="stat-body">
            <span className="stat-value">{value ?? "—"}</span>
            <span className="stat-label">{label}</span>
        </div>
    </div>
);

// Acceso rápido: tarjeta-enlace con icono, título y descripción.
export const QuickLink = ({ to, icon: Icon, title, text, tone = "primary" }) => (
    <Link className="quick-link" to={to}>
        <span className={`stat-icon stat-icon-${tone}`} aria-hidden="true">
            <Icon size={22} />
        </span>

        <span className="quick-link-title">
            {title}
            <IconArrowRight size={18} />
        </span>

        <span className="quick-link-text">{text}</span>
    </Link>
);
