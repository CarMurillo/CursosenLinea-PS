import { useCallback, useState } from "react";
import { Link, useParams } from "react-router-dom";

import Layout from "../../components/Layout";
import StateBadge from "../../components/StateBadge";
import { Empty, ErrorState, Loading, Notice } from "../../components/Status";
import { useResource } from "../../hooks/useResource";
import {
    addQuestion,
    closeAssessment,
    createAssessment,
    getCourseAssessmentsWithAttempts,
    publishAssessment
} from "../../services/assessmentService";
import { getErrorMessage, getErrorStatus } from "../../services/errors";

const EMPTY_ASSESSMENT = {
    title: "",
    description: "",
    passing_score: 60,
    max_attempts: 1,
};

const EMPTY_QUESTION = {
    text: "",
    options: "",
    correct_option: 0,
    points: 1,
};

// Formulario para agregar preguntas (solo en borrador; el backend responde 409 si no).
const QuestionForm = ({ assessmentId, onDone }) => {
    const [form, setForm] = useState(EMPTY_QUESTION);
    const [notice, setNotice] = useState(null);
    const [sending, setSending] = useState(false);

    const options = form.options
        .split("\n")
        .map((option) => option.trim())
        .filter(Boolean);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setNotice(null);

        if (options.length < 2) {
            setNotice({ type: "error", text: "Escribe al menos 2 opciones (una por línea)." });
            return;
        }

        setSending(true);

        try {
            await addQuestion(assessmentId, {
                text: form.text,
                options,
                correct_option: Number(form.correct_option),
                points: Number(form.points),
            });

            setForm(EMPTY_QUESTION);
            setNotice({ type: "success", text: "Pregunta agregada." });
            onDone();

        } catch (err) {
            setNotice({
                type: "error",
                text: getErrorMessage(err, "No se pudo agregar la pregunta."),
            });
        } finally {
            setSending(false);
        }
    };

    return (
        <form className="question-block" onSubmit={handleSubmit}>
            <strong>Nueva pregunta</strong>

            <Notice notice={notice} />

            <input
                placeholder="Enunciado"
                value={form.text}
                onChange={(e) => setForm({ ...form, text: e.target.value })}
                required
            />

            <textarea
                rows={4}
                placeholder="Opciones, una por línea"
                value={form.options}
                onChange={(e) => setForm({ ...form, options: e.target.value })}
            />

            <label>
                Respuesta correcta
                <select
                    value={form.correct_option}
                    onChange={(e) =>
                        setForm({ ...form, correct_option: e.target.value })
                    }
                >
                    {(options.length ? options : ["(escribe opciones)"]).map(
                        (option, index) => (
                            <option key={index} value={index}>
                                {index + 1}. {option}
                            </option>
                        )
                    )}
                </select>
            </label>

            <label>
                Puntos
                <input
                    type="number"
                    min="1"
                    value={form.points}
                    onChange={(e) => setForm({ ...form, points: e.target.value })}
                />
            </label>

            <button type="submit" className="btn-secondary" disabled={sending}>
                Agregar pregunta
            </button>
        </form>
    );
};

