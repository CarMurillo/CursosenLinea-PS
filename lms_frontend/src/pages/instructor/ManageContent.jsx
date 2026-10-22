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
    addLesson,
    getCourseContent
} from "../../services/courseService";


const ManageContent = () => {

    const { courseId } = useParams();

    const [content, setContent] =
        useState(null);

    const [form, setForm] = useState({
        module_title: "Módulo 1",
        title: "",
        media_id: "",
        provider: "vimeo",
        lesson_type: "video"
    });

    const [message, setMessage] =
        useState("");

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

        }
    };


    const handleChange = (e) => {

        setForm({
            ...form,
            [e.target.name]:
                e.target.value
        });
    };


    const handleSubmit = async (e) => {

        e.preventDefault();

        setMessage("");
        setError("");


        try {

            await addLesson(
                courseId,
                form
            );

            setMessage(
                "Lección agregada correctamente."
            );

            setForm({
                ...form,
                title: "",
                media_id: ""
            });

            loadContent();

        } catch (error) {

            console.error(error);

            setError(
                error.response?.data?.detail ||
                "No se pudo agregar la lección."
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
                        Administrar contenido
                    </h1>


                    {message && (
                        <p className="success">
                            {message}
                        </p>
                    )}


                    {error && (
                        <p className="error">
                            {error}
                        </p>
                    )}


                    <form
                        className="course-form"
                        onSubmit={
                            handleSubmit
                        }
                    >

                        <label>
                            Módulo
                        </label>

                        <input
                            name="module_title"
                            value={
                                form.module_title
                            }
                            onChange={
                                handleChange
                            }
                            required
                        />


                        <label>
                            Nombre de la lección
                        </label>

                        <input
                            name="title"
                            value={
                                form.title
                            }
                            onChange={
                                handleChange
                            }
                            required
                        />


                        <label>
                            ID multimedia
                        </label>

                        <input
                            name="media_id"
                            value={
                                form.media_id
                            }
                            onChange={
                                handleChange
                            }
                            required
                        />


                        <label>
                            Proveedor
                        </label>

                        <select
                            name="provider"
                            value={
                                form.provider
                            }
                            onChange={
                                handleChange
                            }
                        >

                            <option value="vimeo">
                                Vimeo
                            </option>

                            <option value="s3">
                                AWS S3
                            </option>

                        </select>


                        <label>
                            Tipo de contenido
                        </label>

                        <select
                            name="lesson_type"
                            value={
                                form.lesson_type
                            }
                            onChange={
                                handleChange
                            }
                        >

                            <option value="video">
                                Video
                            </option>

                            <option value="quiz">
                                Quiz
                            </option>

                        </select>


                        <button type="submit">
                            Agregar lección
                        </button>

                    </form>


                    <h2>
                        Contenido actual
                    </h2>


                    {content?.items?.map(
                        (module, index) => (

                            <div
                                className="dashboard-card"
                                key={index}
                            >

                                <h3>
                                    {module.title}
                                </h3>

                                {module.items.map(
                                    (
                                        lesson,
                                        lessonIndex
                                    ) => (

                                        <p
                                            key={
                                                lessonIndex
                                            }
                                        >
                                            {lesson.title}
                                            {" - "}
                                            {lesson.provider}
                                        </p>

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


export default ManageContent;