import { useCallback, useState } from "react";
import { useParams } from "react-router-dom";

import Layout from "../../components/Layout";
import StateBadge from "../../components/StateBadge";
import { Empty, ErrorState, Loading, Notice } from "../../components/Status";
import { IconLock, IconQuiz } from "../../components/icons";
import { useResource } from "../../hooks/useResource";
import { getAssessment, submitAttempt } from "../../services/assessmentService";
import { getErrorMessage } from "../../services/errors";
import { formatDateTime } from "../../utils/format";

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
            <div className="table-wrap">
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
                                <td>
                                    <span className={`badge ${attempt.passed ? "badge-success" : "badge-error"}`}>
                                        {attempt.passed ? "Aprobado" : "No aprobado"}
                                    </span>
                                </td>
                                <td className="cell-nowrap">{formatDateTime(attempt.submitted_at)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
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
                <section className="panel">
                    <div className="card-head">
                        <h2>{assessment.title}</h2>
                        <StateBadge state={assessment.state} />
                    </div>

                    {assessment.description && <p>{assessment.description}</p>}

                    <p className="meta-inline">
                        <span>Puntaje máximo {assessment.max_score}</span>
                        <span>Aprueba con {assessment.passing_score}%</span>
                        <span>Intentos restantes: {remaining}</span>
                    </p>
                </section>

                <Notice notice={notice} />

                {lastAttempt && (
                    <section className={`result-card ${lastAttempt.passed ? "is-passed" : "is-failed"}`}>
                        <span className="result-score">{lastAttempt.percentage}%</span>
                        <div>
                            <h3>{lastAttempt.passed ? "Aprobado" : "No aprobado"}</h3>
                            <p>
                                {lastAttempt.score}/{lastAttempt.max_score} puntos
                            </p>
                        </div>
                    </section>
                )}

                {canAnswer ? (
                    (assessment.questions || []).length === 0 ? (
                        <Empty icon={IconQuiz}>La evaluación no tiene preguntas.</Empty>
                    ) : (
                        <form className="form-card" onSubmit={handleSubmit}>
                            {assessment.questions.map((question, index) => (
                                <fieldset
                                    className="question-block"
                                    key={question.question_id}
                                >
                                    <legend className="question-title">
                                        {index + 1}. {question.text}{" "}
                                        <span className="muted">
                                            ({question.points} pts)
                                        </span>
                                    </legend>

                                    {question.options.map((option, optionIndex) => (
                                        <label className="option" key={optionIndex}>
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

                            <div className="form-footer">
                                <button
                                    type="submit"
                                    className={`btn btn-primary${sending ? " is-loading" : ""}`}
                                    disabled={sending}
                                    aria-busy={sending}
                                >
                                    Enviar respuestas
                                </button>
                            </div>
                        </form>
                    )
                ) : (
                    <Empty icon={IconLock}>
                        {assessment.state === "closed"
                            ? "La evaluación está cerrada."
                            : "Ya usaste todos tus intentos."}
                    </Empty>
                )}

                <section className="section">
                    <h3>Mis intentos</h3>
                    {renderAttempts(attempts)}
                </section>
            </>
        );
    };

    return (
        <Layout
            title="Evaluación"
            back={
                assessment
                    ? {
                        to: `/student/course/${assessment.course_id}/assessments`,
                        label: "Volver a evaluaciones",
                    }
                    : undefined
            }
        >
            {renderBody()}
        </Layout>
    );
};

export default TakeAssessment;
