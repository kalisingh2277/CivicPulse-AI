"use client";

import { useEffect, useState } from "react";

type Health = {
  status: string;
  db: boolean;
  redis: boolean;
  extensions: string[];
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/v1/health`)
      .then((r) => r.json())
      .then(setHealth)
      .catch((e: unknown) => setError(String(e)));
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-3xl font-semibold">CivicPulse AI</h1>
      <p className="text-neutral-500">Day 1 — stack health</p>
      {error && (
        <p className="rounded-md bg-red-50 px-4 py-2 text-sm text-red-700">
          API unreachable — is uvicorn running on :8000? ({error})
        </p>
      )}
      {health && (
        <div className="flex flex-wrap justify-center gap-3">
          <Chip ok={health.db} label="PostgreSQL" />
          <Chip ok={health.redis} label="Redis" />
          <Chip ok={health.extensions.includes("postgis")} label="PostGIS" />
          <Chip ok={health.extensions.includes("vector")} label="pgvector" />
          <Chip ok={health.extensions.includes("citext")} label="citext" />
        </div>
      )}
    </main>
  );
}

function Chip({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      className={`rounded-full px-4 py-1.5 text-sm font-medium ${
        ok ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
      }`}
    >
      {label} {ok ? "✓" : "✗"}
    </span>
  );
}
