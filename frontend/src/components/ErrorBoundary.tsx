import React from "react";
import { Button } from "@/components/ui/button";

interface Props {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("Unhandled render error:", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center space-y-4 max-w-md px-4">
            <p className="text-destructive font-semibold text-lg">
              Something went wrong.
            </p>
            {this.state.error?.message && import.meta.env.DEV && (
              <p className="text-sm text-muted-foreground font-mono">
                {this.state.error.message}
              </p>
            )}
            <Button
              variant="outline"
              onClick={() =>
                this.setState({ hasError: false, error: null })
              }
            >
              Try again
            </Button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
