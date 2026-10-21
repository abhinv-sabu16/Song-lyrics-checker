"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export default function Home() {
  const [status, setStatus] = useState<"checking" | "ok" | "error">("checking");

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((res) => (res.ok ? setStatus("ok") : setStatus("error")))
      .catch(() => setStatus("error"));
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-8">
      <h1 className="text-3xl font-bold">Song Lyric Checker</h1>
      <p>
        Backend status:{" "}
        <span className={status === "ok" ? "text-green-600" : "text-red-600"}>
          {status === "checking" ? "checking..." : status === "ok" ? "Connected" : "Unreachable"}
        </span>
      </p>
    </main>
  );
}