import { useCallback } from "react";
import { useParams } from "react-router-dom";

import Layout from "../../components/Layout";
import LiveSessionCard from "../../components/LiveSessionCard";
import { Empty, ErrorState, Loading } from "../../components/Status";
import { IconBroadcast, IconRefresh } from "../../components/icons";
import { useResource } from "../../hooks/useResource";
import { getCourseLiveSessions } from "../../services/liveSessionService";

const StudentLiveSessions = () => {

    const { courseId } = useParams();

    const loader = useCallback(
        () => getCourseLiveSessions(courseId),
        [courseId]
    );

    const { data, error, loading, reload } = useResource(loader);

    const renderBody = () => {
        if (loading && !data) {
            return <Loading text="Cargando clases..." />;
        }

        if (error) {
            return (
                <ErrorState
                    error={error}
                    fallback="No se pudieron cargar las clases en vivo."
                    onRetry={reload}
                />
            );
        }

        if (!data || data.length === 0) {
            return (
                <Empty icon={IconBroadcast}>
                    No hay clases en vivo programadas.
                </Empty>
            );
        }

        return (
            <div className="course-grid">
                {data.map((session) => (
                    <LiveSessionCard key={session.id} session={session} />
                ))}
            </div>
        );
    };

    return (
        <Layout
            title="Clases en vivo"
            back={{ to: `/student/course/${courseId}/content`, label: "Volver al contenido" }}
            actions={
                <button type="button" className="btn btn-secondary" onClick={reload}>
                    <IconRefresh size={18} />
                    Actualizar
                </button>
            }
        >
            {renderBody()}
        </Layout>
    );
};

export default StudentLiveSessions;
