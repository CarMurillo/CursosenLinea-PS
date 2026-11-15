// Barra de progreso (Visitor: porcentaje y minutos completados).
const ProgressBar = ({ progress }) => {
    if (!progress) {
        return null;
    }

    const percentage = Math.min(100, Math.max(0, progress.percentage ?? 0));

    return (
        <div>
            <div
                className="progress"
                role="progressbar"
                aria-valuenow={percentage}
                aria-valuemin={0}
                aria-valuemax={100}
            >
                <div
                    className="progress-bar"
                    style={{ width: `${percentage}%` }}
                />
            </div>

            <span className="progress-label">
                {`${percentage}% - ${progress.completed_lessons}/${progress.total_lessons} lecciones - ${progress.completed_minutes}/${progress.total_minutes} min`}
            </span>
        </div>
    );
};

export default ProgressBar;
