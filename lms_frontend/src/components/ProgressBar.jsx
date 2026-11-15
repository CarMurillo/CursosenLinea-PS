// Barra de progreso (Visitor: porcentaje y minutos completados).
const ProgressBar = ({ progress, compact = false }) => {
    if (!progress) {
        return null;
    }

    const percentage = Math.min(100, Math.max(0, progress.percentage ?? 0));
    const detail = `${progress.completed_lessons}/${progress.total_lessons} lecciones · ${progress.completed_minutes}/${progress.total_minutes} min`;

    return (
        <div className={`progress-block${percentage >= 100 ? " is-complete" : ""}`}>
            <div className="progress-head">
                <span className="progress-value">{percentage}%</span>
                {!compact && <span className="progress-label">{detail}</span>}
            </div>

            <div
                className="progress"
                role="progressbar"
                aria-valuenow={percentage}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuetext={`${percentage}% completado, ${detail}`}
            >
                {/* El ancho es un dato dinámico: única propiedad en línea. */}
                <div
                    className="progress-bar"
                    style={{ width: `${percentage}%` }}
                />
            </div>

            {compact && <span className="progress-label">{detail}</span>}
        </div>
    );
};

export default ProgressBar;
