import type { MatchResult, SearchResponse } from "@/lib/types";

const MATCH_LABELS: Record<MatchResult["match_type"], string> = {
  exact: "Exact match",
  fuzzy: "Close match",
};

function SimilarityMeter({ score }: { score: number }) {
  const pct = Math.max(0, Math.min(100, Math.round(score)));
  return (
    <div className="mt-3">
      <div className="flex items-center justify-between text-xs text-neutral-600 dark:text-neutral-400">
        <span>Text similarity</span>
        <span>{pct}%</span>
      </div>
      <div
        role="meter"
        aria-label="Text similarity"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={pct}
        className="mt-1 h-2 w-full overflow-hidden rounded-full bg-neutral-200 dark:bg-neutral-800"
      >
        <div
          className="h-full rounded-full bg-indigo-600 dark:bg-indigo-400"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function MatchResults({ data }: { data: SearchResponse }) {
  if (data.results.length === 0) {
    return (
      <section
        aria-label="No results"
        className="rounded-xl border border-dashed border-neutral-300 p-6 text-center dark:border-neutral-700"
      >
        <h2 className="text-lg font-semibold">No matches found</h2>
        <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">
          Nothing in the local lyrics database is close to “{data.query}”.
        </p>
        <ul className="mx-auto mt-4 max-w-sm list-disc space-y-1 pl-5 text-left text-sm text-neutral-600 dark:text-neutral-400">
          <li>Check the spelling, or try fewer words.</li>
          <li>Only songs stored in your local database can be found.</li>
        </ul>
      </section>
    );
  }

  const count = data.results.length;
  return (
    <section aria-label="Search results">
      <h2 className="mb-3 text-sm text-neutral-600 dark:text-neutral-400">
        {count} {count === 1 ? "result" : "results"} for “{data.query}”
      </h2>
      <ul className="space-y-3">
        {data.results.map((r, i) => (
          <li
            key={`${r.song_id}-${i}`}
            className="rounded-xl border border-neutral-200 bg-white p-4 shadow-sm dark:border-neutral-800 dark:bg-neutral-900"
          >
            <div className="flex flex-wrap items-start justify-between gap-x-3 gap-y-1">
              <div className="min-w-0">
                <h3 className="break-words font-semibold">{r.title}</h3>
                <p className="break-words text-sm text-neutral-600 dark:text-neutral-400">
                  {r.artist}
                </p>
              </div>
              <span className="shrink-0 rounded-full bg-neutral-100 px-2.5 py-0.5 text-xs font-medium text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300">
                {MATCH_LABELS[r.match_type]}
              </span>
            </div>
            <blockquote className="mt-3 break-words border-l-2 border-neutral-300 pl-3 text-sm italic dark:border-neutral-700">
              {r.matched_excerpt}
            </blockquote>
            <SimilarityMeter score={r.similarity_score} />
          </li>
        ))}
      </ul>
      <p className="mt-4 text-xs text-neutral-500 dark:text-neutral-500">
        Text similarity shows how closely your words match a lyric line. It is
        not the probability that the song is correct.
      </p>
    </section>
  );
}