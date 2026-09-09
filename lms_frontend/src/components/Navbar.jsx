import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

const Navbar = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate("/login");
    };

    return (
        <header className="navbar">
            <div className="navbar-logo">
                LMS
            </div>

            <div className="navbar-user">
                {user && (
                    <>
                        <span>
                            {user.full_name}
                        </span>

                        <span className="role">
                            {user.role}
                        </span>

                        <button onClick={handleLogout}>
                            Cerrar sesión
                        </button>
                    </>
                )}
            </div>
        </header>
    );
};

export default Navbar;
