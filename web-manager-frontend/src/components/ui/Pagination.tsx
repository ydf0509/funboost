import clsx from "clsx";
import { ChevronFirst, ChevronLast, ChevronLeft, ChevronRight } from "lucide-react";
import { useState, useCallback } from "react";

export interface PaginationProps {
  currentPage: number;           // 当前页码 (0-based)
  pageSize: number;              // 每页数量
  totalCount: number;            // 总记录数
  pageSizeOptions?: number[];    // 每页数量选项
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  loading?: boolean;
}

const defaultPageSizeOptions = [20, 50, 100, 200];

export function Pagination({
  currentPage,
  pageSize,
  totalCount,
  pageSizeOptions = defaultPageSizeOptions,
  onPageChange,
  onPageSizeChange,
  loading = false,
}: PaginationProps) {
  // 计算分页状态
  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
  // 确保 currentPage 在有效范围内
  const validCurrentPage = Math.max(0, Math.min(currentPage, totalPages - 1));
  const startRecord = totalCount === 0 ? 0 : validCurrentPage * pageSize + 1;
  const endRecord = Math.min((validCurrentPage + 1) * pageSize, totalCount);
  const canGoPrevious = validCurrentPage > 0;
  const canGoNext = validCurrentPage < totalPages - 1;

  const handleFirst = () => {
    if (canGoPrevious && !loading) {
      onPageChange(0);
    }
  };

  const handlePrevious = () => {
    if (canGoPrevious && !loading) {
      onPageChange(validCurrentPage - 1);
    }
  };

  const handleNext = () => {
    if (canGoNext && !loading) {
      onPageChange(validCurrentPage + 1);
    }
  };

  const handleLast = () => {
    if (canGoNext && !loading) {
      onPageChange(totalPages - 1);
    }
  };

  const handlePageSizeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newSize = parseInt(e.target.value, 10);
    onPageSizeChange(newSize);
  };

  // 页码跳转状态
  const [jumpPage, setJumpPage] = useState("");

  const handleJumpPageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // 只允许输入数字
    const value = e.target.value.replace(/[^0-9]/g, "");
    setJumpPage(value);
  };

  const handleJumpPageSubmit = useCallback(() => {
    if (!jumpPage || loading) return;
    const pageNum = parseInt(jumpPage, 10);
    if (isNaN(pageNum) || pageNum < 1 || pageNum > totalPages) {
      setJumpPage("");
      return;
    }
    onPageChange(pageNum - 1); // 转换为 0-based
    setJumpPage("");
  }, [jumpPage, loading, totalPages, onPageChange]);

  const handleJumpPageKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleJumpPageSubmit();
    }
  };

  return (
    <div className="flex flex-wrap items-center justify-between gap-4 py-4">
      {/* 左侧：记录范围显示 */}
      <div className="text-sm text-[hsl(var(--ink-muted))]">
        {totalCount === 0 ? (
          <span>共 0 条记录</span>
        ) : (
          <span>
            显示 {startRecord}-{endRecord} 条，共 {totalCount.toLocaleString()} 条
          </span>
        )}
      </div>

      {/* 右侧：分页控制 */}
      <div className="flex items-center gap-4">
        {/* 每页数量选择器 */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-[hsl(var(--ink-muted))]">每页</span>
          <select
            value={pageSize}
            onChange={handlePageSizeChange}
            disabled={loading}
            className="rounded-lg border border-[hsl(var(--line))] bg-[hsl(var(--card))]/80 px-2 py-1 text-sm text-[hsl(var(--ink))] outline-none transition focus:border-[hsl(var(--accent))] disabled:opacity-50"
          >
            {pageSizeOptions.map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
          <span className="text-xs text-[hsl(var(--ink-muted))]">条</span>
        </div>

        {/* 页码显示 */}
        <div className="text-sm text-[hsl(var(--ink-muted))]">
          第 {validCurrentPage + 1} / {totalPages} 页
        </div>

        {/* 导航按钮 */}
        <div className="flex items-center gap-1">
          <NavButton
            onClick={handleFirst}
            disabled={!canGoPrevious || loading}
            title="首页"
          >
            <ChevronFirst className="h-4 w-4" />
          </NavButton>
          <NavButton
            onClick={handlePrevious}
            disabled={!canGoPrevious || loading}
            title="上一页"
          >
            <ChevronLeft className="h-4 w-4" />
          </NavButton>
          <NavButton
            onClick={handleNext}
            disabled={!canGoNext || loading}
            title="下一页"
          >
            <ChevronRight className="h-4 w-4" />
          </NavButton>
          <NavButton
            onClick={handleLast}
            disabled={!canGoNext || loading}
            title="末页"
          >
            <ChevronLast className="h-4 w-4" />
          </NavButton>
        </div>

        {/* 页码跳转 */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-[hsl(var(--ink-muted))]">跳至</span>
          <input
            type="text"
            value={jumpPage}
            onChange={handleJumpPageChange}
            onKeyDown={handleJumpPageKeyDown}
            onBlur={handleJumpPageSubmit}
            disabled={loading || totalPages <= 1}
            placeholder={String(validCurrentPage + 1)}
            className="w-14 rounded-lg border border-[hsl(var(--line))] bg-[hsl(var(--card))]/80 px-2 py-1 text-center text-sm text-[hsl(var(--ink))] outline-none transition focus:border-[hsl(var(--accent))] disabled:opacity-50"
          />
          <span className="text-xs text-[hsl(var(--ink-muted))]">页</span>
        </div>
      </div>
    </div>
  );
}

interface NavButtonProps {
  onClick: () => void;
  disabled: boolean;
  title: string;
  children: React.ReactNode;
}

function NavButton({ onClick, disabled, title, children }: NavButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={title}
      className={clsx(
        "inline-flex h-8 w-8 items-center justify-center rounded-lg border transition-colors",
        disabled
          ? "cursor-not-allowed border-[hsl(var(--line))] bg-[hsl(var(--sand-2))] text-[hsl(var(--ink-muted))]/50"
          : "border-[hsl(var(--line))] bg-[hsl(var(--card))] text-[hsl(var(--ink-muted))] hover:border-[hsl(var(--accent))] hover:text-[hsl(var(--accent))]"
      )}
    >
      {children}
    </button>
  );
}

// 导出计算函数供测试使用
export function calculatePaginationState(
  currentPage: number,
  pageSize: number,
  totalCount: number
) {
  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
  // 确保 currentPage 在有效范围内
  const validCurrentPage = Math.max(0, Math.min(currentPage, totalPages - 1));
  const startRecord = totalCount === 0 ? 0 : validCurrentPage * pageSize + 1;
  const endRecord = Math.min((validCurrentPage + 1) * pageSize, totalCount);
  const canGoPrevious = validCurrentPage > 0;
  const canGoNext = validCurrentPage < totalPages - 1;

  return {
    totalPages,
    startRecord,
    endRecord,
    canGoPrevious,
    canGoNext,
  };
}
