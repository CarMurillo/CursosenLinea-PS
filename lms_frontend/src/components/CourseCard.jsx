const CourseCard = ({
    course,
    onEnroll,
    showEnroll = false
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
                Tipo: {course.course_type}
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

        </div>
    );
};

export default CourseCard;