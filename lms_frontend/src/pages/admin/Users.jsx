import Layout from "../../components/Layout";
import { Empty, ErrorState, Loading } from "../../components/Status";
import { IconUsers } from "../../components/icons";
import { useResource } from "../../hooks/useResource";
import { getUsers } from "../../services/userService";
import { initials, ROLE_LABEL } from "../../utils/format";

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
            return <Empty icon={IconUsers}>No hay usuarios registrados.</Empty>;
        }

        return (
            <>
                <p className="result-count">
                    {users.length === 1 ? "1 usuario" : `${users.length} usuarios`}
                </p>

                <div className="table-wrap table-wrap-scroll">
                    <table className="users-table">

                        <caption className="sr-only">Usuarios registrados</caption>

                        <thead>
                            <tr>
                                <th scope="col">Nombre</th>
                                <th scope="col">Email</th>
                                <th scope="col">Rol</th>
                                <th scope="col">Estado</th>
                            </tr>
                        </thead>

                        <tbody>

                            {users.map((user) => (

                                <tr key={user.user_id}>

                                    <td>
                                        <span className="cell-user">
                                            <span className="avatar" aria-hidden="true">
                                                {initials(user.full_name)}
                                            </span>
                                            <strong>{user.full_name}</strong>
                                        </span>
                                    </td>

                                    <td>
                                        {user.email}
                                    </td>

                                    <td>
                                        <span className={`badge role-${user.role}`}>
                                            {ROLE_LABEL[user.role] || user.role}
                                        </span>
                                    </td>

                                    <td>
                                        <span className={`badge ${user.is_active ? "badge-success" : "badge-draft"}`}>
                                            {user.is_active
                                                ? "Activo"
                                                : "Inactivo"}
                                        </span>
                                    </td>

                                </tr>

                            ))}

                        </tbody>

                    </table>
                </div>
            </>
        );
    };

    return (
        <Layout
            title="Usuarios"
            subtitle="Usuarios registrados en el LMS y su rol."
        >
            {renderBody()}
        </Layout>
    );
};

export default Users;