// Tarjeta de una evaluación con acciones según su estado (patrón State).
const AssessmentCard = ({ assessment, onChanged }) => {
    const [notice, setNotice] = useState(null);
    const [busy, setBusy] = useState(false);

    const runTransition = async (action, label) => {
        setNotice(null);
        setBusy(true);

        try {
            const updated = await action(assessment.id);

            setNotice({
                type: "success",
                text: `${label}: estado actual "${updated.state}".`,
            });
            onChanged();

        } catch (err) {
            const status = getErrorStatus(err);
            setNotice({
                type: "error",
                text:
                    (status === 409 ? "Transición no permitida: " : "") +
                    getErrorMessage(err, "No se pudo cambiar el estado."),
            });
        } finally {
            setBusy(false);
        }
    };

    const isDraft = assessment.state === "draft";
    const isPublished = assessment.state === "published";
    const attempts = assessment.attempts || [];

    return (
        <div className="panel">
            <h3>{assessment.title}</h3>

            <div>
                <StateBadge state={assessment.state} />
                <span className="muted">
                    {assessment.question_count} preguntas - {assessment.max_score} pts -
                    aprueba con {assessment.passing_score}% - {assessment.max_attempts}{" "}
                    intento(s) - {attempts.length} intento(s) recibidos
                </span>
            </div>

            {assessment.description && <p>{assessment.description}</p>}

            <Notice notice={notice} />

            <div className="actions">
                <button
                    type="button"
                    className="btn-primary"
                    disabled={busy || !isDraft}
                    title={isDraft ? "" : "Solo se publica una evaluación en borrador"}
                    onClick={() => runTransition(publishAssessment, "Publicada")}
                >
                    Publicar
                </button>

                <button
                    type="button"
                    className="btn-danger"
                    disabled={busy || !isPublished}
                    title={isPublished ? "" : "Solo se cierra una evaluación publicada"}
                    onClick={() => runTransition(closeAssessment, "Cerrada")}
                >
                    Cerrar
                </button>
            </div>

            {(assessment.questions || []).length > 0 && (
                <ol style={{ paddingLeft: 20 }}>
                    {assessment.questions.map((question) => (
                        <li key={question.question_id}>
                            {question.text} ({question.points} pts)
                            <span className="muted">
                                {" "}- correcta:{" "}
                                {question.options?.[question.correct_option] ?? "-"}
                            </span>
                        </li>
                    ))}
                </ol>
            )}

            {isDraft && (
                <QuestionForm assessmentId={assessment.id} onDone={onChanged} />
            )}
        </div>
    );
};

const ManageAssessments = () => {

    const { courseId } = useParams();

    const loader = useCallback(
        () => getCourseAssessmentsWithAttempts(courseId),
        [courseId]
    );

    const { data, error, loading, reload } = useResource(loader);

    const [form, setForm] = useState(EMPTY_ASSESSMENT);
    const [notice, setNotice] = useState(null);
    const [sending, setSending] = useState(false);

    const handleChange = (e) =>
        setForm({ ...form, [e.target.name]: e.target.value });

    const handleCreate = async (e) => {
        e.preventDefault();
        setNotice(null);
        setSending(true);

        try {
            const created = await createAssessment({
                course_id: courseId,
                title: form.title,
                description: form.description,
                passing_score: Number(form.passing_score),
                max_attempts: Number(form.max_attempts),
            });

            setNotice({
                type: "success",
                text: `Evaluación "${created.title}" creada en borrador. Agrega preguntas y publícala.`,
            });
            setForm(EMPTY_ASSESSMENT);
            reload();

        } catch (err) {
            setNotice({
                type: "error",
                text: getErrorMessage(err, "No se pudo crear la evaluación."),
            });
        } finally {
            setSending(false);
        }
    };

    const renderList = () => {
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
            return <Empty>Este curso aún no tiene evaluaciones.</Empty>;
        }

        return data.map((assessment) => (
            <AssessmentCard
                key={assessment.id}
                assessment={assessment}
                onChanged={reload}
            />
        ));
    };

    return (
        <Layout
            title="Evaluaciones del curso"
            subtitle="Ciclo de vida: borrador -> publicada -> cerrada. El backend valida cada transición."
        >
            <div className="actions">
                <Link to="/instructor/courses">Volver a mis cursos</Link>
                <Link to={`/instructor/course/${courseId}/content`}>Contenido</Link>
                <Link to={`/instructor/course/${courseId}/live`}>Clases en vivo</Link>
            </div>

            <Notice notice={notice} />

            <form className="course-form" onSubmit={handleCreate}>
                <h3>Nueva evaluación</h3>

                <label>Título</label>
                <input
                    name="title"
                    value={form.title}
                    onChange={handleChange}
                    required
                />

                <label>Descripción</label>
                <textarea
                    name="description"
                    value={form.description}
                    onChange={handleChange}
                />

                <label>Puntaje mínimo para aprobar (%)</label>
                <input
                    name="passing_score"
                    type="number"
                    min="0"
                    max="100"
                    value={form.passing_score}
                    onChange={handleChange}
                />

                <label>Intentos máximos</label>
                <input
                    name="max_attempts"
                    type="number"
                    min="1"
                    max="20"
                    value={form.max_attempts}
                    onChange={handleChange}
                />

                <button type="submit" className="btn-primary" disabled={sending}>
                    Crear evaluación
                </button>
            </form>

            {renderList()}
        </Layout>
    );
};

export default ManageAssessments;
