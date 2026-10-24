"use client";

import { useEffect, useRef, useState } from "react";

import { ApiError, searchLyrics } from "@/lib/api";
import type { SearchResponse } from "@/lib/types";
import MatchResults from "./MatchResults";

type SearchState =
  | { status: "idle" }
  | { status: "loading"; query: string }
  | { status: "success"; data: SearchResponse }
  | { status: "error"; query: string; message: string };

export default function LyricSearch() {
  const [input, setInput] = useState("");
  const [state, setState] = useState<SearchState>({ status: "idle" });
  const abortRef = useRef<AbortController | null>(null);

  // Cancel any in-flight request when the component unmounts.
  useEffect(() => () => abortRef.current?.abort(), []);

  async function runSearch(rawQuery: string) {
    const query = rawQuery.trim();
    if (!query) return;

    // A newer search replaces an older one, so stale results never show up.
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setState({ status: "loading", query });
    try {
      const data = await searchLyrics({ query, limit: 10 }, controller.signal);
      if (controller.signal.aborted) return;
      setState({ status: "success", data });
    } catch (err) {
      if (controller.signal.aborted) return;
      const message =
        err instanceof ApiError
          ? err.message
          : "Something went wrong. Please try again.";
      setState({ status: "error", query, message });
    }
  }

  const isLoading = state.status === "loading";

  return (
    <div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void runSearch(input);
        }}
        className="flex flex-col gap-3 sm:flex-row"
        role="search"
      >
        <label htmlFor="lyric-query" className="sr-only">
          Lyric phrase
        </label>
        <input
          id="lyric-query"
          type="search"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          maxLength={200}
          placeholder="Type a lyric, even if you're unsure of the words"
          autoComplete="off"
          autoFocus
          className="min-w-0 flex-1 rounded-lg border border-neutral-300 bg-white px-4 py-3 text-base text-neutral-900 placeholder:text-neutral-500 focus:border-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-600/30 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100 dark:placeholder:text-neutral-400"
        />
        <button
          type="submit"
          disabled={!input.trim()}
          className="rounded-lg bg-indigo-600 px-6 py-3 font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-600/40 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isLoading ? "Searching…" : "Search"}
        </button>
      </form>

      <div className="mt-6" aria-live="polite" aria-busy={isLoading}>
        {state.status === "idle" && (
          <p className="text-center text-sm text-neutral-600 dark:text-neutral-400">
            Search for a phrase to find matching songs in your local library.
          </p>
        )}

        {state.status === "loading" && (
          <div
            role="status"
            className="flex items-center justify-center gap-3 py-8 text-neutral-600 dark:text-neutral-400"
          >
            <span
              aria-hidden="true"
              className="h-5 w-5 animate-spin rounded-full border-2 border-neutral-300 border-t-indigo-600 dark:border-neutral-700 dark:border-t-indigo-400"
            />
            <span>Searching for “{state.query}”…</span>
          </div>
        )}

        {state.status === "error" && (
          <div
            role="alert"
            className="rounded-xl border border-red-300 bg-red-50 p-4 text-red-900 dark:border-red-900 dark:bg-red-950 dark:text-red-100"
          >
            <p className="font-medium">Search failed</p>
            <p className="mt-1 text-sm">{state.message}</p>
            <button
              type="button"
              onClick={() => void runSearch(state.query)}
              className="mt-3 rounded-md border border-red-400 px-3 py-1.5 text-sm font-medium hover:bg-red-100 dark:border-red-800 dark:hover:bg-red-900"
            >
              Try again
            </button>
          </div>
        )}

        {state.status === "success" && <MatchResults data={state.data} />}
      </div>
    </div>
  );
}