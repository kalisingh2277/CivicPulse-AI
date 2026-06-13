import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto mt-20 max-w-2xl px-4 text-center">
      <h1 className="text-4xl font-semibold">CivicPulse AI</h1>
      <p className="mt-4 text-lg text-neutral-600">
        Report a civic problem in seconds. We deduplicate, prioritize, and route it to the
        right department — and you can track it to resolution.
      </p>
      <div className="mt-8 flex justify-center gap-4">
        <Link href="/report" className="rounded-md bg-neutral-900 px-5 py-2.5 text-white">
          Report a problem
        </Link>
        <Link
          href="/my"
          className="rounded-md border border-neutral-300 px-5 py-2.5 hover:bg-neutral-100"
        >
          Track my complaints
        </Link>
      </div>
      <p className="mt-10 text-sm text-neutral-400">Pilot city: Bengaluru</p>
    </main>
  );
}
