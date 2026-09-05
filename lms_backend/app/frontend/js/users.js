import { apiFetch } from './api.js';

export async function loadUsers() {
    const listElement = document.getElementById('users-list');
    listElement.innerHTML = 'Cargando...';

    try {
        const users = await apiFetch('/users/');
        listElement.innerHTML = '';
        
        users.forEach(user => {
            const li = document.createElement('li');
            li.textContent = `${user.name} (${user.email}) - Rol: ${user.role}`;
            listElement.appendChild(li);
        });
    } catch (error) {
        listElement.innerHTML = '<li>Error al cargar usuarios.</li>';
    }
}

export async function createUser(userData) {
    await apiFetch('/users/', {
        method: 'POST',
        body: JSON.stringify(userData)
    });
    await loadUsers(); // Recarga la lista tras crear
}

// Función para obtener y pintar la lista de usuarios
export async function renderUsers() {
    const listContainer = document.getElementById('users-list');
    
    try {
        // 1. Petición al endpoint GET
        const users = await apiFetch('/users/');
        
        // 2. Limpiar la lista antes de volver a pintar
        listContainer.innerHTML = '';

        if (users.length === 0) {
            listContainer.innerHTML = '<li>No hay usuarios registrados.</li>';
            return;
        }

        // 3. Crear un elemento <li> por cada usuario en la BD
        users.forEach(user => {
            const li = document.createElement('li');
            li.textContent = `${user.name} - ${user.email} (${user.role})`;
            listContainer.appendChild(li);
        });

    } catch (error) {
        console.error('Error al cargar usuarios:', error);
        listContainer.innerHTML = '<li>Error al conectar con el servidor.</li>';
    }
}
