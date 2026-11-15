import api from "./api";

export const getMyCertificates = async () => {
    const response = await api.get("/certificates/me");
    return response.data;
};

// Público: verifica un certificado por su código.
export const verifyCertificate = async (code) => {
    const response = await api.get(
        `/certificates/verify/${encodeURIComponent(code)}`
    );
    return response.data;
};
