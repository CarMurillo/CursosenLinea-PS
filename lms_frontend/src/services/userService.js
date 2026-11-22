import api from "./api";

// Administración de usuarios (todas las rutas exigen rol admin).

// role opcional: "student" | "instructor" | "admin".
export const getUsers = async (role) => {
    const response = await api.get("/users/", { params: role ? { role } : {} });
    return response.data;
};

// Ficha: cursos (sin_iniciar | iniciado | terminado), certificados y pagos
// del estudiante, o cursos y alumnos del instructor.
export const getUserDetail = async (userId) => {
    const response = await api.get(`/users/${userId}/detail`);
    return response.data;
};

// Suspender (false) o reactivar (true). 400 si es admin o la propia cuenta.
export const setUserStatus = async (userId, isActive) => {
    const response = await api.patch(`/users/${userId}/status`, { is_active: isActive });
    return response.data;
};

// El admin registra estudiantes o instructores. 409 correo repetido.
export const createUser = async ({ firstName, lastName, email, password, role }) => {
    const response = await api.post("/users/", {
        first_name: firstName,
        last_name: lastName,
        email,
        password,
        role,
    });
    return response.data;
};
