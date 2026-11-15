import { useCallback } from "react";
import { Link, useParams } from "react-router-dom";

import Layout from "../../components/Layout";
import StateBadge from "../../components/StateBadge";
import { Empty, ErrorState, Loading } from "../../components/Status";
import { IconArrowRight, IconQuiz } from "../../components/icons";
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
            return (
                <Empty icon={IconQuiz}>
                    Este curso no tiene evaluaciones publicadas.
                </Empty>
            );
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
                    const canTake = assessment.state === "published" && remaining > 0;

                    return (
                        <article className="card" key={assessment.id}>
                            <div className="card-head">
                                <StateBadge state={assessment.state} />
                                <span className="muted">
                                    Intentos {attempts.length}/{assessment.max_attempts}
                                </span>
                            </div>

                            <h3 className="card-title">{assessment.title}</h3>

                            {assessment.description && (
                                <p className="muted">{assessment.description}</p>
                            )}

                            <p className="meta-inline">
                                <span>{assessment.question_count} preguntas</span>
                                <span>Aprueba con {assessment.passing_score}%</span>
                            </p>

                            {best && (
                                <div className="result-line">
                                    <span>
                                        Mejor resultado: <strong>{best.score}/{best.max_score}</strong>{" "}
                                        ({best.percentage}%)
                                    </span>
                                    <span className={`badge ${best.passed ? "badge-success" : "badge-error"}`}>
                                        {best.passed ? "Aprobado" : "No aprobado"}
                                    </span>
                                </div>
                            )}

                            {assessment.state === "closed" && (
                                <p className="muted">
                                    La evaluación está cerrada; no admite intentos.
                                </p>
                            )}

                            <div className="card-footer">
                                <Link
                                    className={`btn btn-sm ${canTake ? "btn-primary" : "btn-secondary"}`}
                                    to={`/student/assessments/${assessment.id}`}
                                >
                                    {canTake ? "Rendir evaluación" : "Ver resultados"}
                                    <IconArrowRight size={16} />
                                </Link>
                            </div>
                        </article>
                    );
                })}
            </div>
        );
    };

    return (
        <Layout
            title="Evaluaciones"
            back={{ to: `/student/course/${courseId}/content`, label: "Volver al contenido" }}
        >
            {renderBody()}
        </Layout>
    );
};

export default StudentAssessments;
