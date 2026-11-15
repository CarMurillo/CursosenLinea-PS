import { useCallback } from "react";
import { Link, useParams } from "react-router-dom";

import Layout from "../../components/Layout";
import StateBadge from "../../components/StateBadge";
import { Empty, ErrorState, Loading } from "../../components/Status";
import { useResource } from "../../hooks/useResource";
import { getCourseAssessmentsWithAttempts } from "../../services/assessmentService";

// Evaluaciones visibles para el estudiante (publicadas o cerradas).
const StudentAssessments = () => {

    const { courseId } = useParams();

    const loader = useCallback(
        () => getCourseAssessmentsWithAttempts(courseId),
        [courseId]
    );

    const { data, error, loading, reload } = useResource(loader);

    const renderBody = () => {
        if (loading && !data) {
            return <Loading text="Cargando evaluaciones..." />;
        }

        if (error) {
            return (
                <ErrorState
                    error={error}
                    fallback="No se pudieron cargar las evaluaciones."
                    onRetry={reload}
                />
            );
        }

        if (!data || data.length === 0) {
            return <Empty>Este curso no tiene evaluaciones publicadas.</Empty>;
        }

        return (
            <div className="course-grid">
                {data.map((assessment) => {
                    const attempts = assessment.my_attempts || [];
                    const best = attempts.reduce(
                        (top, attempt) =>
                            !top || attempt.percentage > top.percentage
                                ? attempt
                                : top,
                        null
                    );
                    const remaining = Math.max(
                        0,
                        assessment.max_attempts - attempts.length
                    );

                    return (
                        <div className="course-card" key={assessment.id}>
                            <h3>{assessment.title}</h3>

                            <div>
                                <StateBadge state={assessment.state} />
                            </div>

                            {assessment.description && (
                                <p>{assessment.description}</p>
                            )}

                            <p className="muted">
                                {assessment.question_count} preguntas - aprueba con{" "}
                                {assessment.passing_score}% - intentos:{" "}
                                {attempts.length}/{assessment.max_attempts}
                            </p>

                            {best && (
                                <p className={best.passed ? "success" : "error"}>
                                    Mejor resultado: {best.score}/{best.max_score} (
                                    {best.percentage}%){" "}
                                    {best.passed ? "Aprobado" : "No aprobado"}
                                </p>
                            )}

                            {assessment.state === "closed" && (
                                <p className="muted">
                                    La evaluación está cerrada; no admite intentos.
                                </p>
                            )}

                            <Link to={`/student/assessments/${assessment.id}`}>
                                {assessment.state === "published" && remaining > 0
                                    ? "Rendir evaluación"
                                    : "Ver resultados"}
                            </Link>
                        </div>
                    );
                })}
            </div>
        );
    };

    return (
        <Layout title="Evaluaciones">
            <p>
                <Link to={`/student/course/${courseId}/content`}>
                    Volver al contenido
                </Link>
            </p>

            {renderBody()}
        </Layout>
    );
};

export default StudentAssessments;
