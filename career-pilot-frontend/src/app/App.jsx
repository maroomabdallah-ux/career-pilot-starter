import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import AppRoutes from "./routes";
import AuthBootstrap from "../features/auth/AuthBootstrap";
import AppErrorBoundary from "../components/common/AppErrorBoundary";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000, refetchOnWindowFocus: false },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppErrorBoundary>
          <AuthBootstrap>
            <AppRoutes />
          </AuthBootstrap>
        </AppErrorBoundary>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
