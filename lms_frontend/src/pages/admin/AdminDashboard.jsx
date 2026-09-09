import Navbar from "../../components/Navbar";
import Sidebar from "../../components/Sidebar";

const AdminDashboard = () => {

    return (
        <div className="layout">

            <Navbar />

            <div className="content-wrapper">

                <Sidebar />

                <main className="main-content">

                    <h1>
                        Panel de administración
                    </h1>

                    <p>
                        Administración general del LMS.
                    </p>

                    <div className="dashboard-cards">

                        <div className="dashboard-card">
                            <h3>Usuarios</h3>
                            <p>
                                Gestionar usuarios registrados.
                            </p>
                        </div>

                        <div className="dashboard-card">
                            <h3>Cursos</h3>
                            <p>
                                Consultar cursos del sistema.
                            </p>
                        </div>

                    </div>

                </main>

            </div>

        </div>
    );
};

export default AdminDashboard;