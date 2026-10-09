import { useEffect, useState } from "react";
import Navbar from "../../components/Navbar";
import Sidebar from "../../components/Sidebar";
import { getUsers } from "../../services/userService";

const Users = () => {

    const [users, setUsers] = useState([]);

    useEffect(() => {

        loadUsers();

    }, []);

    const loadUsers = async () => {

        try {

            const data = await getUsers();

            setUsers(data);

        } catch (error) {

            console.error(
                "Error cargando usuarios:",
                error
            );

        }
    };

    return (
        <div className="layout">

            <Navbar />

            <div className="content-wrapper">

                <Sidebar />

                <main className="main-content">

                    <h1>
                        Usuarios
                    </h1>

                    <table className="users-table">

                        <thead>

                            <tr>
                                <th>Nombre</th>
                                <th>Email</th>
                                <th>Rol</th>
                                <th>Estado</th>
                            </tr>

                        </thead>

                        <tbody>

                            {users.map((user) => (

                                <tr key={user.id}>

                                    <td>
                                        {user.full_name}
                                    </td>

                                    <td>
                                        {user.email}
                                    </td>

                                    <td>
                                        {user.role}
                                    </td>

                                    <td>
                                        {user.is_active
                                            ? "Activo"
                                            : "Inactivo"}
                                    </td>

                                </tr>

                            ))}

                        </tbody>

                    </table>

                </main>

            </div>

        </div>
    );
};

export default Users;