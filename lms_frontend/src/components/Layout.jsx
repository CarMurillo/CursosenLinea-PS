import Navbar from "./Navbar";
import Sidebar from "./Sidebar";

// Estructura común: barra superior, menú lateral y contenido.
const Layout = ({ title, subtitle, children }) => {
    return (
        <div className="layout">

            <Navbar />

            <div className="content-wrapper">

                <Sidebar />

                <main className="main-content">

                    {title && <h1>{title}</h1>}

                    {subtitle && <p>{subtitle}</p>}

                    {children}

                </main>

            </div>

        </div>
    );
};

export default Layout;
