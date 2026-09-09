
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { register } from "../services/authService";

const Register = () => {
    const navigate = useNavigate();

    const [form, setForm] = useState({
        first_name: "",
        last_name: "",
        email: "",
        password: "",
        role: "student",
        bio: "",
        specialization: ""
    });

    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    const handleChange = (e) => {
        setForm({
            ...form,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        setError("");
        setSuccess("");

        try {
            await register(form);

            setSuccess("Usuario registrado correctamente.");

            setTimeout(() => {
                navigate("/login");
            }, 1500);

        } catch (error) {
            console.error("Error registrando usuario:", error);

            if (error.response?.status === 409) {
                setError("El correo ya está registrado.");
            } else if (error.response?.status === 422) {
                setError("Los datos enviados no tienen el formato correcto.");
            } else {
                setError(
                    error.response?.data?.detail ||
                    "No se pudo registrar el usuario."
                );
            }
        }
    };

    return (
        <div className="login-container">

            <form
                className="login-form"
                onSubmit={handleSubmit}
            >

                <h1>LMS</h1>

                <h2>Crear cuenta</h2>

                {error && (
                    <p className="error">
                        {error}
                    </p>
                )}

                {success && (
                    <p className="success">
                        {success}
                    </p>
                )}

                <input
                    type="text"
                    name="first_name"
                    placeholder="Nombre"
                    value={form.first_name}
                    onChange={handleChange}
                    required
                />

                <input
                    type="text"
                    name="last_name"
                    placeholder="Apellido"
                    value={form.last_name}
                    onChange={handleChange}
                    required
                />

                <input
                    type="email"
                    name="email"
                    placeholder="Correo electrónico"
                    value={form.email}
                    onChange={handleChange}
                    required
                />

                <input
                    type="password"
                    name="password"
                    placeholder="Contraseña"
                    value={form.password}
                    onChange={handleChange}
                    required
                />

                <select
                    name="role"
                    value={form.role}
                    onChange={handleChange}
                >
                    <option value="student">
                        Estudiante
                    </option>

                    <option value="instructor">
                        Instructor
                    </option>

                    <option value="admin">
                        Administrador
                    </option>
                </select>

                {form.role === "instructor" && (
                    <>
                        <input
                            type="text"
                            name="specialization"
                            placeholder="Especialización"
                            value={form.specialization}
                            onChange={handleChange}
                        />

                        <textarea
                            name="bio"
                            placeholder="Biografía"
                            value={form.bio}
                            onChange={handleChange}
                        />
                    </>
                )}

                <button type="submit">
                    Registrarse
                </button>

                <button
                    type="button"
                    onClick={() => navigate("/login")}
                >
                    Volver al login
                </button>

            </form>

        </div>
    );
};

export default Register;
