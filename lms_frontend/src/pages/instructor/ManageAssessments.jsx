import { useCallback, useState } from "react";
import { useParams } from "react-router-dom";

import Layout from "../../components/Layout";
import CourseTabs from "../../components/CourseTabs";
import StateBadge from "../../components/StateBadge";
import { Empty, ErrorState, Loading, Notice } from "../../components/Status";
import { IconCheck, IconLock, IconPlus, IconQuiz } from "../../components/icons";
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

    const id = (name) => `q-${assessmentId}-${name}`;

    return (
        <form className="question-block" onSubmit={handleSubmit}>
            <strong className="question-title">Nueva pregunta</strong>

            <Notice notice={notice} />

            <div className="field">
                <label className="field-label" htmlFor={id("text")}>
                    Enunciado
                </label>
                <input
                    id={id("text")}
                    value={form.text}
                    onChange={(e) => setForm({ ...form, text: e.target.value })}
                    required
                />
            </div>

            <div className="field">
                <label className="field-label" htmlFor={id("options")}>
                    Opciones
                </label>
                <textarea
                    id={id("options")}
                    rows={4}
                    placeholder="Una opción por línea"
                    aria-describedby={id("options-hint")}
                    value={form.options}
                    onChange={(e) => setForm({ ...form, options: e.target.value })}
                />
                <span className="field-hint" id={id("options-hint")}>
                    Mínimo 2 opciones, una por línea.
                </span>
            </div>

            <div className="field-row">
                <div className="field">
                    <label className="field-label" htmlFor={id("correct")}>
                        Respuesta correcta
                    </label>
                    <select
                        id={id("correct")}
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
                </div>

                <div className="field">
                    <label className="field-label" htmlFor={id("points")}>
                        Puntos
                    </label>
                    <input
                        id={id("points")}
                        type="number"
                        min="1"
                        value={form.points}
                        onChange={(e) => setForm({ ...form, points: e.target.value })}
                    />
                </div>
            </div>

            <div className="form-footer">
                <button
                    type="submit"
                    className={`btn btn-secondary btn-sm${sending ? " is-loading" : ""}`}
                    disabled={sending}
                    aria-busy={sending}
                >
                    <IconPlus size={16} />
                    Agregar pregunta
                </button>
            </div>
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
        <article className="panel">
            <div className="card-head">
                <h3 className="card-title">{assessment.title}</h3>
                <StateBadge state={assessment.state} />
            </div>

            <p className="meta-inline">
                <span>{assessment.question_count} preguntas</span>
                <span>{assessment.max_score} pts</span>
                <span>Aprueba con {assessment.passing_score}%</span>
                <span>{assessment.max_attempts} intento(s)</span>
                <span>{attempts.length} intento(s) recibidos</span>
            </p>

            {assessment.description && <p>{assessment.description}</p>}

            <Notice notice={notice} />

            <div className="actions">
                <button
                    type="button"
                    className="btn btn-primary btn-sm"
                    disabled={busy || !isDraft}
                    title={isDraft ? "" : "Solo se publica una evaluación en borrador"}
                    onClick={() => runTransition(publishAssessment, "Publicada")}
                >
                    <IconCheck size={16} />
                    Publicar
                </button>

                <button
                    type="button"
                    className="btn btn-danger btn-sm"
                    disabled={busy || !isPublished}
                    title={isPublished ? "" : "Solo se cierra una evaluación publicada"}
                    onClick={() => runTransition(closeAssessment, "Cerrada")}
                >
                    <IconLock size={16} />
                    Cerrar
                </button>
            </div>

            {(assessment.questions || []).length > 0 && (
                <ol className="question-list">
                    {assessment.questions.map((question) => (
                        <li key={question.question_id}>
                            <span>
                                {question.text}{" "}
                                <span className="muted">({question.points} pts)</span>
                            </span>
                            <span className="muted">
                                Correcta:{" "}
                                {question.options?.[question.correct_option] ?? "-"}
                            </span>
                        </li>
                    ))}
                </ol>
            )}

            {isDraft && (
                <QuestionForm assessmentId={assessment.id} onDone={onChanged} />
            )}
        </article>
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
            return <Empty icon={IconQuiz}>Este curso aún no tiene evaluaciones.</Empty>;
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
            subtitle="Ciclo de vida: borrador → publicada → cerrada. El backend valida cada transición."
            back={{ to: "/instructor/courses", label: "Mis cursos" }}
        >
            <CourseTabs courseId={courseId} />

            <Notice notice={notice} />

            <div className="split">
                <form className="form-card" onSubmit={handleCreate}>
                    <h2 className="form-section-title">Nueva evaluación</h2>

                    <div className="field">
                        <label className="field-label" htmlFor="assessment-title">
                            Título
                        </label>
                        <input
                            id="assessment-title"
                            name="title"
                            value={form.title}
                            onChange={handleChange}
                            required
                        />
                    </div>

                    <div className="field">
                        <label className="field-label" htmlFor="assessment-description">
                            Descripción
                        </label>
                        <textarea
                            id="assessment-description"
                            name="description"
                            value={form.description}
                            onChange={handleChange}
                        />
                    </div>

                    <div className="field-row">
                        <div className="field">
                            <label className="field-label" htmlFor="assessment-passing">
                                Mínimo para aprobar (%)
                            </label>
                            <input
                                id="assessment-passing"
                                name="passing_score"
                                type="number"
                                min="0"
                                max="100"
                                value={form.passing_score}
                                onChange={handleChange}
                            />
                        </div>

                        <div className="field">
                            <label className="field-label" htmlFor="assessment-attempts">
                                Intentos máximos
                            </label>
                            <input
                                id="assessment-attempts"
                                name="max_attempts"
                                type="number"
                                min="1"
                                max="20"
                                value={form.max_attempts}
                                onChange={handleChange}
                            />
                        </div>
                    </div>

                    <div className="form-footer">
                        <button
                            type="submit"
                            className={`btn btn-primary${sending ? " is-loading" : ""}`}
                            disabled={sending}
                            aria-busy={sending}
                        >
                            Crear evaluación
                        </button>
                    </div>
                </form>

                <section className="split-aside section" aria-label="Evaluaciones existentes">
                    {renderList()}
                </section>
            </div>
        </Layout>
    );
};

export default ManageAssessments;
