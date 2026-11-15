import { NavLink } from "react-router-dom";
import { IconBroadcast, IconLayers, IconQuiz } from "./icons";

// Pestañas de las vistas de gestión de un curso (instructor).
const CourseTabs = ({ courseId }) => {
    const base = `/instructor/course/${courseId}`;

    const tabs = [
        { to: `${base}/content`, label: "Contenido", icon: IconLayers },
        { to: `${base}/assessments`, label: "Evaluaciones", icon: IconQuiz },
        { to: `${base}/live`, label: "Clases en vivo", icon: IconBroadcast },
    ];

    return (
        <nav className="tabs" aria-label="Secciones del curso">
            {tabs.map(({ to, label, icon: Icon }) => (
                <NavLink
                    key={to}
                    to={to}
                    className={({ isActive }) => `tab${isActive ? " active" : ""}`}
                >
                    <Icon size={18} />
                    {label}
                </NavLink>
            ))}
        </nav>
    );
};

export default CourseTabs;
