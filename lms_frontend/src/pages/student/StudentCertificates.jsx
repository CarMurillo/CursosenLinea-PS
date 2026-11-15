import { Link } from "react-router-dom";

import Layout from "../../components/Layout";
import { BrandMark } from "../../components/Brand";
import { Empty, ErrorState, Loading } from "../../components/Status";
import { IconAward } from "../../components/icons";
import { useAuth } from "../../context/auth-context";
import { useResource } from "../../hooks/useResource";
import { getMyCertificates } from "../../services/certificateService";
import { formatDate } from "../../utils/format";

// Certificados emitidos por CertificateIssuerObserver al aprobar una evaluación.
const StudentCertificates = () => {

    const { user } = useAuth();
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
                <Empty
                    icon={IconAward}
                    title="Todavía no tienes certificados"
                    action={
                        <Link className="btn btn-primary btn-sm" to="/student/my-courses">
                            Ir a Mis cursos
                        </Link>
                    }
                >
                    Aprueba la evaluación de un curso con certificado para obtener uno.
                </Empty>
            );
        }

        return (
            <div className="diploma-grid">
                {data.map((certificate) => (
                    <article className="diploma" key={certificate.certificate_id}>
                        <div className="diploma-inner">
                            <div className="diploma-head">
                                <BrandMark size={28} />
                                <span className="diploma-kicker">Certificado de aprobación</span>
                            </div>

                            <p className="diploma-text">Se otorga a</p>
                            <p className="diploma-name">{user?.full_name}</p>
                            <p className="diploma-text">por aprobar el curso</p>
                            <h3 className="diploma-course">{certificate.course_title}</h3>

                            <dl className="diploma-meta">
                                <div>
                                    <dt>Fecha</dt>
                                    <dd>{formatDate(certificate.issued_at)}</dd>
                                </div>
                                <div>
                                    <dt>Nota</dt>
                                    <dd>{certificate.score}</dd>
                                </div>
                                <div>
                                    <dt>Código</dt>
                                    <dd><code>{certificate.verification_code}</code></dd>
                                </div>
                            </dl>

                            <span className="diploma-seal" aria-hidden="true">
                                <IconAward size={28} />
                            </span>
                        </div>
                    </article>
                ))}
            </div>
        );
    };

    return (
        <Layout
            title="Mis certificados"
            subtitle="Cada certificado incluye un código de verificación único."
        >
            {renderBody()}
        </Layout>
    );
};

export default StudentCertificates;
