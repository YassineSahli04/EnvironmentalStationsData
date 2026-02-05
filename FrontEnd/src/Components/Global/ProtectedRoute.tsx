import {Navigate} from "react-router-dom";
import {useAppUser} from "../../Context/AppUserContext";

type ProtectedRouteProps = {
    children: React.ReactNode;
    requiredRole?: "admin" | "user";
};

export default function ProtectedRoute({children, requiredRole = "admin"}: ProtectedRouteProps) {
    const {appUser} = useAppUser();
    if (!appUser || appUser.role !== requiredRole) {
        return <Navigate to="/" />;
    }
    return <>{children}</>;
}