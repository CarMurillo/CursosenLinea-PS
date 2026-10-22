
const CourseCard = ({
    course,
    onEnroll,
    onClone,
    onPay,
    onContent,

    showEnroll = false,
    showClone = false,
    showPay = false,
    showContent = false
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
                Precio: ${course.price}
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

                <div>

                    <button
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
                    onClick={() =>
                        onEnroll(course)
                    }
                >
                    Inscribirme
                </button>
            )}


            {showClone && (

                <button
                    onClick={() =>
                        onClone(course)
                    }
                >
                    Clonar curso
                </button>
            )}


            {showContent && (

                <button
                    onClick={() =>
                        onContent(course)
                    }
                >
                    Ver contenido
                </button>
            )}

        </div>
    );
};


export default CourseCard;