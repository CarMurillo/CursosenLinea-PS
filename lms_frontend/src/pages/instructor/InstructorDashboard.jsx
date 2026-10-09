import Navbar from "../../components/Navbar";
import Sidebar from "../../components/Sidebar";
import { useAuth } from "../../context/AuthContext";

const InstructorDashboard = () => {

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
                        Panel del instructor.
                    </p>

                    <div className="dashboard-cards">

                        <div className="dashboard-card">
                            <h3>Mis cursos</h3>
                            <p>
                                Consulta los cursos creados.
                            </p>
                        </div>

                        <div className="dashboard-card">
                            <h3>Crear curso</h3>
                            <p>
                                Publica un nuevo curso.
                            </p>
                        </div>

                    </div>

                </main>

            </div>

        </div>
    );
};

export default InstructorDashboard;