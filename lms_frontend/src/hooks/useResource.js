import { useCallback, useEffect, useState } from "react";

// Carga datos de un servicio con estados de carga, error y recarga.
// `loader` debe ser estable (useCallback) para no recargar en cada render.
// El estado de carga se deriva (sin setState síncrono dentro del efecto).
export const useResource = (loader) => {
    const [version, setVersion] = useState(0);
    const [result, setResult] = useState({
        loader: null,
        version: -1,
        data: undefined,
        error: null,
    });

    useEffect(() => {
        let active = true;

        loader().then(
            (data) => {
                if (active) {
                    setResult({ loader, version, data, error: null });
                }
            },
            (error) => {
                if (active) {
                    setResult({ loader, version, data: undefined, error });
                }
            }
        );

        return () => {
            active = false;
        };
    }, [loader, version]);

    const reload = useCallback(() => setVersion((value) => value + 1), []);

    // Actualiza los datos localmente (p. ej. tras marcar una lección).
    const mutate = useCallback((updater) => {
        setResult((previous) => ({
            ...previous,
            data:
                typeof updater === "function"
                    ? updater(previous.data)
                    : updater,
        }));
    }, []);

    const loading =
        result.loader !== loader || result.version !== version;

    return {
        data: result.data,
        error: result.error,
        loading,
        reload,
        mutate,
    };
};
