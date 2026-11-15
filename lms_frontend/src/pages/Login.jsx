import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/auth-context";
import { login } from "../services/authService";
import AuthLayout from "../components/AuthLayout";
import { Notice } from "../components/Status";

const Login = () => {

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [sending, setSending] = useState(false);
    const [searchParams] = useSearchParams();
    const expired = searchParams.get("expired") === "1";

    const { loginUser } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();

        setError("");
        setSending(true);

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

            setError(
                error.response?.data?.detail ||
                "Correo o contraseña incorrectos"
            );
        } finally {
            setSending(false);
        }
    };

    return (
        <AuthLayout
            title="Iniciar sesión"
            subtitle="Bienvenido de nuevo. Ingresa con tu correo y contraseña."
        >
            <form
                className="auth-form"
                onSubmit={handleSubmit}
            >

                {expired && !error && (
                    <Notice
                        notice={{
                            type: "warning",
                            text: "Tu sesión expiró o no es válida. Inicia sesión de nuevo.",
                        }}
                    />
                )}

                {error && (
                    <Notice notice={{ type: "error", text: error }} />
                )}

                <div className="field">
                    <label className="field-label" htmlFor="login-email">
                        Correo electrónico
                    </label>
                    <input
                        id="login-email"
                        type="email"
                        autoComplete="email"
                        placeholder="nombre@correo.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                    />
                </div>

                <div className="field">
                    <label className="field-label" htmlFor="login-password">
                        Contraseña
                    </label>
                    <input
                        id="login-password"
                        type="password"
                        autoComplete="current-password"
                        placeholder="Tu contraseña"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>

                <button
                    type="submit"
                    className={`btn btn-primary btn-block${sending ? " is-loading" : ""}`}
                    disabled={sending}
                    aria-busy={sending}
                >
                    Iniciar sesión
                </button>

                <p className="auth-switch">
                    ¿No tienes cuenta?{" "}
                    <button
                        type="button"
                        className="btn-link"
                        onClick={() => navigate("/register")}
                    >
                        Registrarse
                    </button>
                </p>

            </form>
        </AuthLayout>
    );
};

export default Login;