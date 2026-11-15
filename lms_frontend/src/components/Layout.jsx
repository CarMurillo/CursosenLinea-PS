import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";

import Navbar from "./Navbar";
import Sidebar from "./Sidebar";
import { IconArrowLeft } from "./icons";

// PageLayout: barra superior, menú lateral y contenido con cabecera de página
// (título, subtítulo, enlace de regreso y acciones).
const Layout = ({ title, subtitle, actions, back, children }) => {
    const location = useLocation();
    const [menuOpen, setMenuOpen] = useState(false);
    const [menuPath, setMenuPath] = useState(location.pathname);

    // Al navegar se cierra el menú móvil (estado derivado, sin efecto).
    if (menuPath !== location.pathname) {
        setMenuPath(location.pathname);
        setMenuOpen(false);
    }

    useEffect(() => {
        if (!menuOpen) {
            return undefined;
        }

        const handleKey = (event) => {
            if (event.key === "Escape") {
                setMenuOpen(false);
            }
        };

        document.addEventListener("keydown", handleKey);

        return () => document.removeEventListener("keydown", handleKey);
    }, [menuOpen]);

    return (
        <div className="layout">

            <a className="skip-link" href="#contenido">
                Saltar al contenido
            </a>

            <Navbar
                menuOpen={menuOpen}
                onToggleMenu={() => setMenuOpen((open) => !open)}
            />

            <div className="content-wrapper">

                <Sidebar open={menuOpen} />

                {menuOpen && (
                    <div
                        className="sidebar-overlay"
                        aria-hidden="true"
                        onClick={() => setMenuOpen(false)}
                    />
                )}

                <main className="main-content" id="contenido" tabIndex={-1}>

                    <div className="page">

                        {(title || subtitle || actions || back) && (
                            <header className="page-header">
                                <div className="page-heading">
                                    {back && (
                                        <Link className="back-link" to={back.to}>
                                            <IconArrowLeft size={16} />
                                            {back.label}
                                        </Link>
                                    )}

                                    {title && <h1>{title}</h1>}

                                    {subtitle && (
                                        <p className="page-subtitle">{subtitle}</p>
                                    )}
                                </div>

                                {actions && (
                                    <div className="page-actions">{actions}</div>
                                )}
                            </header>
                        )}

                        {children}

                    </div>

                </main>

            </div>

        </div>
    );
};

export default Layout;
