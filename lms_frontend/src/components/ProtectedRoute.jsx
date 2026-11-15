import { Navigate } from "react-router-dom";
import { useAuth } from "../context/auth-context";

// `role` acepta un rol ("student") o una lista (["instructor", "admin"]).
const ProtectedRoute = ({ children, role }) => {
    const { user, isAuthenticated } = useAuth();

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    const allowed = Array.isArray(role) ? role : role ? [role] : null;

    if (allowed && !allowed.includes(user?.role)) {
        return <Navigate to="/unauthorized" replace />;
    }

    return children;
};

export default ProtectedRoute;
