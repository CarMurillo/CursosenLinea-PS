import { NavLink } from "react-router-dom";
import { useAuth } from "../context/auth-context";

// Enlaces por rol. Las rutas están protegidas por rol en App.jsx.
const LINKS = {
    student: [
        { to: "/student", label: "Dashboard", end: true },
        { to: "/student/courses", label: "Explorar cursos" },
        { to: "/student/my-courses", label: "Mis cursos" },
        { to: "/student/recommendations", label: "Recomendaciones" },
        { to: "/student/certificates", label: "Certificados" },
    ],
    instructor: [
        { to: "/instructor", label: "Dashboard", end: true },
        { to: "/instructor/courses", label: "Mis cursos" },
        { to: "/instructor/create-course", label: "Crear curso" },
        { to: "/patterns", label: "Laboratorio de patrones" },
    ],
    admin: [
        { to: "/admin", label: "Dashboard", end: true },
        { to: "/admin/users", label: "Usuarios" },
        { to: "/admin/courses", label: "Cursos" },
        { to: "/admin/audit-log", label: "Auditoría" },
        { to: "/patterns", label: "Laboratorio de patrones" },
    ],
};

const Sidebar = () => {
    const { user } = useAuth();

    if (!user) {
        return null;
    }

    return (
        <aside className="sidebar">

            <h2>LMS</h2>

            {(LINKS[user.role] || []).map((link) => (
                <NavLink
                    key={link.to}
                    to={link.to}
                    end={link.end}
                >
                    {link.label}
                </NavLink>
            ))}

        </aside>
    );
};

export default Sidebar;
