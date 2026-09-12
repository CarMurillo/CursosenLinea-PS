import {
    BrowserRouter,
    Routes,
    Route,
    Navigate
} from "react-router-dom";

import { AuthProvider } from "./context/AuthContext";

import ProtectedRoute from "./components/ProtectedRoute";

import Login from "./pages/Login";
import Register from "./pages/Register";

import StudentDashboard from "./pages/student/StudentDashboard";
import StudentCourses from "./pages/student/StudentCourses";
import StudentMyCourses from "./pages/student/StudentMyCourses";

import InstructorDashboard from "./pages/instructor/InstructorDashboard";
import CreateCourse from "./pages/instructor/CreateCourse";
import ManageCourses from "./pages/instructor/ManageCourses";

import AdminDashboard from "./pages/admin/AdminDashboard";
import Users from "./pages/admin/Users";

const Unauthorized = () => {
    return (
        <div>
            <h1>Acceso no autorizado</h1>
            <p>
                No tienes permisos para acceder a esta página.
            </p>
        </div>
    );
};

const App = () => {

    return (
        <BrowserRouter>

            <AuthProvider>

                <Routes>

                    {/* Públicas */}

                    <Route
                        path="/login"
                        element={<Login />}
                    />

                    <Route
                        path="/register"
                        element={<Register />}
                    />

                    <Route
                        path="/unauthorized"
                        element={<Unauthorized />}
                    />

                    {/* STUDENT */}

                    <Route
                        path="/student"
                        element={
                            <ProtectedRoute role="student">
                                <StudentDashboard />
                            </ProtectedRoute>
                        }
                    />

                    <Route
                        path="/student/courses"
                        element={
                            <ProtectedRoute role="student">
                                <StudentCourses />
                            </ProtectedRoute>
                        }
                    />

                    <Route
                        path="/student/my-courses"
                        element={
                            <ProtectedRoute role="student">
                                <StudentMyCourses /> {/* o <StudentCourses /> mientras la creas */}
                            </ProtectedRoute>
                        }
                    />

                    {/* INSTRUCTOR */}

                    <Route
                        path="/instructor"
                        element={
                            <ProtectedRoute role="instructor">
                                <InstructorDashboard />
                            </ProtectedRoute>
                        }
                    />

                    <Route
                        path="/instructor/create-course"
                        element={
                            <ProtectedRoute role="instructor">
                                <CreateCourse />
                            </ProtectedRoute>
                        }
                    />

                    <Route
                        path="/instructor/courses"
                        element={
                            <ProtectedRoute role="instructor">
                                <ManageCourses />
                            </ProtectedRoute>
                        }
                    />

                    {/* ADMIN */}

                    <Route
                        path="/admin"
                        element={
                            <ProtectedRoute role="admin">
                                <AdminDashboard />
                            </ProtectedRoute>
                        }
                    />

                    <Route
                        path="/admin/users"
                        element={
                            <ProtectedRoute role="admin">
                                <Users />
                            </ProtectedRoute>
                        }
                    />

                    {/* Ruta inicial */}

                    <Route
                        path="/"
                        element={
                            <Navigate
                                to="/login"
                                replace
                            />
                        }
                    />

                    <Route
                        path="*"
                        element={
                            <Navigate
                                to="/login"
                                replace
                            />
                        }
                    />

                </Routes>

            </AuthProvider>

        </BrowserRouter>
    );
};

export default App;