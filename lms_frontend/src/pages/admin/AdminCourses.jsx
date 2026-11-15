import Layout from "../../components/Layout";
import CourseCard from "../../components/CourseCard";
import { Empty, ErrorState, Loading } from "../../components/Status";
import { IconLayers } from "../../components/icons";
import { useResource } from "../../hooks/useResource";
import { getCourses } from "../../services/courseService";

// Listado de todos los cursos del sistema (solo lectura).
const AdminCourses = () => {

    const { data, error, loading, reload } = useResource(getCourses);

    const renderBody = () => {
        if (loading && !data) {
            return <Loading text="Cargando cursos..." variant="cards" />;
        }

        if (error) {
            return (
                <ErrorState
                    error={error}
                    fallback="No se pudieron cargar los cursos."
                    onRetry={reload}
                />
            );
        }

        if (!data || data.length === 0) {
            return <Empty icon={IconLayers}>No hay cursos en el sistema.</Empty>;
        }

        return (
            <>
                <p className="result-count">
                    {data.length === 1 ? "1 curso" : `${data.length} cursos`}
                </p>

                <div className="course-grid">
                    {data.map((course) => (
                        <CourseCard key={course.id} course={course} />
                    ))}
                </div>
            </>
        );
    };

    return (
        <Layout
            title="Cursos del sistema"
            subtitle="Vista de solo lectura de todos los cursos publicados."
        >
            {renderBody()}
        </Layout>
    );
};

export default AdminCourses;
