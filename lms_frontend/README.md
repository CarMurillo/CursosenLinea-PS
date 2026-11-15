# lms_frontend: interfaz del LMS (React + Vite)

React 19, Vite 8, react-router-dom 7 y axios. Consume la API de `lms_backend`.
Ver el [`README.md` raíz](../README.md) para el flujo completo y las cuentas de demostración.

## Ejecutar

```bash
npm install
npm run dev        # http://localhost:5173
npm run lint       # oxlint
npm run build      # genera dist/
```

Requiere Node.js 22 (o 20.19+). El backend debe estar corriendo; la URL base se configura con
`VITE_API_URL` (por defecto `http://127.0.0.1:8000`).

## Estructura

- `src/services/`: un servicio por recurso de la API (`api.js` con axios, `courseService.js`,
  `paymentService.js`, `assessmentService.js`, `liveSessionService.js`, `progressService.js`,
  `notificationService.js`, `recommendationService.js`, `certificateService.js`, …). Las páginas no
  usan URLs sueltas.
- `src/services/api.js`: añade el token `Bearer` y, ante un 401, cierra sesión y redirige a `/login`.
- `src/pages/student/`, `src/pages/instructor/`, `src/pages/admin/`: páginas por rol
  (`PatternLab.jsx` demuestra Observer, State y Visitor).
- `src/context/`: sesión (`AuthContext`), guardada en `localStorage`.
- `src/components/`: `Navbar` (campana de notificaciones), `Sidebar`, `ProtectedRoute`, etc.
