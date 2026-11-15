import api from "./api";

// Pago simulado (sandbox). Body: { amount, currency, gateway, course_id }.
// `amount` debe ser >= course.price (el precio ya incluye el recargo premium).
// Si se aprueba, el backend inscribe automáticamente (Observer): no llamar
// a enroll después. 400 rechazo/monto, 409 ya pagado.
export const processPayment = async ({
    amount,
    currency = "USD",
    gateway,
    courseId,
}) => {
    const response = await api.post("/payments/process", {
        amount,
        currency,
        gateway,
        course_id: courseId,
    });

    return response.data;
};

export const getMyPayments = async () => {
    const response = await api.get("/payments/me");
    return response.data;
};
