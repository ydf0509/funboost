import type { ReactNode } from "react";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <div className="mx-auto flex min-h-screen max-w-5xl items-center justify-center px-6 py-12">
        <div className="w-full max-w-md space-y-8 rounded-[32px] border border-[hsl(var(--line))] bg-[hsl(var(--card))]/85 p-10 shadow-2xl">
          <div className="text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.45em] text-[hsl(var(--accent-2))]">
              Funboost
            </p>
            <h1 className="font-display text-2xl text-[hsl(var(--ink))]">管理控制台</h1>
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}
