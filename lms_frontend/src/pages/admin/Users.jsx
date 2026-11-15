import Layout from "../../components/Layout";
import { Empty, ErrorState, Loading } from "../../components/Status";
import { useResource } from "../../hooks/useResource";
import { getUsers } from "../../services/userService";

const Users = () => {

    const { data: users, error, loading, reload } = useResource(getUsers);

    const renderBody = () => {
        if (loading && !users) {
            return <Loading text="Cargando usuarios..." />;
        }

        if (error) {
            return (
                <ErrorState
                    error={error}
                    fallback="No se pudieron cargar los usuarios."
                    onRetry={reload}
                />
            );
        }

        if (!users || users.length === 0) {
            return <Empty>No hay usuarios registrados.</Empty>;
        }

        return (
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

                        <tr key={user.user_id}>

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
        );
    };

    return (
        <Layout title="Usuarios">
            {renderBody()}
        </Layout>
    );
};

export default Users;
