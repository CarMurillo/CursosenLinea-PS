import { useState } from "react";
import { useNavigate } from "react-router-dom";

import Layout from "../../components/Layout";
import CourseCard from "../../components/CourseCard";
import { Empty, ErrorState, Loading, Notice } from "../../components/Status";
import { useResource } from "../../hooks/useResource";
import {
    enrollCourse,
    getCourses,
    getMyEnrolledCourses
} from "../../services/courseService";
import { processPayment } from "../../services/paymentService";
import { getErrorMessage } from "../../services/errors";
import { IconCompass, IconSearch } from "../../components/icons";
import { courseKind } from "../../utils/format";

const PRICE_FILTERS = [
    { value: "all", label: "Todos" },
    { value: "free", label: "Gratis" },
    { value: "premium", label: "Premium" },
];

// Wompi opera en pesos colombianos y Stripe en dólares (ambos simulados).
const CURRENCY_BY_GATEWAY = {
    wompi: "COP",
    stripe: "USD",
};

const loadCatalog = async () => {
    const [courses, enrolled] = await Promise.all([
        getCourses(),
        getMyEnrolledCourses(),
    ]);

    return {
        courses,
        enrolledIds: new Set(enrolled.map((course) => course.id)),
    };
};

const StudentCourses = () => {

    const navigate = useNavigate();
    const { data, error, loading, reload } = useResource(loadCatalog);

    const [notice, setNotice] = useState(null);
    const [busyId, setBusyId] = useState(null);

    const [query, setQuery] = useState("");
    const [kind, setKind] = useState("all");
    const [price, setPrice] = useState("all");

    const goToContent = (course) =>
        navigate(`/student/course/${course.id}/content`);

    // Curso gratuito: inscripción directa (por token, sin cuerpo).
    const handleEnroll = async (course) => {
        setNotice(null);
        setBusyId(course.id);

        try {
            await enrollCourse(course.id);

            setNotice({
                type: "success",
                text: `Te inscribiste en "${course.title}". Ya puedes ver el contenido.`,
            });

            reload();

        } catch (err) {
            setNotice({
                type: "error",
                text: getErrorMessage(err, "No se pudo realizar la inscripción."),
            });
        } finally {
            setBusyId(null);
        }
    };

    // F4: pagar -> pago aprobado -> inscripción automática (Observer en el
    // backend) -> acceso al contenido (Proxy). No se llama a enroll después.
    const handlePay = async (course, gateway) => {
        setNotice(null);
        setBusyId(course.id);

        try {
            const result = await processPayment({
                amount: course.price,
                currency: CURRENCY_BY_GATEWAY[gateway],
                gateway,
                courseId: course.id,
            });

            if (!result.success) {
                setNotice({
                    type: "error",
                    text: result.message || "El pago fue rechazado.",
                });
                return;
            }

            setNotice({
                type: "success",
                text: `Pago aprobado (${result.transaction_id}). Quedaste inscrito automáticamente en "${course.title}".`,
            });

            reload();

        } catch (err) {
            setNotice({
                type: "error",
                text: getErrorMessage(err, "No se pudo procesar el pago."),
            });
        } finally {
            setBusyId(null);
        }
    };

    const renderBody = () => {
        if (loading && !data) {
            return <Loading text="Cargando cursos..." variant="cards" />;
        }

        if (error) {
            return (
                <ErrorState
                    error={error}
                    fallback="No se pudieron cargar los cursos."
                    onRetry={reload}
                />
            );
        }

        if (!data || data.courses.length === 0) {
            return (
                <Empty icon={IconCompass} title="Catálogo vacío">
                    No hay cursos publicados todavía.
                </Empty>
            );
        }

        // Filtros en el cliente: texto, tipo y precio.
        const text = query.trim().toLowerCase();
        const visible = data.courses.filter((course) => {
            const matchesText =
                !text ||
                `${course.title} ${course.instructor ?? ""}`.toLowerCase().includes(text);
            const matchesKind = kind === "all" || courseKind(course) === kind;
            const matchesPrice =
                price === "all" ||
                (price === "free" && !(Number(course.price) > 0)) ||
                (price === "premium" && course.premium);

            return matchesText && matchesKind && matchesPrice;
        });

        return (
            <>
                <div className="toolbar" role="search">
                    <div className="search">
                        <IconSearch size={18} />
                        <label className="sr-only" htmlFor="catalog-search">
                            Buscar cursos
                        </label>
                        <input
                            id="catalog-search"
                            type="search"
                            placeholder="Buscar por título o instructor"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                        />
                    </div>

                    <label className="sr-only" htmlFor="catalog-kind">
                        Tipo de curso
                    </label>
                    <select
                        id="catalog-kind"
                        value={kind}
                        onChange={(e) => setKind(e.target.value)}
                    >
                        <option value="all">Todos los tipos</option>
                        <option value="video">Video bajo demanda</option>
                        <option value="live">Clase en vivo</option>
                    </select>

                    <div className="segmented" role="group" aria-label="Precio">
                        {PRICE_FILTERS.map((option) => (
                            <button
                                key={option.value}
                                type="button"
                                aria-pressed={price === option.value}
                                onClick={() => setPrice(option.value)}
                            >
                                {option.label}
                            </button>
                        ))}
                    </div>
                </div>

                <p className="result-count" aria-live="polite">
                    {visible.length === 1
                        ? "1 curso"
                        : `${visible.length} cursos`}
                </p>

                {visible.length === 0 ? (
                    <Empty
                        icon={IconSearch}
                        title="Sin resultados"
                        action={
                            <button
                                type="button"
                                className="btn btn-secondary btn-sm"
                                onClick={() => {
                                    setQuery("");
                                    setKind("all");
                                    setPrice("all");
                                }}
                            >
                                Limpiar filtros
                            </button>
                        }
                    >
                        Ningún curso coincide con la búsqueda.
                    </Empty>
                ) : (
                    <div className="course-grid">

                        {visible.map((course) => {
                            const enrolled = data.enrolledIds.has(course.id);

                            return (
                                <CourseCard
                                    key={course.id}
                                    course={course}
                                    busy={busyId === course.id}
                                    enrolled={enrolled}
                                    showPay={!enrolled && course.price > 0}
                                    showEnroll={!enrolled && course.price === 0}
                                    showContent={enrolled}
                                    contentLabel="Ir al curso"
                                    onPay={handlePay}
                                    onEnroll={handleEnroll}
                                    onContent={goToContent}
                                />
                            );
                        })}

                    </div>
                )}
            </>
        );
    };

    return (
        <Layout
            title="Explorar cursos"
            subtitle="Los cursos de pago se habilitan al aprobarse el pago (pasarela simulada)."
        >
            <Notice notice={notice} />

            {renderBody()}
        </Layout>
    );
};

export default StudentCourses;
