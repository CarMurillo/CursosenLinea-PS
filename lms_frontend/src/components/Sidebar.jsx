import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const Sidebar = () => {
    const { user } = useAuth();

    if (!user) {
        return null;
    }

    return (
        <aside className="sidebar">

            <h2>LMS</h2>

            {user.role === "student" && (
                <>
                    <Link to="/student">
                        Dashboard
                    </Link>

                    <Link to="/student/courses">
                        Explorar cursos
                    </Link>

                    <Link to="/student/my-courses">
                        Mis cursos
                    </Link>
                </>
            )}

            {user.role === "instructor" && (
                <>
                    <Link to="/instructor">
                        Dashboard
                    </Link>

                    <Link to="/instructor/courses">
                        Mis cursos
                    </Link>

                    <Link to="/instructor/create-course">
                        Crear curso
                    </Link>
                </>
            )}

            {user.role === "admin" && (
                <>
                    <Link to="/admin">
                        Dashboard
                    </Link>

                    <Link to="/admin/users">
                        Usuarios
                    </Link>

                    <Link to="/admin/courses">
                        Cursos
                    </Link>
                </>
            )}

        </aside>
    );
};

export default Sidebar;