import {
    BrowserRouter,
    Routes,
    Route,
    Navigate
} from "react-router-dom";

import { AuthProvider } from "./context/AuthContext";
import { useAuth } from "./context/auth-context";

import ProtectedRoute from "./components/ProtectedRoute";

import Login from "./pages/Login";
import { NotFound, Unauthorized } from "./pages/ErrorPages";
import Register from "./pages/Register";

import StudentDashboard from "./pages/student/StudentDashboard";
import StudentCourses from "./pages/student/StudentCourses";
import StudentMyCourses from "./pages/student/StudentMyCourses";
import CourseContent from "./pages/student/CourseContent";
import StudentAssessments from "./pages/student/StudentAssessments";
import TakeAssessment from "./pages/student/TakeAssessment";
import StudentLiveSessions from "./pages/student/StudentLiveSessions";
import StudentCertificates from "./pages/student/StudentCertificates";
import StudentRecommendations from "./pages/student/StudentRecommendations";

import InstructorDashboard from "./pages/instructor/InstructorDashboard";
import CreateCourse from "./pages/instructor/CreateCourse";
import ManageCourses from "./pages/instructor/ManageCourses";
import ManageContent from "./pages/instructor/ManageContent";
import ManageAssessments from "./pages/instructor/ManageAssessments";
import ManageLiveSessions from "./pages/instructor/ManageLiveSessions";
import PatternLab from "./pages/instructor/PatternLab";

import AdminDashboard from "./pages/admin/AdminDashboard";
import Users from "./pages/admin/Users";
import UserDetail from "./pages/admin/UserDetail";
import AdminCourses from "./pages/admin/AdminCourses";
import AuditLog from "./pages/admin/AuditLog";

const HOME_BY_ROLE = {
    student: "/student",
    instructor: "/instructor",
    admin: "/admin",
};

// Ruta inicial: lleva al panel del rol si hay sesión; si no, al login.
const Home = () => {
    const { user, isAuthenticated } = useAuth();

    return (
        <Navigate
            to={isAuthenticated ? HOME_BY_ROLE[user?.role] || "/login" : "/login"}
            replace
        />
    );
};

// Envuelve una página en ProtectedRoute con el rol (o roles) indicado.
const guard = (role, element) => (
    <ProtectedRoute role={role}>
        {element}
    </ProtectedRoute>
);

const App = () => {

    return (
        <BrowserRouter>

            <AuthProvider>

                <Routes>

                    {/* Públicas */}

                    <Route path="/login" element={<Login />} />
                    <Route path="/register" element={<Register />} />
                    <Route path="/unauthorized" element={<Unauthorized />} />

                    {/* STUDENT */}

                    <Route path="/student" element={guard("student", <StudentDashboard />)} />
                    <Route path="/student/courses" element={guard("student", <StudentCourses />)} />
                    <Route path="/student/my-courses" element={guard("student", <StudentMyCourses />)} />
                    <Route path="/student/course/:courseId/content" element={guard("student", <CourseContent />)} />
                    <Route path="/student/course/:courseId/assessments" element={guard("student", <StudentAssessments />)} />
                    <Route path="/student/course/:courseId/live" element={guard("student", <StudentLiveSessions />)} />
                    <Route path="/student/assessments/:assessmentId" element={guard("student", <TakeAssessment />)} />
                    <Route path="/student/certificates" element={guard("student", <StudentCertificates />)} />
                    <Route path="/student/recommendations" element={guard("student", <StudentRecommendations />)} />

                    {/* INSTRUCTOR */}

                    <Route path="/instructor" element={guard("instructor", <InstructorDashboard />)} />
                    <Route path="/instructor/create-course" element={guard("instructor", <CreateCourse />)} />
                    <Route path="/instructor/courses" element={guard("instructor", <ManageCourses />)} />
                    <Route path="/instructor/course/:courseId/content" element={guard("instructor", <ManageContent />)} />
                    <Route path="/instructor/course/:courseId/assessments" element={guard("instructor", <ManageAssessments />)} />
                    <Route path="/instructor/course/:courseId/live" element={guard("instructor", <ManageLiveSessions />)} />

                    {/* Laboratorio de patrones (instructor y admin) */}

                    <Route path="/patterns" element={guard(["instructor", "admin"], <PatternLab />)} />
                    <Route path="/instructor/patterns" element={<Navigate to="/patterns" replace />} />

                    {/* ADMIN */}

                    <Route path="/admin" element={guard("admin", <AdminDashboard />)} />
                    <Route path="/admin/users" element={guard("admin", <Users />)} />
                    <Route path="/admin/users/:userId" element={guard("admin", <UserDetail />)} />
                    <Route path="/admin/courses" element={guard("admin", <AdminCourses />)} />
                    <Route path="/admin/audit-log" element={guard("admin", <AuditLog />)} />

                    {/* Ruta inicial */}

                    <Route path="/" element={<Home />} />

                    {/* F2: comodín siempre al final (página 404 con regreso al inicio) */}

                    <Route path="*" element={<NotFound />} />

                </Routes>

            </AuthProvider>

        </BrowserRouter>
    );
};

export default App;
