
import { useState } from "react";
import Navbar from "../../components/Navbar";
import Sidebar from "../../components/Sidebar";
import { getDemoContentAccess } from "../../services/courseService";

const contentTypes = [
    { type: "video", label: "Video", icon: "play-circle" },
    { type: "quiz", label: "Cuestionario", icon: "clipboard-check" },
    { type: "document", label: "Documento", icon: "file-text" }
];

export default function PatternLab() {
    const [result, setResult] = useState(null);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const checkAccess = async (hasAccess) => {
        setLoading(true);
        setError("");
        setResult(null);

        try {
            const data = await getDemoContentAccess(hasAccess);
            setResult(data);
        } catch (err) {
            setError(
                err.response?.data?.detail ||
                "No fue posible consultar el contenido."
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="layout">
            <Navbar />

            <div className="content-wrapper">
                <Sidebar />

                <main className="main-content">
                    <h1>Laboratorio de patrones GoF</h1>

                    <section>
                        <h2>Proxy: control de acceso</h2>
                        <p>
                            Comprueba cómo el proxy bloquea o permite
                            el acceso al contenido Premium de demostración.
                        </p>

                        <button
                            type="button"
                            disabled={loading}
                            onClick={() => checkAccess(false)}
                        >
                            Probar sin acceso
                        </button>

                        <button
                            type="button"
                            disabled={loading}
                            onClick={() => checkAccess(true)}
                        >
                            Probar con acceso
                        </button>

                        {loading && <p>Consultando...</p>}
                        {error && <p className="error">{error}</p>}

                        {result && (
                            <div>
                                <h3>Contenido permitido</h3>
                                <p>{result.title}</p>
                                <p>
                                    Recurso: {result.resource_url}
                                </p>
                            </div>
                        )}
                    </section>

                    <hr />

                    <section>
                        <h2>Flyweight: tipos de contenido</h2>
                        <p>
                            Los metadatos comunes se reutilizan en el
                            backend para evitar duplicar objetos iguales.
                        </p>

                        <div className="course-grid">
                            {contentTypes.map((item) => (
                                <article
                                    className="course-card"
                                    key={item.type}
                                >
                                    <h3>{item.label}</h3>
                                    <p>Tipo: {item.type}</p>
                                    <p>Icono: {item.icon}</p>
                                </article>
                            ))}
                        </div>
                    </section>

                    <hr />

                    <section>
                        <h2>Facade: operaciones centralizadas</h2>
                        <p>
                            La gestión de cursos utiliza una fachada
                            en el backend para listar, crear, clonar
                            e inscribir estudiantes.
                        </p>
                        <p>
                            Puedes verificar su funcionamiento desde
                            la sección de gestión de cursos existente.
                        </p>
                    </section>
                </main>
            </div>
        </div>
    );
}
