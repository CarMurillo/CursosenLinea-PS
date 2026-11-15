// Iconos SVG propios: trazo uniforme de 1.8 px sobre una retícula de 24 px.
// Son decorativos por defecto (aria-hidden). Si el icono comunica algo por sí
// solo, pasa `label` y se anuncia como imagen.

const Svg = ({ size = 20, label, className = "", children }) => (
    <svg
        className={`icon ${className}`.trim()}
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        role={label ? "img" : undefined}
        aria-label={label}
        aria-hidden={label ? undefined : true}
        focusable="false"
    >
        {children}
    </svg>
);

export const IconHome = (props) => (
    <Svg {...props}>
        <path d="M3 10.5 12 3l9 7.5" />
        <path d="M5 9.5V21h5v-6h4v6h5V9.5" />
    </Svg>
);

export const IconCompass = (props) => (
    <Svg {...props}>
        <circle cx="12" cy="12" r="9" />
        <path d="m15.5 8.5-2 5-5 2 2-5z" />
    </Svg>
);

export const IconBook = (props) => (
    <Svg {...props}>
        <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5z" />
        <path d="M4 20.5A2.5 2.5 0 0 0 6.5 23H20v-5" />
    </Svg>
);

export const IconSparkle = (props) => (
    <Svg {...props}>
        <path d="M12 3v4M12 17v4M3 12h4M17 12h4" />
        <path d="m7.5 7.5 2 2M14.5 14.5l2 2M16.5 7.5l-2 2M9.5 14.5l-2 2" />
    </Svg>
);

export const IconAward = (props) => (
    <Svg {...props}>
        <circle cx="12" cy="9" r="6" />
        <path d="m8.5 13.8-1.5 7.2 5-3 5 3-1.5-7.2" />
    </Svg>
);

export const IconStar = (props) => (
    <Svg {...props}>
        <path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z" />
    </Svg>
);

export const IconPlus = (props) => (
    <Svg {...props}>
        <path d="M12 5v14M5 12h14" />
    </Svg>
);

export const IconLayers = (props) => (
    <Svg {...props}>
        <path d="m12 3 9 5-9 5-9-5z" />
        <path d="m3 13 9 5 9-5" />
    </Svg>
);

export const IconFlask = (props) => (
    <Svg {...props}>
        <path d="M9 3h6M10 3v6L4.5 19a1.5 1.5 0 0 0 1.3 2h12.4a1.5 1.5 0 0 0 1.3-2L14 9V3" />
        <path d="M7 15h10" />
    </Svg>
);

export const IconUsers = (props) => (
    <Svg {...props}>
        <circle cx="9" cy="8" r="3.5" />
        <path d="M2.5 20a6.5 6.5 0 0 1 13 0" />
        <path d="M16 4.5a3.5 3.5 0 0 1 0 7M18 14.5a6.5 6.5 0 0 1 3.5 5.5" />
    </Svg>
);

export const IconClipboard = (props) => (
    <Svg {...props}>
        <rect x="5" y="4" width="14" height="17" rx="2" />
        <path d="M9 4V3h6v1M9 10h6M9 14h6M9 18h3" />
    </Svg>
);

export const IconBell = (props) => (
    <Svg {...props}>
        <path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15z" />
        <path d="M10 20.5a2 2 0 0 0 4 0" />
    </Svg>
);

export const IconLogout = (props) => (
    <Svg {...props}>
        <path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3" />
        <path d="M10 16l-4-4 4-4M6 12h10" />
    </Svg>
);

export const IconMenu = (props) => (
    <Svg {...props}>
        <path d="M4 7h16M4 12h16M4 17h16" />
    </Svg>
);

export const IconClose = (props) => (
    <Svg {...props}>
        <path d="M6 6l12 12M18 6 6 18" />
    </Svg>
);

export const IconChevronDown = (props) => (
    <Svg {...props}>
        <path d="m6 9 6 6 6-6" />
    </Svg>
);

export const IconArrowLeft = (props) => (
    <Svg {...props}>
        <path d="M19 12H5M11 6l-6 6 6 6" />
    </Svg>
);

