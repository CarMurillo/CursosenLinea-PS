
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { register } from "../services/authService";
import AuthLayout from "../components/AuthLayout";
import { Notice } from "../components/Status";
import { IconBook, IconLayers, IconLock } from "../components/icons";

// Tarjetas seleccionables de rol. El administrador no se registra públicamente
// (el backend responde 403): se muestra deshabilitado como referencia.
const ROLE_OPTIONS = [
    {
        value: "student",
        label: "Estudiante",
        text: "Inscríbete en cursos y obtén certificados.",
        icon: IconBook,
    },
    {
        value: "instructor",
        label: "Instructor",
        text: "Crea cursos, evaluaciones y clases en vivo.",
        icon: IconLayers,
    },
    {
        value: "admin",
        label: "Administrador",
        text: "Solo lo asigna otro administrador.",
        icon: IconLock,
        disabled: true,
    },
];

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
        <AuthLayout
            title="Crear cuenta"
            subtitle="Elige cómo vas a usar CursosenLínea y completa tus datos."
        >
            <form
                className="auth-form"
                onSubmit={handleSubmit}
            >

                <Notice notice={error ? { type: "error", text: error } : null} />
                <Notice notice={success ? { type: "success", text: success } : null} />

                {/* El registro público solo admite student/instructor (admin => 403). */}
                <fieldset className="role-picker">
                    <legend className="field-label">Tipo de cuenta</legend>

                    <div className="role-options">
                        {ROLE_OPTIONS.map(({ value, label, text, icon: Icon, disabled }) => (
                            <label
                                key={value}
                                className={`role-option${disabled ? " is-disabled" : ""}`}
                            >
                                <input
                                    type="radio"
                                    name="role"
                                    value={value}
                                    checked={form.role === value}
                                    onChange={handleChange}
                                    disabled={disabled}
                                    className="role-radio"
                                />
                                <span className="role-option-icon" aria-hidden="true">
                                    <Icon size={22} />
                                </span>
                                <span className="role-option-title">{label}</span>
                                <span className="role-option-text">{text}</span>
                            </label>
                        ))}
                    </div>
                </fieldset>

                <div className="field-row">
                    <div className="field">
                        <label className="field-label" htmlFor="reg-first-name">
                            Nombre
                        </label>
                        <input
                            id="reg-first-name"
                            type="text"
                            name="first_name"
                            autoComplete="given-name"
                            value={form.first_name}
                            onChange={handleChange}
                            required
                        />
                    </div>

                    <div className="field">
                        <label className="field-label" htmlFor="reg-last-name">
                            Apellido
                        </label>
                        <input
                            id="reg-last-name"
                            type="text"
                            name="last_name"
                            autoComplete="family-name"
                            value={form.last_name}
                            onChange={handleChange}
                            required
                        />
                    </div>
                </div>

                <div className="field">
                    <label className="field-label" htmlFor="reg-email">
                        Correo electrónico
                    </label>
                    <input
                        id="reg-email"
                        type="email"
                        name="email"
                        autoComplete="email"
                        placeholder="nombre@correo.com"
                        value={form.email}
                        onChange={handleChange}
                        required
                    />
                </div>

                <div className="field">
                    <label className="field-label" htmlFor="reg-password">
                        Contraseña
                    </label>
                    <input
                        id="reg-password"
                        type="password"
                        name="password"
                        autoComplete="new-password"
                        aria-describedby="reg-password-hint"
                        value={form.password}
                        onChange={handleChange}
                        minLength={8}
                        required
                    />
                    <span className="field-hint" id="reg-password-hint">
                        Mínimo 8 caracteres.
                    </span>
                </div>

                {form.role === "instructor" && (
                    <>
                        <div className="field">
                            <label className="field-label" htmlFor="reg-specialization">
                                Especialización
                            </label>
                            <input
                                id="reg-specialization"
                                type="text"
                                name="specialization"
                                placeholder="Ej.: Ingeniería de software"
                                value={form.specialization}
                                onChange={handleChange}
                            />
                        </div>

                        <div className="field">
                            <label className="field-label" htmlFor="reg-bio">
                                Biografía
                            </label>
                            <textarea
                                id="reg-bio"
                                name="bio"
                                placeholder="Cuéntales a tus estudiantes quién eres."
                                value={form.bio}
                                onChange={handleChange}
                            />
                        </div>
                    </>
                )}

                <button type="submit" className="btn btn-primary btn-block">
                    Registrarse
                </button>

                <p className="auth-switch">
                    ¿Ya tienes cuenta?{" "}
                    <button
                        type="button"
                        className="btn-link"
                        onClick={() => navigate("/login")}
                    >
                        Volver al login
                    </button>
                </p>

            </form>
        </AuthLayout>
    );
};

export default Register;
