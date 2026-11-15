import { Link } from "react-router-dom";

import Layout from "../../components/Layout";
import { QuickLink, StatCard } from "../../components/StatCard";
import { Empty, Loading } from "../../components/Status";
import {
    IconArrowRight,
    IconAward,
    IconBook,
    IconChart,
    IconCompass,
    IconSparkle
} from "../../components/icons";
import { useAuth } from "../../context/auth-context";
import { useResource } from "../../hooks/useResource";
import { getMyCertificates } from "../../services/certificateService";
import { getMyEnrolledCourses } from "../../services/courseService";
import { getMyProgress } from "../../services/progressService";
import { getMyRecommendations } from "../../services/recommendationService";

// Indicadores del panel. Cada fuente falla por separado sin romper la página.
const loadOverview = async () => {
    const [courses, certificates, recommendations] = await Promise.all([
        getMyEnrolledCourses().catch(() => null),
        getMyCertificates().catch(() => null),
        getMyRecommendations().catch(() => null),
    ]);

    const progress = courses
        ? await Promise.all(
            courses.map((course) => getMyProgress(course.id).catch(() => null))
        )
        : [];

    const percentages = progress
        .filter(Boolean)
        .map((item) => Number(item.percentage) || 0);

    return {
        enrolled: courses ? courses.length : null,
        averageProgress: percentages.length
            ? Math.round(percentages.reduce((sum, value) => sum + value, 0) / percentages.length)
            : courses ? 0 : null,
        certificates: certificates ? certificates.length : null,
        recommendations: recommendations || [],
    };
};

const StudentDashboard = () => {

    const { user } = useAuth();
    const { data, loading } = useResource(loadOverview);

    const firstName = (user?.full_name ?? "").split(" ")[0];

    return (
        <Layout
            title={`Hola, ${firstName || "bienvenido"}`}
            subtitle="Este es tu resumen de aprendizaje."
        >
            <section className="section" aria-labelledby="indicadores">
                <h2 id="indicadores" className="sr-only">Indicadores</h2>

                <div className="stat-grid">
                    <StatCard
                        icon={IconBook}
                        label="Cursos inscritos"
                        value={loading && !data ? "…" : data?.enrolled}
                    />
                    <StatCard
                        icon={IconChart}
                        tone="success"
                        label="Progreso promedio"
                        value={
                            loading && !data
                                ? "…"
                                : data?.averageProgress === null || data?.averageProgress === undefined
                                    ? null
                                    : `${data.averageProgress}%`
                        }
                    />
                    <StatCard
                        icon={IconAward}
                        tone="accent"
                        label="Certificados"
                        value={loading && !data ? "…" : data?.certificates}
                    />
                </div>
            </section>

            <section className="section" aria-labelledby="accesos">
                <h2 id="accesos">Accesos rápidos</h2>

                <div className="quick-grid">
                    <QuickLink
                        to="/student/courses"
                        icon={IconCompass}
                        title="Explorar cursos"
                        text="Descubre el catálogo completo del LMS."
                    />
                    <QuickLink
                        to="/student/my-courses"
                        icon={IconBook}
                        title="Mis cursos"
                        text="Continúa donde te quedaste."
                    />
                    <QuickLink
                        to="/student/recommendations"
                        icon={IconSparkle}
                        tone="violet"
                        title="Recomendaciones"
                        text="Cursos sugeridos según tu avance."
                    />
                    <QuickLink
                        to="/student/certificates"
                        icon={IconAward}
                        tone="accent"
                        title="Certificados"
                        text="Tus logros al aprobar evaluaciones."
                    />
                </div>
            </section>

            <section className="section" aria-labelledby="sugeridos">
                <div className="section-head">
                    <h2 id="sugeridos">Recomendado para ti</h2>
                    <Link className="btn-link" to="/student/recommendations">
                        Ver todas
                        <IconArrowRight size={16} />
                    </Link>
                </div>

                {loading && !data ? (
                    <Loading text="Calculando recomendaciones..." />
                ) : (data?.recommendations || []).length === 0 ? (
                    <Empty icon={IconSparkle}>
                        Avanza en tus cursos para recibir sugerencias.
                    </Empty>
                ) : (
                    <ul className="list-card">
                        {data.recommendations.slice(0, 3).map((item) => (
                            <li key={item.course_id} className="list-row">
                                <span className="stat-icon stat-icon-violet" aria-hidden="true">
                                    <IconSparkle size={20} />
                                </span>
                                <div className="list-row-body">
                                    <strong>{item.title}</strong>
                                    <span className="muted">{item.reason}</span>
                                </div>
                                <Link className="btn btn-secondary btn-sm" to="/student/courses">
                                    Ver
                                </Link>
                            </li>
                        ))}
                    </ul>
                )}
            </section>
        </Layout>
    );
};

export default StudentDashboard;
