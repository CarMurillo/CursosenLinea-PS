import { Link } from "react-router-dom";

import Layout from "../../components/Layout";
import { Empty, ErrorState, Loading } from "../../components/Status";
import { useResource } from "../../hooks/useResource";
import { getMyCertificates } from "../../services/certificateService";

// Certificados emitidos por CertificateIssuerObserver al aprobar una evaluación.
const StudentCertificates = () => {

    const { data, error, loading, reload } = useResource(getMyCertificates);

    const renderBody = () => {
        if (loading && !data) {
            return <Loading text="Cargando certificados..." />;
        }

        if (error) {
            return (
                <ErrorState
                    error={error}
                    fallback="No se pudieron cargar los certificados."
                    onRetry={reload}
                />
            );
        }

        if (!data || data.length === 0) {
            return (
                <Empty>
                    Todavía no tienes certificados. Aprueba la evaluación de un
                    curso con certificado para obtener uno.{" "}
                    <Link to="/student/my-courses">Ir a Mis cursos</Link>
                </Empty>
            );
        }

        return (
            <div className="course-grid">
                {data.map((certificate) => (
                    <div className="course-card" key={certificate.certificate_id}>
                        <h3>{certificate.course_title}</h3>

                        <p>Puntaje: {certificate.score}</p>

                        <p className="muted">
                            Emitido: {new Date(certificate.issued_at).toLocaleString()}
                        </p>

                        <p>
                            Código de verificación:{" "}
                            <code>{certificate.verification_code}</code>
                        </p>
                    </div>
                ))}
            </div>
        );
    };

    return (
        <Layout title="Mis certificados">
            {renderBody()}
        </Layout>
    );
};

export default StudentCertificates;
