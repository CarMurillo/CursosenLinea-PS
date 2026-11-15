
const CourseCard = ({
    course,
    onEnroll,
    onClone,
    onPay,
    onContent,

    showEnroll = false,
    showClone = false,
    showPay = false,
    showContent = false,

    busy = false,
    children
}) => {

    return (

        <div className="course-card">

            <h3>
                {course.title}
            </h3>

            <p>
                Instructor: {course.instructor}
            </p>

            <p>
                Tipo: {course.type}
            </p>

            <p>
                Precio: {course.price > 0 ? `$${course.price}` : "Gratis"}
                {course.premium && course.base_price !== undefined && (
                    <span className="muted">
                        {" "}(base ${course.base_price} + 20% premium)
                    </span>
                )}
            </p>


            {course.premium && (
                <span>
                    ⭐ Premium
                </span>
            )}


            {course.certificate && (
                <span>
                    🏆 Certificado
                </span>
            )}


            {showPay && (

                <div className="actions">

                    <button
                        className="btn-primary"
                        disabled={busy}
                        onClick={() =>
                            onPay(
                                course,
                                "wompi"
                            )
                        }
                    >
                        Pagar con Wompi
                    </button>


                    <button
                        className="btn-primary"
                        disabled={busy}
                        onClick={() =>
                            onPay(
                                course,
                                "stripe"
                            )
                        }
                    >
                        Pagar con Stripe
                    </button>

                </div>
            )}


            {showEnroll && (

                <button
                    className="btn-primary"
                    disabled={busy}
                    onClick={() =>
                        onEnroll(course)
                    }
                >
                    Inscribirme
                </button>
            )}


            {showClone && (

                <button
                    className="btn-secondary"
                    disabled={busy}
                    onClick={() =>
                        onClone(course)
                    }
                >
                    Clonar curso
                </button>
            )}


            {showContent && (

                <button
                    className="btn-secondary"
                    onClick={() =>
                        onContent(course)
                    }
                >
                    Ver contenido
                </button>
            )}

            {children}

        </div>
    );
};


export default CourseCard;
