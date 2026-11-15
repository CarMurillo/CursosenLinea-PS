import { Link } from "react-router-dom";

import Layout from "../../components/Layout";
import { Empty, ErrorState, Loading } from "../../components/Status";
import { IconArrowRight, IconAward, IconSparkle, IconStar } from "../../components/icons";
import { useResource } from "../../hooks/useResource";
import { getMyRecommendations } from "../../services/recommendationService";
import { COURSE_KIND_LABEL, courseKind, formatPrice } from "../../utils/format";

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
            return <Loading text="Calculando recomendaciones..." variant="cards" />;
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
                <Empty icon={IconSparkle}>
                    No hay recomendaciones por ahora. Avanza en tus cursos para
                    recibir sugerencias.
                </Empty>
            );
        }

        return (
            <div className="course-grid">
                {data.map((item) => (
                    <article className="card card-interactive" key={item.course_id}>
                        <div className="badge-row">
                            <span className="badge badge-live-course">
                                <IconSparkle size={14} />
                                {RULE_LABELS[item.rule] || item.rule}
                            </span>
                            {item.premium && (
                                <span className="badge badge-premium">
                                    <IconStar size={14} />
                                    Premium
                                </span>
                            )}
                            {item.certificate && (
                                <span className="badge badge-certificate">
                                    <IconAward size={14} />
                                    Certificado
                                </span>
                            )}
                        </div>

                        <h3 className="card-title">{item.title}</h3>

                        <p className="reason">
                            <strong>Por qué:</strong> {item.reason}
                        </p>

                        <p className="meta-inline">
                            <span>{item.instructor}</span>
                            <span>{COURSE_KIND_LABEL[courseKind(item)]}</span>
                            <span className="price-inline">{formatPrice(item.price)}</span>
                        </p>

                        <div className="card-footer">
                            <Link className="btn btn-secondary btn-sm" to="/student/courses">
                                Ver en el catálogo
                                <IconArrowRight size={16} />
                            </Link>
                        </div>
                    </article>
                ))}
            </div>
        );
    };

    return (
        <Layout
            title="Recomendaciones para ti"
            subtitle="Sugerencias calculadas con reglas a partir de tu avance."
        >
            {renderBody()}
        </Layout>
    );
};

export default StudentRecommendations;
