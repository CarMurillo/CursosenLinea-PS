import { useState } from "react";
import { Link } from "react-router-dom";

import Layout from "../../components/Layout";
import { Notice } from "../../components/Status";
import { createCourse } from "../../services/courseService";
import { getErrorMessage } from "../../services/errors";

const EMPTY_FORM = {
    title: "",
    price: "",
    course_type: "video",
    premium: false,
    certificate: false
};

const CreateCourse = () => {

    const [form, setForm] = useState(EMPTY_FORM);
    const [notice, setNotice] = useState(null);
    const [created, setCreated] = useState(null);
    const [sending, setSending] = useState(false);

    const handleChange = (e) => {
        setForm({
            ...form,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        setNotice(null);
        setCreated(null);
        setSending(true);

        try {
            // El instructor lo deriva el backend del token.
            const course = await createCourse({
                title: form.title,
                price: Number(form.price),
                course_type: form.course_type,
                premium: form.premium,
                certificate: form.certificate
            });

            setCreated(course);
            setNotice({
                type: "success",
                text: `Curso "${course.title}" creado. Precio final: $${course.price}.`,
            });

            setForm(EMPTY_FORM);

        } catch (err) {
            setNotice({
                type: "error",
                text: getErrorMessage(err, "No se pudo crear el curso"),
            });
        } finally {
            setSending(false);
        }
    };

    return (
        <Layout title="Crear curso">

            <Notice notice={notice} />

            {created && (
                <p>
                    <Link to={`/instructor/course/${created.id}/content`}>
                        Agregar contenido a "{created.title}"
                    </Link>
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

                <label>Precio base (0 = gratis)</label>
                <input
                    name="price"
                    type="number"
                    min="0"
                    step="0.01"
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

                <label className="inline-label">
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
                    Curso Premium (recargo de 20% sobre el precio base)
                </label>

                <label className="inline-label">
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

                <button
                    type="submit"
                    className="btn-primary"
                    disabled={sending}
                >
                    {sending ? "Publicando..." : "Publicar curso"}
                </button>
            </form>
        </Layout>
    );
};

export default CreateCourse;
