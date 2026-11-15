import axios from "axios";

// URL base de la API. Se puede sobrescribir con VITE_API_URL (archivo .env);
// por defecto apunta al backend local (CORS permite localhost:5173 y 127.0.0.1:5173).
export const API_URL =
    import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const api = axios.create({
    baseURL: API_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

// Agregar automáticamente el token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem("token");

        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        return config;
    },
    (error) => Promise.reject(error)
);

// F5: manejo global de 401. Si la sesión es inválida o expiró, se limpia el
// almacenamiento y se redirige a /login. El login fallido (credenciales
// incorrectas) también responde 401, pero ahí la página muestra el error.
api.interceptors.response.use(
    (response) => response,
    (error) => {
        const status = error.response?.status;
        const url = error.config?.url || "";

        if (status === 401 && !url.includes("/auth/login")) {
            localStorage.removeItem("token");
            localStorage.removeItem("user");

            if (window.location.pathname !== "/login") {
                window.location.assign("/login?expired=1");
            }
        }

        return Promise.reject(error);
    }
);

export default api;
