// Marca del producto: logotipo propio (página abierta sobre una línea de
// progreso) y nombre. Los colores salen de las variables CSS.
export const BrandMark = ({ size = 32 }) => (
    <svg
        className="brand-mark"
        width={size}
        height={size}
        viewBox="0 0 32 32"
        aria-hidden="true"
        focusable="false"
    >
        <rect className="brand-mark-bg" width="32" height="32" rx="9" />
        <path
            className="brand-mark-page"
            d="M8 10.5c2.8-1.4 5.5-1.4 8 0v11c-2.5-1.4-5.2-1.4-8 0zM16 10.5c2.5-1.4 5.2-1.4 8 0v11c-2.8-1.4-5.5-1.4-8 0z"
        />
        <circle className="brand-mark-dot" cx="24" cy="8" r="2.5" />
    </svg>
);

const Brand = ({ size = 32, tagline = false }) => (
    <span className="brand">
        <BrandMark size={size} />
        <span className="brand-text">
            <span className="brand-name">
                Cursosen<strong>Línea</strong>
            </span>
            {tagline && <span className="brand-tagline">Aprende a tu ritmo</span>}
        </span>
    </span>
);

export default Brand;
