import Navbar from "../../components/Navbar";
import Sidebar from "../../components/Sidebar";
import { useAuth } from "../../context/AuthContext";

const StudentDashboard = () => {

    const { user } = useAuth();

    return (
        <div className="layout">

            <Navbar />

            <div className="content-wrapper">

                <Sidebar />

                <main className="main-content">

                    <h1>
                        Bienvenido, {user?.full_name}
                    </h1>

                    <p>
                        Panel principal del estudiante.
                    </p>

                    <div className="dashboard-cards">

                        <div className="dashboard-card">
                            <h3>Cursos disponibles</h3>
                            <p>
                                Explora los cursos del LMS.
                            </p>
                        </div>

                        <div className="dashboard-card">
                            <h3>Mis cursos</h3>
                            <p>
                                Consulta los cursos en los
                                que estás inscrito.
                            </p>
                        </div>

                    </div>

                </main>

            </div>

        </div>
    );
};

export default StudentDashboard;