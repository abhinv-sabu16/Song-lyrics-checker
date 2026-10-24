import LyricSearch from "@/components/LyricSearch";

export default function Home() {
  return (
    <main className="mx-auto w-full max-w-2xl px-4 py-10 sm:py-16">
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
          Song Lyric Checker
        </h1>
        <p className="mt-2 text-neutral-600 dark:text-neutral-400">
          Search song lyrics from a few words. Runs entirely on your computer.
        </p>
      </header>
      <LyricSearch />
    </main>
  );
}