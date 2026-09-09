import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { login } from "../services/authService";

const Login = () => {

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");

    const { loginUser } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();

        setError("");

        try {

            const data = await login(email, password);

            loginUser(data);

            const role = data.user.role;

            if (role === "student") {
                navigate("/student");
            } 
            else if (role === "instructor") {
                navigate("/instructor");
            } 
            else if (role === "admin") {
                navigate("/admin");
            }

        } catch (error) {

            console.error(error);

            setError(
                error.response?.data?.detail ||
                "Correo o contraseña incorrectos"
            );
        }
    };

    return (
        <div className="login-container">

            <form
                className="login-form"
                onSubmit={handleSubmit}
            >

                <h1>LMS</h1>

                <h2>Iniciar sesión</h2>

                {error && (
                    <p className="error">
                        {error}
                    </p>
                )}

                <input
                    type="email"
                    placeholder="Correo electrónico"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                />

                <input
                    type="password"
                    placeholder="Contraseña"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                />

                <button type="submit">
                    Iniciar sesión
                </button>

                <p>
                    ¿No tienes cuenta?
                </p>

                <button
                    type="button"
                    onClick={() => navigate("/register")}
                >
                    Registrarse
                </button>

            </form>

        </div>
    );
};

export default Login;