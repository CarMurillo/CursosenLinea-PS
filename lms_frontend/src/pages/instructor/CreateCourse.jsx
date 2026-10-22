import { useState } from "react";
import Navbar from "../../components/Navbar";
import Sidebar from "../../components/Sidebar";
import { createCourse } from "../../services/courseService";
import { useAuth } from "../../context/AuthContext";

const CreateCourse = () => {

    const { user } = useAuth();

    const [form, setForm] = useState({
        title: "",
        price: "",
        course_type: "video",
        premium: false,
        certificate: false
    });

    const [message, setMessage] = useState("");
    const [error, setError] = useState("");

    const handleChange = (e) => {
        setForm({
            ...form,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        setError("");
        setMessage("");

        try {
            await createCourse({
                title: form.title,
                instructor: user.full_name,
                price: Number(form.price),
                course_type: form.course_type,
                premium: form.premium,
                certificate: form.certificate
            });

            setMessage("Curso creado correctamente");

            setForm({
                title: "",
                price: "",
                course_type: "video",
                premium: false,
                certificate: false
            });

        } catch (error) {
            console.error(error);
            setError(
                error.response?.data?.detail ||
                "No se pudo crear el curso"
            );
        }
    };

    return (
        <div className="layout">
            <Navbar />
            <div className="content-wrapper">
                <Sidebar />
                <main className="main-content">
                    <h1>Crear curso</h1>

                    {message && (
                        <p className="success">
                            {message}
                        </p>
                    )}

                    {error && (
                        <p className="error">
                            {error}
                        </p>
                    )}

                    <form
                        className="course-form"
                        onSubmit={handleSubmit}
                    >
                        <label>Nombre del curso</label>
                        <input
                            name="title"
                            value={form.title}
                            onChange={handleChange}
                            required
                        />

                        <label>Precio</label>
                        <input
                            name="price"
                            type="number"
                            value={form.price}
                            onChange={handleChange}
                            required
                        />

                        <label>Tipo de curso</label>
                        <select
                            name="course_type"
                            value={form.course_type}
                            onChange={handleChange}
                        >
                            <option value="video">
                                Video bajo demanda
                            </option>
                            <option value="live">
                                Clase en vivo
                            </option>
                        </select>

                        <label>
                            <input
                                type="checkbox"
                                name="premium"
                                checked={form.premium}
                                onChange={(e) =>
                                    setForm({
                                        ...form,
                                        premium: e.target.checked
                                    })
                                }
                            />
                            Curso Premium
                        </label>

                        <label>
                            <input
                                type="checkbox"
                                name="certificate"
                                checked={form.certificate}
                                onChange={(e) =>
                                    setForm({
                                        ...form,
                                        certificate: e.target.checked
                                    })
                                }
                            />
                            Incluir certificado
                        </label>

                        <button type="submit">
                            Publicar curso
                        </button>
                    </form>
                </main>
            </div>
        </div>
    );
};

export default CreateCourse;