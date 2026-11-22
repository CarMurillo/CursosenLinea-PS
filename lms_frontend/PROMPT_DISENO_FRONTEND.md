# PROMPT PARA CLAUDE CODE — Rediseño visual del FRONTEND (lms_frontend)

> Pega esto en Claude Code abierto en la raíz del repo `CursosenLinea-PS/`.
> Córrelo **después** del prompt funcional del frontend, para no diseñar pantallas que luego cambian.
> Si Claude Code tiene disponible el skill `frontend-design`, que lo cargue antes de empezar.

---

## Rol

Eres diseñador de producto y desarrollador frontend senior. Tu trabajo es que el LMS se vea como un producto
profesional y coherente, sin romper ninguna funcionalidad. Trabajas solo en `lms_frontend/`.
Stack: React 19 + Vite + react-router-dom 7. **CSS puro, sin librerías nuevas** (nada de Tailwind, Bootstrap,
MUI ni librerías de iconos). Textos en español.

## Estado actual (verifícalo)

- **`src/App.css` es basura del template de Vite.** Contiene `.hero`, `#center`, `#next-steps`, `#docs`, `.counter`,
  `.ticks` y `#spacer`, que ninguna página usa. Bórralo o reemplázalo.
- **`src/index.css`** tiene todo el estilo real: fuente Arial, grises sueltos (`#1f2937`, `#374151`, `#f5f6fa`, `#ccc`, `#ddd`…),
  sin variables, sin escala de espaciado, sin estados `:hover`/`:focus`/`:disabled` consistentes y sin diseño responsive.
- **`index.html`** tiene `lang="en"` y `<title>lms_frontend</title>`.
- **Las páginas repiten** `layout > Navbar + content-wrapper > Sidebar + main-content`. Las clases en uso son
  `layout`, `content-wrapper`, `main-content`, `course-grid`, `course-card`, `dashboard-cards`, `dashboard-card`,
  `course-form`, `users-table`, `login-container`, `login-form`, `navbar*`, `sidebar`, `role`, `error` y `success`.
- **Las insignias Premium y Certificado** son un `<span>` con emoji sin estilo, y los botones de pago son botones planos.

## Paso 0 — Inventario (no edites todavía)

1. Lista cada página y componente y qué clases usa.
2. Levanta `npm run dev` con el backend y anota en texto, sin capturas, el aspecto actual de: login, registro, los dashboards de los tres roles,
   catálogo, mis cursos, contenido del curso, crear curso, gestionar cursos y contenido, usuarios y PatternLab.
3. Propón en pocas líneas la dirección visual (paleta, tipografía, tono) y sigue con ella sin esperar aprobación.

## Paso 1 — Sistema de diseño (tokens)

Crea `src/styles/tokens.css` con variables CSS e impórtalo primero en `main.jsx`.

- **Color.** Una identidad educativa sobria con un color primario con carácter (por ejemplo un azul petróleo o un índigo profundo),
  un acento cálido para lo Premium (ámbar o dorado) y colores semánticos de éxito, error, aviso e info.
  Cada color necesita sus variantes de fondo suave, texto y borde. Agrega neutrales en escala del 50 al 900.
  Contraste **WCAG AA**: 4.5:1 para texto normal y 3:1 para componentes.
- **Tipografía.** Una pila de fuentes del sistema bien elegida (`"Inter", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`)
  o una fuente de Google Fonts vía `<link>` en `index.html`, sin dependencias npm.
  Escala de tamaños (`--text-xs` … `--text-3xl`), pesos e interlineado.
- **Espaciado** en base 4 (`--space-1` … `--space-12`), radios (`--radius-sm/md/lg/full`), sombras (`--shadow-sm/md/lg`),
  anchura máxima del contenido y transiciones (`--ease`, 150–200 ms).
- **Modo oscuro opcional** con `@media (prefers-color-scheme: dark)` solo si queda bien. Si no, déjalo fuera.

## Paso 2 — Base y componentes CSS

Organiza los estilos en `src/styles/` (`tokens.css`, `base.css`, `layout.css`, `components.css`, `pages.css`) e impórtalos en `main.jsx`.
Usa siempre variables, nunca colores escritos a mano en los componentes.

- **Base.** Reset moderno, tipografía de encabezados y párrafos, enlaces, `:focus-visible` visible en todo lo interactivo,
  y `prefers-reduced-motion`.
- **Botones.** Variantes `btn-primary`, `btn-secondary`, `btn-ghost`, `btn-danger` y `btn-premium`, en tamaños `sm` y `md`,
  con estados hover, active, focus, disabled y cargando (spinner CSS). Los botones de pago con Stripe y Wompi se distinguen por el texto,
  no por logos de marca.
- **Formularios.** Etiqueta, campo, ayuda y error en línea. Inputs, selects, checkboxes y textarea con el mismo alto, borde y foco.
  Agrupa los campos en tarjetas o secciones.
- **Tarjetas:**
  - `card` genérica.
  - `course-card` con encabezado de color según el tipo de curso: video o en vivo.
  - Insignias (`badge`) de Premium, Certificado, Inscrito, tipo de curso y estado de evaluación.
  - Precio destacado con formato `es-CO`.
  - Acciones al pie de la tarjeta.
- **Tablas** (`users-table`): encabezado fijo, filas alternas, insignia de rol y scroll horizontal en móvil.
- **Avisos.** `alert` en variantes success, error, warning e info, que reemplazan `.error` y `.success`. Mantén esas dos clases como
  alias para no romper páginas. Agrega un toast simple si el prompt funcional lo creó.
