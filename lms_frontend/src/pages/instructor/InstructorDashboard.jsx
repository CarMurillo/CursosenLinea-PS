import { Link } from "react-router-dom";

import Layout from "../../components/Layout";
import { QuickLink, StatCard } from "../../components/StatCard";
import { Empty, Loading } from "../../components/Status";
import {
    IconArrowRight,
    IconAward,
    IconBroadcast,
    IconFlask,
    IconLayers,
    IconPlus,
    IconStar
} from "../../components/icons";
import { useAuth } from "../../context/auth-context";
import { useResource } from "../../hooks/useResource";
import { getCourses } from "../../services/courseService";
import { COURSE_KIND_LABEL, courseKind, formatPrice } from "../../utils/format";

const InstructorDashboard = () => {

    const { user } = useAuth();
    const { data, loading } = useResource(getCourses);

    // Mismo criterio que "Gestionar cursos": cursos cuyo dueño es el usuario.
    const courses = (data || []).filter(
        (course) => course.instructor_id === user?.user_id
    );

    const firstName = (user?.full_name ?? "").split(" ")[0];
    const pending = loading && !data;
    const count = (predicate) => (pending ? "…" : courses.filter(predicate).length);

    return (
        <Layout
            title={`Hola, ${firstName || "instructor"}`}
            subtitle="Gestiona tus cursos, evaluaciones y clases en vivo."
            actions={
                <Link className="btn btn-primary" to="/instructor/create-course">
                    <IconPlus size={18} />
                    Crear curso
                </Link>
            }
        >
            <section className="section" aria-labelledby="indicadores">
                <h2 id="indicadores" className="sr-only">Indicadores</h2>

                <div className="stat-grid">
                    <StatCard
                        icon={IconLayers}
                        label="Cursos propios"
                        value={pending ? "…" : courses.length}
                    />
                    <StatCard
                        icon={IconStar}
                        tone="accent"
                        label="Cursos Premium"
                        value={count((course) => course.premium)}
                    />
                    <StatCard
                        icon={IconBroadcast}
                        tone="violet"
                        label="Clases en vivo"
                        value={count((course) => courseKind(course) === "live")}
                    />
                    <StatCard
                        icon={IconAward}
                        tone="success"
                        label="Con certificado"
                        value={count((course) => course.certificate)}
                    />
                </div>
            </section>

            <section className="section" aria-labelledby="accesos">
                <h2 id="accesos">Accesos rápidos</h2>

                <div className="quick-grid">
                    <QuickLink
                        to="/instructor/courses"
                        icon={IconLayers}
                        title="Mis cursos"
                        text="Contenido, evaluaciones y clases en vivo."
                    />
                    <QuickLink
                        to="/instructor/create-course"
                        icon={IconPlus}
                        title="Crear curso"
                        text="Publica un curso nuevo en minutos."
                    />
                    <QuickLink
                        to="/patterns"
                        icon={IconFlask}
                        tone="accent"
                        title="Laboratorio de patrones"
                        text="Observer, State y Visitor contra la API real."
                    />
                </div>
            </section>

            <section className="section" aria-labelledby="recientes">
                <div className="section-head">
                    <h2 id="recientes">Tus cursos recientes</h2>
                    <Link className="btn-link" to="/instructor/courses">
                        Ver todos
                        <IconArrowRight size={16} />
                    </Link>
                </div>

                {pending ? (
                    <Loading text="Cargando tus cursos..." />
                ) : courses.length === 0 ? (
                    <Empty
                        icon={IconLayers}
                        action={
                            <Link className="btn btn-primary btn-sm" to="/instructor/create-course">
                                Crear mi primer curso
                            </Link>
                        }
                    >
                        Aún no has creado cursos.
                    </Empty>
                ) : (
                    <ul className="list-card">
                        {courses.slice(-4).reverse().map((course) => (
                            <li key={course.id} className="list-row">
                                <span className="stat-icon" aria-hidden="true">
                                    {courseKind(course) === "live"
                                        ? <IconBroadcast size={20} />
                                        : <IconLayers size={20} />}
                                </span>
                                <div className="list-row-body">
                                    <strong>{course.title}</strong>
                                    <span className="muted">
                                        {COURSE_KIND_LABEL[courseKind(course)]} · {formatPrice(course.price)}
                                    </span>
                                </div>
                                <Link
                                    className="btn btn-secondary btn-sm"
                                    to={`/instructor/course/${course.id}/content`}
                                >
                                    Gestionar
                                </Link>
                            </li>
                        ))}
                    </ul>
                )}
            </section>
        </Layout>
    );
};

export default InstructorDashboard;
