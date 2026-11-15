import { COURSE_KIND_LABEL, courseKind, formatPrice } from "../utils/format";
import {
    IconArrowRight,
    IconAward,
    IconBroadcast,
    IconCard,
    IconCheck,
    IconCopy,
    IconStar,
    IconVideo
} from "./icons";

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

    enrolled = false,
    contentLabel = "Ver contenido",

    busy = false,
    children
}) => {

    const kind = courseKind(course);
    const KindIcon = kind === "live" ? IconBroadcast : IconVideo;
    const isPaid = Number(course.price) > 0;
    const hasActions = showPay || showEnroll || showClone || showContent;
    const loadingClass = busy ? " is-loading" : "";

    return (

        <article className={`course-card course-card-${kind}`}>

            <div className="course-card-header">
                <span className="course-kind">
                    <KindIcon size={18} />
                    {COURSE_KIND_LABEL[kind]}
                </span>

                {course.premium && (
                    <span className="badge badge-premium">
                        <IconStar size={14} />
                        Premium
                    </span>
                )}
            </div>

            <div className="course-card-body">

                <h3 className="course-title">
                    {course.title}
                </h3>

                <p className="course-instructor">
                    {course.instructor}
                </p>

                <div className="badge-row">
                    {enrolled && (
                        <span className="badge badge-enrolled">
                            <IconCheck size={14} />
                            Inscrito
                        </span>
                    )}

                    {course.certificate && (
                        <span className="badge badge-certificate">
                            <IconAward size={14} />
                            Certificado
                        </span>
                    )}
                </div>

                <div className="course-price">
                    <span className={`price${isPaid ? "" : " price-free"}`}>
                        {formatPrice(course.price)}
                    </span>

                    {course.premium && course.base_price !== undefined && (
                        <span className="muted">
                            Base {formatPrice(course.base_price)} + 20% premium
                        </span>
                    )}
                </div>

                {children}

            </div>

            {hasActions && (

                <div className="course-card-footer">

                    {showPay && (
                        <>
                            <button
                                type="button"
                                className={`btn ${course.premium ? "btn-premium" : "btn-primary"} btn-sm${loadingClass}`}
                                disabled={busy}
                                aria-busy={busy}
                                onClick={() =>
                                    onPay(
                                        course,
                                        "wompi"
                                    )
                                }
                            >
                                <IconCard size={16} />
                                Pagar con Wompi
                            </button>

                            <button
                                type="button"
                                className={`btn btn-secondary btn-sm${loadingClass}`}
                                disabled={busy}
                                aria-busy={busy}
                                onClick={() =>
                                    onPay(
                                        course,
                                        "stripe"
                                    )
                                }
                            >
                                <IconCard size={16} />
                                Pagar con Stripe
                            </button>
                        </>
                    )}

                    {showEnroll && (
                        <button
                            type="button"
                            className={`btn btn-primary btn-sm${loadingClass}`}
                            disabled={busy}
                            aria-busy={busy}
                            onClick={() =>
                                onEnroll(course)
                            }
                        >
                            Inscribirme gratis
                        </button>
                    )}

                    {showContent && (
                        <button
                            type="button"
                            className="btn btn-primary btn-sm"
                            onClick={() =>
                                onContent(course)
                            }
                        >
                            {contentLabel}
                            <IconArrowRight size={16} />
                        </button>
                    )}

                    {showClone && (
                        <button
                            type="button"
                            className={`btn btn-ghost btn-sm${loadingClass}`}
                            disabled={busy}
                            aria-busy={busy}
                            onClick={() =>
                                onClone(course)
                            }
                        >
                            <IconCopy size={16} />
                            Clonar
                        </button>
                    )}

                </div>
            )}

        </article>
    );
};


export default CourseCard;