- **Estados.** Componente o clases para estado vacío (icono SVG inline + texto + acción), cargando (skeleton o spinner) y error.
- **Progreso.** Barra con porcentaje y texto accesible (`role="progressbar"`, `aria-valuenow`).
- **Etiquetas de estado** para evaluaciones (borrador, publicada, cerrada) y clases en vivo (programada, en vivo con punto animado,
  finalizada, grabada).
- **Iconos:** SVG inline propios en `src/components/icons/`, simples y de trazo uniforme. Reemplaza los emojis de las tarjetas.

## Paso 3 — Layout

- Crea o reutiliza `PageLayout` (Navbar + Sidebar + main con título, subtítulo y acciones de página) y aplícalo a **todas** las páginas internas.
- **Navbar:** marca del producto (nombre "CursosenLínea" o el que tenga el proyecto) con un logotipo SVG simple y original,
  avatar con iniciales, nombre, insignia de rol, campana de notificaciones si existe y menú para cerrar sesión.
- **Sidebar:** `NavLink` con estado activo, iconos, secciones por rol y un enlace destacado a PatternLab para el instructor.
- **Responsive:**
  - Escritorio ≥ 1024 px: sidebar fija.
  - Tablet: sidebar compacta.
  - Móvil < 768 px: sidebar como menú desplegable con botón hamburguesa.
  - `course-grid` con `grid-template-columns: repeat(auto-fill, minmax(280px, 1fr))`.
- **Contenido:** ancho máximo cómodo, márgenes generosos y jerarquía clara (título de página → secciones → tarjetas).

## Paso 4 — Páginas

Rediseña cada página usando solo el sistema anterior:

- **Login y registro:** pantalla dividida en escritorio, con la marca y una frase del LMS a un lado y el formulario al otro.
  En móvil, una sola columna. En registro, el rol se elige con tarjetas seleccionables (estudiante, instructor, administrador)
  en vez de un `<select>`.
- **Dashboards:** fila de indicadores (cursos inscritos, progreso promedio, certificados; o cursos propios y estudiantes;
  o usuarios y cursos), accesos rápidos y recomendaciones o actividad reciente.
- **Catálogo:** encabezado con buscador y filtros (tipo, gratis o premium) hechos en el cliente, y grilla de tarjetas.
- **Mis cursos:** tarjetas con barra de progreso y botón "Continuar".
- **Contenido del curso:** cabecera del curso (título, instructor, insignias, progreso y duración total). Debajo, módulos como
  acordeón y lecciones como filas con icono por tipo (video o quiz), duración, proveedor y estado completada.
  El bloqueo Premium (403) se muestra como un panel con candado y botón para adquirir.
- **Crear curso y gestionar contenido:** formulario por secciones. En gestionar contenido, vista previa del árbol a la derecha
  en escritorio y debajo en móvil.
- **Evaluaciones, certificados y clases en vivo** (si existen): listas con etiquetas de estado. Cada certificado como una tarjeta
  tipo diploma con curso, fecha, nota y código.
- **PatternLab:** una tarjeta por patrón con nombre, categoría GoF (creacional, estructural o comportamiento) como insignia,
  descripción breve, botón de demostración y resultado formateado. Usa un bloque `pre` con estilo para el JSON, no el objeto crudo.
- **`/unauthorized` y 404:** página ilustrada con un SVG simple y un botón de regreso.

## Paso 5 — Detalles

- En `index.html`: `lang="es"`, `<title>CursosenLínea · LMS</title>`, favicon propio y `meta description`.
- Microinteracciones discretas: hover de tarjetas (sombra y leve elevación), transiciones de 150–200 ms y nada que distraiga.
- Accesibilidad:
  - Todo se puede usar con teclado.
  - Cada input tiene su `label`.
  - `alt` o `aria-label` en los iconos con significado.
  - Contraste AA.
  - Nada se comunica solo con color: las insignias llevan texto.
- Elimina estilos inline, CSS muerto y clases que ya no se usan. Ningún color escrito a mano fuera de `tokens.css`.
- No cambies lógica, llamadas a la API ni rutas. Si para el diseño necesitas tocar JSX, limítate a estructura y clases.

## Paso 6 — Verificación

1. `npm run lint` y `npm run build` sin errores. Pega la salida real.
2. Recorre todas las páginas, sin tomar capturas, en 1440 px, 768 px y 375 px, con los tres roles, y revisa:
   - No hay scroll horizontal ni texto cortado.
   - Los botones son alcanzables en móvil.
   - El foco es visible.
3. Prueba con datos vacíos, con muchos cursos y con títulos largos.
4. Confirma que los flujos siguen funcionando: login, inscripción, pago, contenido y creación de curso.
5. Consola del navegador sin errores.

## Entrega

- Resumen de la dirección visual (paleta con códigos, tipografía, decisiones clave).
- Archivos creados, modificados y eliminados.
- Salida de lint y build.
- Lista de páginas revisadas en cada ancho y lo que se ajustó (texto breve, sin capturas).

## Restricciones de esta sesión

- **No hagas commits, no crees ramas y no hagas push.** Deja todos los cambios sin confirmar en el árbol de trabajo para que yo los revise primero. Al final muestra `git status` y `git diff --stat`.
- **No tomes capturas de pantalla** de las páginas ni generes imágenes de evidencia. La verificación visual la describes en texto.
