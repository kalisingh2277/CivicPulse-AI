"use client";

import Link from "next/link";
import { useState } from "react";

import { LocationPicker, type LngLat } from "@/components/LocationPicker";
import { ApiError, api, uploadToStorage } from "@/lib/api";
import { useAuth } from "@/lib/auth";

type ComplaintOut = { id: string; public_code: string; ward_id: number | null };
type Presign = { upload_url: string; object_key: string };

export default function ReportPage() {
  const { user, loading } = useAuth();
  const [description, setDescription] = useState("");
  const [address, setAddress] = useState("");
  const [location, setLocation] = useState<LngLat | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ComplaintOut | null>(null);

  if (loading) return <p className="p-8 text-neutral-500">Loading…</p>;
  if (!user)
    return (
      <main className="mx-auto mt-16 max-w-md px-4 text-center">
        <p className="mb-4">Please log in to report a problem.</p>
        <Link href="/login" className="rounded-md bg-neutral-900 px-4 py-2 text-white">
          Log in
        </Link>
      </main>
    );

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!location) {
      setError("Drop a pin on the map first.");
      return;
    }
    setBusy(true);
    try {
      const complaint = await api.post<ComplaintOut>("/complaints", {
        description,
        address_text: address || null,
        location: { type: "Point", coordinates: [location.lng, location.lat] },
      });

      if (file) {
        const ps = await api.post<Presign>(`/complaints/${complaint.id}/media/presign`, {
          mime: file.type,
          bytes: file.size,
        });
        await uploadToStorage(ps.upload_url, file);
        await api.post(`/complaints/${complaint.id}/media/confirm`, {
          object_key: ps.object_key,
          mime: file.type,
        });
      }
      setResult(complaint);
      setDescription("");
      setAddress("");
      setLocation(null);
      setFile(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  if (result)
    return (
      <main className="mx-auto mt-16 max-w-md px-4 text-center">
        <h1 className="mb-2 text-2xl font-semibold">Reported ✓</h1>
        <p className="text-neutral-600">
          Your reference is <span className="font-mono">{result.public_code}</span>.
          {result.ward_id
            ? " We've located it in your ward and our AI will categorize it shortly."
            : " (This location is outside the pilot city.)"}
        </p>
        <div className="mt-6 flex justify-center gap-3">
          <button
            onClick={() => setResult(null)}
            className="rounded-md border px-4 py-2 hover:bg-neutral-100"
          >
            Report another
          </button>
          <Link href="/my" className="rounded-md bg-neutral-900 px-4 py-2 text-white">
            Track my complaints
          </Link>
        </div>
      </main>
    );

  return (
    <main className="mx-auto my-10 max-w-2xl px-4">
      <h1 className="mb-6 text-2xl font-semibold">Report a problem</h1>
      <form onSubmit={onSubmit} className="flex flex-col gap-5">
        <div>
          <label className="mb-1 block text-sm font-medium">
            What&apos;s the problem? (any language)
          </label>
          <textarea
            required
            minLength={5}
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g. Bada gaddha hai bus stop ke paas"
            className="w-full rounded-md border border-neutral-300 px-3 py-2"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">Where is it?</label>
          <LocationPicker value={location} onChange={setLocation} />
        </div>

        <input
          type="text"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder="Nearby landmark (optional)"
          className="rounded-md border border-neutral-300 px-3 py-2"
        />

        <div>
          <label className="mb-1 block text-sm font-medium">Photo (optional)</label>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="text-sm"
          />
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={busy}
          className="rounded-md bg-neutral-900 px-4 py-2 text-white disabled:opacity-50"
        >
          {busy ? "Submitting…" : "Submit report"}
        </button>
      </form>
    </main>
  );
}
