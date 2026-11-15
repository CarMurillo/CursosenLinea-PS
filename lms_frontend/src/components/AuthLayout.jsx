import Brand from "./Brand";
import { IconAward, IconBroadcast, IconChart } from "./icons";

const HIGHLIGHTS = [
    { icon: IconChart, text: "Sigue tu progreso lección a lección." },
    { icon: IconBroadcast, text: "Clases en vivo y cursos bajo demanda." },
    { icon: IconAward, text: "Certificados al aprobar tus evaluaciones." },
];

// Pantalla dividida para login y registro: marca a un lado, formulario al otro.
const AuthLayout = ({ title, subtitle, children }) => (
    <div className="auth">
        <aside className="auth-aside">
            <Brand size={40} tagline />

            <div className="auth-pitch">
                <p className="auth-quote">
                    Aprender es avanzar un paso cada día. Aquí cada paso cuenta.
                </p>

                <ul className="auth-highlights">
                    {HIGHLIGHTS.map(({ icon: Icon, text }) => (
                        <li key={text}>
                            <span className="auth-highlight-icon" aria-hidden="true">
                                <Icon size={18} />
                            </span>
                            {text}
                        </li>
                    ))}
                </ul>
            </div>

            <p className="auth-foot">CursosenLínea · LMS académico</p>
        </aside>

        <main className="auth-main">
            <div className="auth-panel">
                <div className="auth-brand-mobile">
                    <Brand size={36} />
                </div>

                <header className="auth-header">
                    <h1>{title}</h1>
                    {subtitle && <p className="page-subtitle">{subtitle}</p>}
                </header>

                {children}
            </div>
        </main>
    </div>
);

export default AuthLayout;
