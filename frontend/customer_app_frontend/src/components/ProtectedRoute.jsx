import { Navigate } from "react-router-dom";

import { useSession } from "../context/SessionContext";

function ProtectedRoute({ children, expectedRole }) {
  const { isAuthenticated, session } = useSession();

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  if (expectedRole && session?.role !== expectedRole) {
    return <Navigate to="/" replace />;
  }

  return children;
}

export default ProtectedRoute;
