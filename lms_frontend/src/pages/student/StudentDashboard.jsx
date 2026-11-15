import { Link } from "react-router-dom";

import Layout from "../../components/Layout";
import { useAuth } from "../../context/auth-context";

const StudentDashboard = () => {

    const { user } = useAuth();

    return (
        <Layout
            title={`Bienvenido, ${user?.full_name ?? ""}`}
            subtitle="Panel principal del estudiante."
        >
            <div className="dashboard-cards">

                <div className="dashboard-card">
                    <h3>Cursos disponibles</h3>
                    <p>
                        Explora los cursos del LMS.
                    </p>
                    <Link to="/student/courses">Explorar</Link>
                </div>

                <div className="dashboard-card">
                    <h3>Mis cursos</h3>
                    <p>
                        Consulta los cursos en los
                        que estás inscrito y tu progreso.
                    </p>
                    <Link to="/student/my-courses">Ver mis cursos</Link>
                </div>

                <div className="dashboard-card">
                    <h3>Recomendaciones</h3>
                    <p>
                        Cursos sugeridos según tu avance.
                    </p>
                    <Link to="/student/recommendations">Ver recomendaciones</Link>
                </div>

                <div className="dashboard-card">
                    <h3>Certificados</h3>
                    <p>
                        Certificados obtenidos al aprobar evaluaciones.
                    </p>
                    <Link to="/student/certificates">Ver certificados</Link>
                </div>

            </div>
        </Layout>
    );
};

export default StudentDashboard;
