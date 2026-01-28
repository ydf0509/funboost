"use client";

import { Suspense } from "react";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { navigateTo } from "@/lib/navigation";

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";
  const [message, setMessage] = useState("正在验证邮箱...");

  useEffect(() => {
    if (!token) {
      setMessage("无效的验证链接。");
      return;
    }

    const verify = async () => {
      try {
        await fetch(`${process.env.NEXT_PUBLIC_API_BASE ?? ""}/profile/verify-email/${token}`, {
          credentials: "include",
        });
        setMessage("邮箱验证成功，正在返回个人中心...");
        setTimeout(() => navigateTo("/profile"), 1200);
      } catch (err) {
        setMessage(err instanceof Error ? err.message : "验证失败。");
      }
    };

    verify();
  }, [token]);

  return (
    <div className="space-y-8">
      <SectionHeader title="验证邮箱" subtitle="正在完成验证。" />
      <Card>
        <p className="text-sm text-[hsl(var(--ink-muted))]">{message}</p>
        <Button variant="outline" className="mt-4" onClick={() => navigateTo("/profile")}>
          返回个人中心
        </Button>
      </Card>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <div className="space-y-8">
        <SectionHeader title="验证邮箱" subtitle="正在加载..." />
        <Card>
          <p className="text-sm text-[hsl(var(--ink-muted))]">正在验证邮箱...</p>
        </Card>
      </div>
    }>
      <VerifyEmailContent />
    </Suspense>
  );
}
