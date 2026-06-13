"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

type Complaint = {
  id: string;
  public_code: string;
  description: string;
  processing_status: string;
  ward_id: number | null;
  created_at: string;
};

export default function MyComplaintsPage() {
  const { user, loading } = useAuth();
  const [items, setItems] = useState<Complaint[] | null>(null);

  useEffect(() => {
    if (user) api.get<Complaint[]>("/complaints/mine").then(setItems).catch(() => setItems([]));
  }, [user]);

  if (loading) return <p className="p-8 text-neutral-500">Loading…</p>;
  if (!user)
    return (
      <main className="mx-auto mt-16 max-w-md px-4 text-center">
        <p className="mb-4">Please log in to see your complaints.</p>
        <Link href="/login" className="rounded-md bg-neutral-900 px-4 py-2 text-white">
          Log in
        </Link>
      </main>
    );

  return (
    <main className="mx-auto my-10 max-w-2xl px-4">
      <h1 className="mb-6 text-2xl font-semibold">My complaints</h1>
      {items === null ? (
        <p className="text-neutral-500">Loading…</p>
      ) : items.length === 0 ? (
        <p className="text-neutral-500">
          No complaints yet.{" "}
          <Link href="/report" className="underline">
            Report one
          </Link>
          .
        </p>
      ) : (
        <ul className="flex flex-col gap-3">
          {items.map((c) => (
            <li key={c.id} className="rounded-lg border border-neutral-200 p-4">
              <div className="flex items-center justify-between">
                <span className="font-mono text-sm">{c.public_code}</span>
                <span className="rounded-full bg-neutral-100 px-2 py-0.5 text-xs">
                  {c.processing_status}
                </span>
              </div>
              <p className="mt-1 text-neutral-700">{c.description}</p>
              <p className="mt-1 text-xs text-neutral-400">
                {new Date(c.created_at).toLocaleString()}
                {c.ward_id ? ` · ward #${c.ward_id}` : ""}
              </p>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
