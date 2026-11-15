import { NavLink } from "react-router-dom";
import { useAuth } from "../context/auth-context";
import {
    IconAward,
    IconBook,
    IconClipboard,
    IconCompass,
    IconFlask,
    IconHome,
    IconLayers,
    IconPlus,
    IconSparkle,
    IconUsers
} from "./icons";

// Enlaces por rol, agrupados en secciones. Las rutas están protegidas por rol
// en App.jsx. `featured` resalta el Laboratorio de patrones.
const SECTIONS = {
    student: [
        {
            title: "Aprender",
            links: [
                { to: "/student", label: "Dashboard", icon: IconHome, end: true },
                { to: "/student/courses", label: "Explorar cursos", icon: IconCompass },
                { to: "/student/my-courses", label: "Mis cursos", icon: IconBook },
            ],
        },
        {
            title: "Mi avance",
            links: [
                { to: "/student/recommendations", label: "Recomendaciones", icon: IconSparkle },
                { to: "/student/certificates", label: "Certificados", icon: IconAward },
            ],
        },
    ],
    instructor: [
        {
            title: "Enseñar",
            links: [
                { to: "/instructor", label: "Dashboard", icon: IconHome, end: true },
                { to: "/instructor/courses", label: "Mis cursos", icon: IconLayers },
                { to: "/instructor/create-course", label: "Crear curso", icon: IconPlus },
            ],
        },
        {
            title: "Explorar",
            links: [
                { to: "/patterns", label: "Laboratorio de patrones", icon: IconFlask, featured: true },
            ],
        },
    ],
    admin: [
        {
            title: "Administración",
            links: [
                { to: "/admin", label: "Dashboard", icon: IconHome, end: true },
                { to: "/admin/users", label: "Usuarios", icon: IconUsers },
                { to: "/admin/courses", label: "Cursos", icon: IconLayers },
                { to: "/admin/audit-log", label: "Auditoría", icon: IconClipboard },
            ],
        },
        {
            title: "Explorar",
            links: [
                { to: "/patterns", label: "Laboratorio de patrones", icon: IconFlask, featured: true },
            ],
        },
    ],
};

const Sidebar = ({ open = false }) => {
    const { user } = useAuth();

    if (!user) {
        return null;
    }

    return (
        <aside
            id="menu-lateral"
            className={`sidebar${open ? " is-open" : ""}`}
        >
            <nav aria-label="Menú principal">
                {(SECTIONS[user.role] || []).map((section) => (
                    <div className="sidebar-section" key={section.title}>
                        <p className="sidebar-heading">{section.title}</p>

                        {section.links.map(({ to, label, icon: Icon, end, featured }) => (
                            <NavLink
                                key={to}
                                to={to}
                                end={end}
                                title={label}
                                className={({ isActive }) =>
                                    [
                                        "sidebar-link",
                                        featured ? "sidebar-link-featured" : "",
                                        isActive ? "active" : "",
                                    ]
                                        .filter(Boolean)
                                        .join(" ")
                                }
                            >
                                <Icon size={20} />
                                <span className="sidebar-label">{label}</span>
                            </NavLink>
                        ))}
                    </div>
                ))}
            </nav>
        </aside>
    );
};

export default Sidebar;
