import { useEffect, useState } from "react";
import Navbar from "../../components/Navbar";
import Sidebar from "../../components/Sidebar";
import CourseCard from "../../components/CourseCard";
import { getCourses, enrollCourse } from "../../services/courseService";
import { useAuth } from "../../context/AuthContext";
import { processPayment } from "../../services/paymentService";

import { useNavigate } from "react-router-dom";

const StudentCourses = () => {

    const [courses, setCourses] = useState([]);
    const [error, setError] = useState("");
    const { user } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {

        loadCourses();

    }, []);

    const loadCourses = async () => {

        try {

            const data = await getCourses();

            setCourses(data);

        } catch (error) {

            console.error(error);

            setError(
                "No se pudieron cargar los cursos"
            );
        }
    };

    const handleEnroll = async (course) => {

        try {

            await enrollCourse(
                course.id,
                user.full_name
            );

            alert(
                `Te has inscrito en ${course.title}`
            );

        } catch (error) {

            console.error(error);

            alert(
                error.response?.data?.detail ||
                "No se pudo realizar la inscripción"
            );
        }
    };

    const handlePay = async (
            course,
            gateway
        ) => {

            try {

                const result =
                    await processPayment({
                        amount: course.price,
                        currency: "COP",
                        customer_email: user.email,
                        gateway
                    });


                if (!result.success) {

                    alert(
                        "El pago fue rechazado."
                    );

                    return;
                }


                await enrollCourse(
                    course.id,
                    user.full_name
                );


                alert(
                    `Pago exitoso.\nTransacción: ${result.transaction_id}`
                );

            } catch (error) {

                console.error(error);

                alert(
                    error.response?.data?.detail ||
                    "No se pudo procesar el pago."
                );
            }
        };

    return (
        <div className="layout">

            <Navbar />

            <div className="content-wrapper">

                <Sidebar />

                <main className="main-content">

                    <h1>
                        Cursos disponibles
                    </h1>

                    {error && (
                        <p className="error">
                            {error}
                        </p>
                    )}

                    <div className="course-grid">

                        {courses.map((course) => (

                            <CourseCard
                                key={course.id}
                                course={course}
                                showPay={course.price > 0}
                                showEnroll={course.price === 0}
                                showContent={true}
                                onPay={handlePay}
                                onEnroll={handleEnroll}
                                onContent={(course) =>
                                    navigate(
                                        `/student/course/${course.id}/content`
                                    )
                                }
                            />

                        ))}

                    </div>

                </main>

            </div>

        </div>
    );
};

export default StudentCourses;