export const IconArrowRight = (props) => (
    <Svg {...props}>
        <path d="M5 12h14M13 6l6 6-6 6" />
    </Svg>
);

export const IconPlay = (props) => (
    <Svg {...props}>
        <circle cx="12" cy="12" r="9" />
        <path d="m10 8.5 5.5 3.5-5.5 3.5z" />
    </Svg>
);

export const IconVideo = (props) => (
    <Svg {...props}>
        <rect x="3" y="6" width="13" height="12" rx="2" />
        <path d="m16 10 5-3v10l-5-3" />
    </Svg>
);

export const IconQuiz = (props) => (
    <Svg {...props}>
        <circle cx="12" cy="12" r="9" />
        <path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .8-1 1.5v.7" />
        <path d="M12 17h.01" />
    </Svg>
);

export const IconDocument = (props) => (
    <Svg {...props}>
        <path d="M6 3h8l4 4v14H6z" />
        <path d="M14 3v4h4M9 12h6M9 16h6" />
    </Svg>
);

export const IconBroadcast = (props) => (
    <Svg {...props}>
        <circle cx="12" cy="12" r="2" />
        <path d="M8.5 8.5a5 5 0 0 0 0 7M15.5 8.5a5 5 0 0 1 0 7" />
        <path d="M5.6 5.6a9 9 0 0 0 0 12.8M18.4 5.6a9 9 0 0 1 0 12.8" />
    </Svg>
);

export const IconClock = (props) => (
    <Svg {...props}>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
    </Svg>
);

export const IconCheck = (props) => (
    <Svg {...props}>
        <path d="m5 12.5 4.5 4.5L19 7.5" />
    </Svg>
);

export const IconCheckCircle = (props) => (
    <Svg {...props}>
        <circle cx="12" cy="12" r="9" />
        <path d="m8 12.5 3 3 5-6" />
    </Svg>
);

export const IconAlert = (props) => (
    <Svg {...props}>
        <path d="M12 3.5 2.5 20h19z" />
        <path d="M12 10v4M12 17h.01" />
    </Svg>
);

export const IconInfo = (props) => (
    <Svg {...props}>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 11v5M12 8h.01" />
    </Svg>
);

export const IconLock = (props) => (
    <Svg {...props}>
        <rect x="4.5" y="10.5" width="15" height="10.5" rx="2" />
        <path d="M8 10.5V7.5a4 4 0 0 1 8 0v3" />
        <path d="M12 15v2" />
    </Svg>
);

export const IconSearch = (props) => (
    <Svg {...props}>
        <circle cx="11" cy="11" r="6.5" />
        <path d="m16 16 4.5 4.5" />
    </Svg>
);

export const IconInbox = (props) => (
    <Svg {...props}>
        <path d="M3 13h5l1.5 3h5L16 13h5" />
        <path d="M5.5 5h13L21 13v6H3v-6z" />
    </Svg>
);

export const IconCopy = (props) => (
    <Svg {...props}>
        <rect x="8" y="8" width="12" height="12" rx="2" />
        <path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3" />
    </Svg>
);

export const IconRefresh = (props) => (
    <Svg {...props}>
        <path d="M20 11a8 8 0 0 0-14.5-4.5M4 13a8 8 0 0 0 14.5 4.5" />
        <path d="M5 3v4h4M19 21v-4h-4" />
    </Svg>
);

export const IconActivity = (props) => (
    <Svg {...props}>
        <path d="M3 12h4l3-8 4 16 3-8h4" />
    </Svg>
);

export const IconCard = (props) => (
    <Svg {...props}>
        <rect x="3" y="5.5" width="18" height="13" rx="2" />
        <path d="M3 10h18M7 15h3" />
    </Svg>
);

export const IconExternal = (props) => (
    <Svg {...props}>
        <path d="M14 4h6v6M20 4l-9 9" />
        <path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" />
    </Svg>
);

export const IconChart = (props) => (
    <Svg {...props}>
        <path d="M4 20V4M4 20h16" />
        <path d="M8 16v-4M12 16V8M16 16v-6" />
    </Svg>
);
