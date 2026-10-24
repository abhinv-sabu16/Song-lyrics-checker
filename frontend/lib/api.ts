import type { SearchRequest, SearchResponse } from "./types";

// Configured in frontend/.env.local (NEXT_PUBLIC_API_URL). Restart `npm run dev`
// after changing it.
export const API_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000"
).replace(/\/+$/, "");

const REQUEST_TIMEOUT_MS = 15_000;

export type ApiErrorKind = "network" | "timeout" | "validation" | "server";

export class ApiError extends Error {
  kind: ApiErrorKind;

  constructor(kind: ApiErrorKind, message: string) {
    super(message);
    this.name = "ApiError";
    this.kind = kind;
  }
}

/**
 * POST /api/search. Pass `signal` to cancel a request that is no longer
 * wanted; a cancelled request rejects with the browser's AbortError.
 */
export async function searchLyrics(
  request: SearchRequest,
  signal?: AbortSignal,
): Promise<SearchResponse> {
  const timeout = new AbortController();
  const timer = setTimeout(() => timeout.abort(), REQUEST_TIMEOUT_MS);
  const cancel = () => timeout.abort();
  signal?.addEventListener("abort", cancel);

  let response: Response;
  try {
    response = await fetch(`${API_URL}/api/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
      signal: timeout.signal,
    });
  } catch (err) {
    if (signal?.aborted) throw err; // the caller cancelled on purpose
    if (timeout.signal.aborted) {
      throw new ApiError(
        "timeout",
        "The search took too long. Please try again.",
      );
    }
    throw new ApiError(
      "network",
      "Can't reach the search server. Make sure the backend is running, then try again.",
    );
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", cancel);
  }

  if (response.status === 422) {
    throw new ApiError(
      "validation",
      "That search isn't valid. Use 1 to 200 characters.",
    );
  }
  if (!response.ok) {
    throw new ApiError(
      "server",
      `The server ran into a problem (error ${response.status}). Please try again.`,
    );
  }

  try {
    return (await response.json()) as SearchResponse;
  } catch {
    throw new ApiError("server", "The server sent a response we couldn't read.");
  }
}