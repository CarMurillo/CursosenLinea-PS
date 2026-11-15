import { useState } from "react";
import { AuthContext } from "./auth-context";

// Lee la sesión guardada al montar (inicialización perezosa, sin efecto).
const readStoredSession = () => {
    const storedToken = localStorage.getItem("token");
    const storedUser = localStorage.getItem("user");

    if (!storedToken || !storedUser) {
        return { token: null, user: null };
    }

    try {
        return { token: storedToken, user: JSON.parse(storedUser) };
    } catch {
        return { token: null, user: null };
    }
};

export const AuthProvider = ({ children }) => {
    const [session, setSession] = useState(readStoredSession);

    const loginUser = (data) => {
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("user", JSON.stringify(data.user));

        setSession({ token: data.access_token, user: data.user });
    };

    const logout = () => {
        localStorage.removeItem("token");
        localStorage.removeItem("user");

        setSession({ token: null, user: null });
    };

    return (
        <AuthContext.Provider
            value={{
                user: session.user,
                token: session.token,
                loginUser,
                logout,
                isAuthenticated: !!session.token,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};
