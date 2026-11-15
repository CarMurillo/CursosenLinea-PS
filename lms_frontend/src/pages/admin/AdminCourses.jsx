import Layout from "../../components/Layout";
import CourseCard from "../../components/CourseCard";
import { Empty, ErrorState, Loading } from "../../components/Status";
import { useResource } from "../../hooks/useResource";
import { getCourses } from "../../services/courseService";

// Listado de todos los cursos del sistema (solo lectura).
const AdminCourses = () => {

    const { data, error, loading, reload } = useResource(getCourses);

    const renderBody = () => {
        if (loading && !data) {
            return <Loading text="Cargando cursos..." />;
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
            return <Empty>No hay cursos en el sistema.</Empty>;
        }

        return (
            <div className="course-grid">
                {data.map((course) => (
                    <CourseCard key={course.id} course={course} />
                ))}
            </div>
        );
    };

    return (
        <Layout title="Cursos del sistema">
            {renderBody()}
        </Layout>
    );
};

export default AdminCourses;
