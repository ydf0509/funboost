"use client";

import { Button } from "@/components/ui/Button";

type TimingJobsPaginationProps = {
  page: number;
  totalPages: number;
  onChange: (page: number) => void;
};

export function TimingJobsPagination({ page, totalPages, onChange }: TimingJobsPaginationProps) {
  if (totalPages <= 1) return null;

  const goTo = (nextPage: number) => {
    const safePage = Math.min(Math.max(nextPage, 1), totalPages);
    onChange(safePage);
  };

  return (
    <div className="flex flex-wrap items-center justify-end gap-2 px-4 py-3 text-xs text-[hsl(var(--ink-muted))]">
      <Button variant="outline" size="sm" onClick={() => goTo(1)} disabled={page === 1}>
        首页
      </Button>
      <Button variant="outline" size="sm" onClick={() => goTo(page - 1)} disabled={page === 1}>
        上一页
      </Button>
      <span className="rounded-full border border-[hsl(var(--line))] px-3 py-1 text-[hsl(var(--ink))]">
        {page} / {totalPages}
      </span>
      <Button variant="outline" size="sm" onClick={() => goTo(page + 1)} disabled={page === totalPages}>
        下一页
      </Button>
      <Button variant="outline" size="sm" onClick={() => goTo(totalPages)} disabled={page === totalPages}>
        末页
      </Button>
    </div>
  );
}
