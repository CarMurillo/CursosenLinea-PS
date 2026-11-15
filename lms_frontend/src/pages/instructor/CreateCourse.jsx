import { useState } from "react";
import { Link } from "react-router-dom";

import Layout from "../../components/Layout";
import { Notice } from "../../components/Status";
import { IconArrowRight } from "../../components/icons";
import { createCourse } from "../../services/courseService";
import { getErrorMessage } from "../../services/errors";
import { formatPrice } from "../../utils/format";

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

        // Un curso Premium con precio base 0 no se podría adquirir (422 en el backend).
        if (form.premium && !(Number(form.price) > 0)) {
            setNotice({
                type: "error",
                text: "Un curso Premium requiere un precio base mayor que 0.",
            });
            return;
        }

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
                text: `Curso "${course.title}" creado. Precio final: ${formatPrice(course.price)}.`,
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

    // Vista previa del precio final (solo visual; el backend calcula el real).
    const basePrice = Number(form.price) || 0;
    const finalPrice = form.premium ? basePrice * 1.2 : basePrice;

    return (
        <Layout
            title="Crear curso"
            subtitle="Define los datos básicos. Luego podrás agregar contenido, evaluaciones y clases."
            back={{ to: "/instructor/courses", label: "Mis cursos" }}
        >

            <Notice notice={notice} />

            {created && (
                <Link
                    className="btn btn-secondary next-step"
                    to={`/instructor/course/${created.id}/content`}
                >
                    Agregar contenido a "{created.title}"
                    <IconArrowRight size={18} />
                </Link>
            )}

            <form
                className="form-card form-narrow"
                onSubmit={handleSubmit}
            >
                <section className="form-section">
                    <h2 className="form-section-title">Información general</h2>

                    <div className="field">
                        <label className="field-label" htmlFor="course-title">
                            Nombre del curso
                        </label>
                        <input
                            id="course-title"
                            name="title"
                            placeholder="Ej.: Patrones de diseño en Python"
                            value={form.title}
                            onChange={handleChange}
                            required
                        />
                    </div>

                    <div className="field">
                        <label className="field-label" htmlFor="course-type">
                            Tipo de curso
                        </label>
                        <select
                            id="course-type"
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
                    </div>
                </section>

                <section className="form-section">
                    <h2 className="form-section-title">Precio y beneficios</h2>

                    <div className="field">
                        <label className="field-label" htmlFor="course-price">
                            Precio base
                        </label>
                        <input
                            id="course-price"
                            name="price"
                            type="number"
                            min="0"
                            step="0.01"
                            inputMode="decimal"
                            aria-describedby="course-price-hint"
                            value={form.price}
                            onChange={handleChange}
                            required
                        />
                        <span className="field-hint" id="course-price-hint">
                            Escribe 0 para un curso gratuito.
                        </span>
                    </div>

                    <label className="check">
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
                        <span className="check-text">
                            <strong>Curso Premium</strong>
                            <span className="muted">Recargo de 20% sobre el precio base.</span>
                        </span>
                    </label>

                    <label className="check">
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
                        <span className="check-text">
                            <strong>Incluir certificado</strong>
                            <span className="muted">Se emite al aprobar la evaluación del curso.</span>
                        </span>
                    </label>

                    <p className="price-preview">
                        Precio final estimado:{" "}
                        <strong>{formatPrice(finalPrice)}</strong>
                    </p>
                </section>

                <div className="form-footer">
                    <button
                        type="submit"
                        className={`btn btn-primary${sending ? " is-loading" : ""}`}
                        disabled={sending}
                        aria-busy={sending}
                    >
                        Publicar curso
                    </button>
                </div>
            </form>
        </Layout>
    );
};

export default CreateCourse;
