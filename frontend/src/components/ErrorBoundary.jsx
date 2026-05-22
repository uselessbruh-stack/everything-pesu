import { Component } from 'react';
import { AlertTriangle } from 'lucide-react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
          <AlertTriangle className="w-8 h-8 text-bad" />
          <p className="text-sm font-medium text-ink">Something went wrong</p>
          <p className="text-xs text-ink-muted max-w-sm">
            {this.state.error?.message || 'An unexpected error occurred.'}
          </p>
          <button
            className="btn-ghost text-xs mt-2"
            onClick={() => this.setState({ hasError: false, error: null })}
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
