import { useCallback, useState } from "react";
import { Link, useParams } from "react-router-dom";

import Layout from "../../components/Layout";
import StateBadge from "../../components/StateBadge";
import { Empty, ErrorState, Loading, Notice } from "../../components/Status";
import { useResource } from "../../hooks/useResource";
import { getAssessment, submitAttempt } from "../../services/assessmentService";
import { getErrorMessage } from "../../services/errors";

const formatDate = (iso) => (iso ? new Date(iso).toLocaleString() : "");

// Rendir una evaluación publicada. El backend califica (State: PublishedState)
// y responde 409 si está cerrada o se agotaron los intentos.
const TakeAssessment = () => {

    const { assessmentId } = useParams();

    const loader = useCallback(
        () => getAssessment(assessmentId),
        [assessmentId]
    );

    const { data: assessment, error, loading, reload } = useResource(loader);

    const [answers, setAnswers] = useState({});
    const [notice, setNotice] = useState(null);
    const [lastAttempt, setLastAttempt] = useState(null);
    const [sending, setSending] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setNotice(null);

        const missing = (assessment.questions || []).filter(
            (question) => answers[question.question_id] === undefined
        );

        if (missing.length > 0) {
            setNotice({
                type: "error",
                text: `Responde todas las preguntas (faltan ${missing.length}).`,
            });
            return;
        }

        setSending(true);

        try {
            const attempt = await submitAttempt(assessmentId, answers);

            setLastAttempt(attempt);
            setAnswers({});
            setNotice({
                type: attempt.passed ? "success" : "error",
                text: attempt.passed
                    ? "Evaluación aprobada. Si el curso incluye certificado, ya está disponible en Certificados."
                    : "Evaluación enviada, pero no alcanzaste el puntaje mínimo.",
            });

            reload();

        } catch (err) {
            setNotice({
                type: "error",
                text: getErrorMessage(err, "No se pudo enviar la evaluación."),
            });
        } finally {
            setSending(false);
        }
    };

    const renderAttempts = (attempts) => {
        if (!attempts || attempts.length === 0) {
            return <p className="muted">Aún no tienes intentos.</p>;
        }

        return (
            <table className="users-table">
                <thead>
                    <tr>
                        <th>Intento</th>
                        <th>Puntaje</th>
                        <th>Porcentaje</th>
                        <th>Resultado</th>
                        <th>Fecha</th>
                    </tr>
                </thead>
                <tbody>
                    {attempts.map((attempt) => (
                        <tr key={attempt.attempt_id}>
                            <td>{attempt.attempt_number}</td>
                            <td>{attempt.score}/{attempt.max_score}</td>
                            <td>{attempt.percentage}%</td>
                            <td className={attempt.passed ? "success" : "error"}>
                                {attempt.passed ? "Aprobado" : "No aprobado"}
                            </td>
                            <td>{formatDate(attempt.submitted_at)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        );
    };

    const renderBody = () => {
        if (loading && !assessment) {
            return <Loading text="Cargando evaluación..." />;
        }

        if (error) {
            return (
                <ErrorState
                    error={error}
                    fallback="No se pudo cargar la evaluación."
                    onRetry={reload}
                />
            );
        }

        const attempts = assessment.my_attempts || [];
        const remaining = Math.max(0, assessment.max_attempts - attempts.length);
        const canAnswer = assessment.state === "published" && remaining > 0;

        return (
            <>
                <div className="panel">
                    <h2>{assessment.title}</h2>

                    <div>
                        <StateBadge state={assessment.state} />
                    </div>

                    {assessment.description && <p>{assessment.description}</p>}

                    <p className="muted">
                        Puntaje máximo {assessment.max_score} - aprueba con{" "}
                        {assessment.passing_score}% - intentos restantes: {remaining}
                    </p>
                </div>

                <Notice notice={notice} />

                {lastAttempt && (
                    <div className="panel">
                        <h3>Resultado</h3>
                        <p>
                            {lastAttempt.score}/{lastAttempt.max_score} puntos (
                            {lastAttempt.percentage}%) -{" "}
                            <strong className={lastAttempt.passed ? "success" : "error"}>
                                {lastAttempt.passed ? "Aprobado" : "No aprobado"}
                            </strong>
                        </p>
                    </div>
                )}

                {canAnswer ? (
                    (assessment.questions || []).length === 0 ? (
                        <Empty>La evaluación no tiene preguntas.</Empty>
                    ) : (
                        <form className="panel" onSubmit={handleSubmit}>
                            {assessment.questions.map((question, index) => (
                                <fieldset
                                    className="question-block"
                                    key={question.question_id}
                                >
                                    <strong>
                                        {index + 1}. {question.text}{" "}
                                        <span className="muted">
                                            ({question.points} pts)
                                        </span>
                                    </strong>

                                    {question.options.map((option, optionIndex) => (
                                        <label key={optionIndex}>
                                            <input
                                                type="radio"
                                                name={question.question_id}
                                                checked={
                                                    answers[question.question_id] ===
                                                    optionIndex
                                                }
                                                onChange={() =>
                                                    setAnswers({
                                                        ...answers,
                                                        [question.question_id]:
                                                            optionIndex,
                                                    })
                                                }
                                            />
                                            {option}
                                        </label>
                                    ))}
                                </fieldset>
                            ))}

                            <button
                                type="submit"
                                className="btn-primary"
                                disabled={sending}
                            >
                                {sending ? "Enviando..." : "Enviar respuestas"}
                            </button>
                        </form>
                    )
                ) : (
                    <p className="status status-empty">
                        {assessment.state === "closed"
                            ? "La evaluación está cerrada."
                            : "Ya usaste todos tus intentos."}
                    </p>
                )}

                <div className="panel">
                    <h3>Mis intentos</h3>
                    {renderAttempts(attempts)}
                </div>

                <p>
                    <Link to={`/student/course/${assessment.course_id}/assessments`}>
                        Volver a evaluaciones
                    </Link>
                </p>
            </>
        );
    };

    return (
        <Layout title="Evaluación">
            {renderBody()}
        </Layout>
    );
};

export default TakeAssessment;
