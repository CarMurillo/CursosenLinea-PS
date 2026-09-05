import { loadUsers, createUser } from './users.js';
import { renderUsers } from './users.js';
import { apiFetch } from './api.js';

document.addEventListener('DOMContentLoaded', () => {
    // Cargar usuarios al abrir la página
    loadUsers();

    // Capturar el evento del formulario
    const userForm = document.getElementById('user-form');
    userForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const newUser = {
            name: document.getElementById('user-name').value,
            email: document.getElementById('user-email').value,
            role: document.getElementById('user-role').value
        };

        await createUser(newUser);
        userForm.reset();
    });
});

document.addEventListener('DOMContentLoaded', () => {
    // Cargar la lista apenas abra la página
    renderUsers();

    // Evento del formulario para registrar nuevos usuarios
    const userForm = document.getElementById('user-form');
    userForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const newUser = {
            name: document.getElementById('user-name').value,
            email: document.getElementById('user-email').value,
            role: document.getElementById('user-role').value
        };

        // Guardar en la base de datos
        await apiFetch('/users/', {
            method: 'POST',
            body: JSON.stringify(newUser)
        });

        // Recargar la lista automáticamente para mostrar el nuevo registro
        await renderUsers();
        userForm.reset();
    });
});