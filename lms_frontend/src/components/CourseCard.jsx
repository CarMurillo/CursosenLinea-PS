const CourseCard = ({
    course,
    onEnroll,
    onClone,
    showEnroll = false,
    showClone = false
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
                Tipo: {course.type || course.course_type}
            </p>

            <p>
                Precio: ${course.price}
            </p>

            {showEnroll && (
                <button
                    onClick={() => onEnroll(course)}
                >
                    Inscribirme
                </button>
            )}

            {showClone && (
                <button
                    onClick={() => onClone(course)}
                >
                    Clonar curso
                </button>
            )}

        </div>
    );
};

export default CourseCard;