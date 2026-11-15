import { Link } from "react-router-dom";

import Layout from "../../components/Layout";
import { useAuth } from "../../context/auth-context";

const InstructorDashboard = () => {

    const { user } = useAuth();

    return (
        <Layout
            title={`Bienvenido, ${user?.full_name ?? ""}`}
            subtitle="Panel del instructor."
        >
            <div className="dashboard-cards">

                <div className="dashboard-card">
                    <h3>Mis cursos</h3>
                    <p>
                        Contenido, evaluaciones y clases en vivo de tus cursos.
                    </p>
                    <Link to="/instructor/courses">Gestionar</Link>
                </div>

                <div className="dashboard-card">
                    <h3>Crear curso</h3>
                    <p>
                        Publica un nuevo curso.
                    </p>
                    <Link to="/instructor/create-course">Crear</Link>
                </div>

                <div className="dashboard-card">
                    <h3>Laboratorio de patrones</h3>
                    <p>
                        Observer, State y Visitor contra la API real.
                    </p>
                    <Link to="/patterns">Abrir</Link>
                </div>

            </div>
        </Layout>
    );
};

export default InstructorDashboard;
