"use client";

import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";
import { navigateTo } from "@/lib/navigation";
import { PermissionProvider } from "@/contexts/PermissionContext";
import { ProjectProvider } from "@/contexts/ProjectContext";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const checkSession = async () => {
      try {
        const response = await apiFetch<{ success: boolean }>("/api/profile", { method: "GET" });
        if (!response.success) {
          navigateTo("/login");
        }
      } catch {
        navigateTo("/login");
      }
    };

    checkSession();
  }, []);

  return (
    <PermissionProvider>
      <ProjectProvider>
        <div className="min-h-screen">
          <Sidebar open={open} onClose={() => setOpen(false)} />
          <div className="min-h-screen md:pl-72">
            <TopBar onMenu={() => setOpen(true)} />
            <main className="space-y-10 px-6 py-10 fade-in">{children}</main>
          </div>
        </div>
      </ProjectProvider>
    </PermissionProvider>
  );
}
