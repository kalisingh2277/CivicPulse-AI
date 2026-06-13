"use client";

import Link from "next/link";

import { useAuth } from "@/lib/auth";

export function Nav() {
  const { user, logout, loading } = useAuth();
  return (
    <nav className="flex items-center justify-between border-b border-neutral-200 px-6 py-3">
      <Link href="/" className="text-lg font-semibold">
        CivicPulse AI
      </Link>
      <div className="flex items-center gap-4 text-sm">
        <Link href="/report" className="hover:underline">
          Report
        </Link>
        <Link href="/my" className="hover:underline">
          My complaints
        </Link>
        {loading ? null : user ? (
          <>
            <span className="text-neutral-500">{user.full_name}</span>
            <button onClick={logout} className="rounded-md border px-3 py-1 hover:bg-neutral-100">
              Logout
            </button>
          </>
        ) : (
          <Link href="/login" className="rounded-md border px-3 py-1 hover:bg-neutral-100">
            Login
          </Link>
        )}
      </div>
    </nav>
  );
}
