import { Component } from "react";

export default class AppErrorBoundary extends Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    if (import.meta.env.DEV)
      console.error("CareerPilot UI error", error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <main className="error-boundary" role="alert">
        <section>
          <span>CareerPilot</span>
          <h1>Something went wrong in this section.</h1>
          <p>
            Your session and saved information are safe. Try rendering the page
            again.
          </p>
          <button
            type="button"
            className="button primary"
            onClick={() => this.setState({ error: null })}
          >
            Try again
          </button>
        </section>
      </main>
    );
  }
}
