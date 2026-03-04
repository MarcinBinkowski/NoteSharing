export class ApiError extends Error {
  public readonly status: number;
  public readonly detail: string | undefined;

  constructor(status: number, detail: string | undefined) {
    super(detail ?? `Request failed with status ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export function isApiError(err: unknown): err is ApiError {
  return err instanceof ApiError;
}

export function getStatusCode(err: unknown): number | undefined {
  if (err instanceof ApiError) return err.status;
  return (err as { response?: { status?: number } })?.response?.status;
}

export function isNotFound(err: unknown): boolean {
  return getStatusCode(err) === 404;
}

export function isExpired(err: unknown): boolean {
  return getStatusCode(err) === 410;
}

export function isUnauthorized(err: unknown): boolean {
  return getStatusCode(err) === 401;
}

export const isInvalidPassword = isUnauthorized;

export function isForbidden(err: unknown): boolean {
  return getStatusCode(err) === 403;
}
