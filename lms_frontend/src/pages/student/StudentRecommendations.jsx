import { Link } from "react-router-dom";

import Layout from "../../components/Layout";
import { Empty, ErrorState, Loading } from "../../components/Status";
import { useResource } from "../../hooks/useResource";
import { getMyRecommendations } from "../../services/recommendationService";

const RULE_LABELS = {
    refuerzo: "Refuerzo",
    siguiente_nivel: "Siguiente nivel",
    afinidad: "Afinidad",
    gratis_para_empezar: "Gratis para empezar",
    popular: "Popular",
};

// Recomendaciones por reglas: cada una explica su motivo (`reason`).
const StudentRecommendations = () => {

    const { data, error, loading, reload } = useResource(getMyRecommendations);

    const renderBody = () => {
        if (loading && !data) {
            return <Loading text="Calculando recomendaciones..." />;
        }

        if (error) {
            return (
                <ErrorState
                    error={error}
                    fallback="No se pudieron cargar las recomendaciones."
                    onRetry={reload}
                />
            );
        }

        if (!data || data.length === 0) {
            return (
                <Empty>
                    No hay recomendaciones por ahora. Avanza en tus cursos para
                    recibir sugerencias.
                </Empty>
            );
        }

        return (
            <div className="course-grid">
                {data.map((item) => (
                    <div className="course-card" key={item.course_id}>
                        <h3>{item.title}</h3>

                        <div>
                            <span className="badge">
                                {RULE_LABELS[item.rule] || item.rule}
                            </span>
                            {item.premium && <span className="badge">Premium</span>}
                            {item.certificate && (
                                <span className="badge">Certificado</span>
                            )}
                        </div>

                        <p>
                            <strong>Por qué:</strong> {item.reason}
                        </p>

                        <p className="muted">
                            {item.instructor} - {item.type} -{" "}
                            {item.price > 0 ? `$${item.price}` : "Gratis"}
                        </p>

                        <Link to="/student/courses">Ver en el catálogo</Link>
                    </div>
                ))}
            </div>
        );
    };

    return (
        <Layout title="Recomendaciones para ti">
            {renderBody()}
        </Layout>
    );
};

export default StudentRecommendations;
