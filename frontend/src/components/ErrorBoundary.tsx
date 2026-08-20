import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

// Class component because React's error boundary API (getDerivedStateFromError/
// componentDidCatch) has no hook equivalent — any unhandled render exception
// below this point would otherwise white-screen the whole SPA with no way
// to recover without a manual page reload.
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Unhandled render error", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="error-boundary">
          <h1>Algo salió mal</h1>
          <p>Ocurrió un error inesperado y esta parte de la aplicación no puede continuar.</p>
          <button type="button" onClick={() => window.location.reload()}>
            Recargar página
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
