
import { useEffect, useState } from "react";
import Navbar from "../../components/Navbar";
import Sidebar from "../../components/Sidebar";
import {
    getCourses,
    getCourseContent,
    getContentMetadata
} from "../../services/courseService";

const CONTENT_TYPES = ["video", "quiz", "document"];

export default function PatternLab() {
    const [courses, setCourses] = useState([]);
    const [result, setResult] = useState(null);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const [metadata, setMetadata] = useState([]);

    useEffect(() => {
        const load = async () => {
            try {
                setCourses(await getCourses());
            } catch (err) {
                console.error(err);
            }

            try {
                // Flyweight: los datos vienen de la fábrica del backend.
                setMetadata(
                    await Promise.all(CONTENT_TYPES.map(getContentMetadata))
                );
            } catch (err) {
                console.error(err);
            }
        };

        load();
    }, []);

    // Proxy: el backend decide con el token del usuario autenticado.
    const checkAccess = async (course) => {
        setLoading(true);
        setError("");
        setResult(null);

        try {
            const data = await getCourseContent(course.id);
            setResult({ course: course.title, content: data });
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
                            El acceso al contenido de un curso Premium lo
                            decide el proxy en el backend según el usuario
                            autenticado y su inscripción. Elige un curso:
                        </p>

                        {courses.length === 0 && <p>No hay cursos creados.</p>}

                        {courses.map((course) => (
                            <button
                                key={course.id}
                                type="button"
                                disabled={loading}
                                onClick={() => checkAccess(course)}
                            >
                                {course.title}
                                {course.premium ? " (Premium)" : ""}
                            </button>
                        ))}

                        {loading && <p>Consultando...</p>}
                        {error && <p className="error">{error}</p>}

                        {result && (
                            <div>
                                <h3>Acceso permitido: {result.course}</h3>
                                <p>
                                    Módulos: {result.content.items?.length ?? 0}
                                </p>
                            </div>
                        )}
                    </section>

                    <hr />

                    <section>
                        <h2>Flyweight: tipos de contenido</h2>
                        <p>
                            Todas las lecciones del mismo tipo comparten un
                            único objeto de metadatos en el backend.
                        </p>

                        <div className="course-grid">
                            {metadata.map((item) => (
                                <article
                                    className="course-card"
                                    key={item.content_type}
                                >
                                    <h3>{item.label}</h3>
                                    <p>Tipo: {item.content_type}</p>
                                    <p>Icono: {item.icon}</p>
                                </article>
                            ))}
                        </div>
                    </section>

                    <hr />

                    <section>
                        <h2>Facade: operaciones centralizadas</h2>
                        <p>
                            La gestión de cursos utiliza una fachada en el
                            backend para listar, crear, clonar e inscribir
                            estudiantes. Puedes verificarlo desde la sección
                            de gestión de cursos.
                        </p>
                    </section>
                </main>
            </div>
        </div>
    );
}
