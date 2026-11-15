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
            return <Loading text="Cargando cursos..." />;
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
            return <Empty>No hay cursos publicados todavía.</Empty>;
        }

        return (
            <div className="course-grid">

                {data.courses.map((course) => {
                    const enrolled = data.enrolledIds.has(course.id);

                    return (
                        <CourseCard
                            key={course.id}
                            course={course}
                            busy={busyId === course.id}
                            showPay={!enrolled && course.price > 0}
                            showEnroll={!enrolled && course.price === 0}
                            showContent={enrolled}
                            onPay={handlePay}
                            onEnroll={handleEnroll}
                            onContent={goToContent}
                        >
                            {enrolled && (
                                <span className="badge badge-published">
                                    Inscrito
                                </span>
                            )}
                        </CourseCard>
                    );
                })}

            </div>
        );
    };

    return (
        <Layout
            title="Cursos disponibles"
            subtitle="Los cursos de pago se habilitan al aprobarse el pago (pasarela simulada)."
        >
            <Notice notice={notice} />

            {renderBody()}
        </Layout>
    );
};

export default StudentCourses;
