import {
    useEffect,
    useState
} from "react";

import {
    useParams
} from "react-router-dom";

import Navbar from "../../components/Navbar";
import Sidebar from "../../components/Sidebar";

import {
    getCourseContent
} from "../../services/courseService";


const CourseContent = () => {

    const { courseId } = useParams();

    const [content, setContent] =
        useState(null);

    const [error, setError] =
        useState("");


    useEffect(() => {

        loadContent();

    }, [courseId]);


    const loadContent = async () => {

        try {

            const data =
                await getCourseContent(
                    courseId
                );

            setContent(data);

        } catch (error) {

            console.error(error);

            setError(
                "No se pudo cargar el contenido."
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
                        Contenido del curso
                    </h1>


                    {error && (
                        <p className="error">
                            {error}
                        </p>
                    )}


                    {content?.items?.map(
                        (module, index) => (

                            <div
                                className="dashboard-card"
                                key={index}
                            >

                                <h2>
                                    {module.title}
                                </h2>


                                {module.items.map(
                                    (
                                        lesson,
                                        lessonIndex
                                    ) => (

                                        <div
                                            key={
                                                lessonIndex
                                            }
                                        >

                                            <h3>
                                                {lesson.title}
                                            </h3>

                                            <p>
                                                Tipo:{" "}
                                                {lesson.type}
                                            </p>

                                            <p>
                                                Proveedor:{" "}
                                                {
                                                    lesson.provider
                                                }
                                            </p>

                                            <a
                                                href={
                                                    lesson.url
                                                }
                                                target="_blank"
                                                rel="noreferrer"
                                            >
                                                Abrir contenido
                                            </a>

                                        </div>
                                    )
                                )}

                            </div>
                        )
                    )}

                </main>

            </div>

        </div>
    );
};


export default CourseContent;