/**
 * 属性测试：Pagination 组件
 *
 * 使用 fast-check 进行属性测试，验证分页组件的正确性属性。
 *
 * **Feature: fun-results-pagination**
 * 
 * @vitest-environment node
 */

import { describe, it, expect } from "vitest";
import * as fc from "fast-check";
import { calculatePaginationState } from "./Pagination";

/**
 * **Property 1: Navigation Button Disabled States**
 *
 * *For any* pagination state with currentPage and totalPages, the first/previous buttons
 * SHALL be disabled if and only if currentPage === 0, and the next/last buttons SHALL
 * be disabled if and only if currentPage >= totalPages - 1.
 *
 * **Validates: Requirements 1.4, 3.5, 3.6**
 */
describe("Property 1: Navigation Button Disabled States", () => {
  it("first/previous buttons disabled when currentPage === 0", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 500 }), // pageSize
        fc.integer({ min: 0, max: 10000 }), // totalCount
        (pageSize, totalCount) => {
          const currentPage = 0;
          const state = calculatePaginationState(currentPage, pageSize, totalCount);

          // 在第一页时，canGoPrevious 应该为 false
          expect(state.canGoPrevious).toBe(false);
        }
      ),
      { numRuns: 100 }
    );
  });

  it("first/previous buttons enabled when currentPage > 0", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 100 }), // currentPage (> 0)
        fc.integer({ min: 1, max: 500 }), // pageSize
        fc.integer({ min: 1, max: 10000 }), // totalCount
        (currentPage, pageSize, totalCount) => {
          // 确保 currentPage 在有效范围内
          const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
          if (currentPage >= totalPages) return; // 跳过无效情况

          const state = calculatePaginationState(currentPage, pageSize, totalCount);

          // 不在第一页时，canGoPrevious 应该为 true
          expect(state.canGoPrevious).toBe(true);
        }
      ),
      { numRuns: 100 }
    );
  });

  it("next/last buttons disabled when on last page", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 500 }), // pageSize
        fc.integer({ min: 1, max: 10000 }), // totalCount
        (pageSize, totalCount) => {
          const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
          const currentPage = totalPages - 1; // 最后一页

          const state = calculatePaginationState(currentPage, pageSize, totalCount);

          // 在最后一页时，canGoNext 应该为 false
          expect(state.canGoNext).toBe(false);
        }
      ),
      { numRuns: 100 }
    );
  });

  it("next/last buttons enabled when not on last page", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 500 }), // pageSize
        fc.integer({ min: 2, max: 10000 }), // totalCount (至少2条才能有多页)
        (pageSize, totalCount) => {
          const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
          if (totalPages <= 1) return; // 跳过只有一页的情况

          const currentPage = 0; // 第一页

          const state = calculatePaginationState(currentPage, pageSize, totalCount);

          // 不在最后一页时，canGoNext 应该为 true
          expect(state.canGoNext).toBe(true);
        }
      ),
      { numRuns: 100 }
    );
  });

  it("all navigation disabled when only one page", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 500 }), // pageSize
        (pageSize) => {
          // totalCount <= pageSize 意味着只有一页
          const totalCount = pageSize;
          const currentPage = 0;

          const state = calculatePaginationState(currentPage, pageSize, totalCount);

          // 只有一页时，所有导航都应该禁用
          expect(state.canGoPrevious).toBe(false);
          expect(state.canGoNext).toBe(false);
        }
      ),
      { numRuns: 100 }
    );
  });
});

/**
 * **Property 4: Record Range Display**
 *
 * *For any* pagination state with currentPage, pageSize, and totalCount, the displayed
 * range SHALL be from (currentPage * pageSize + 1) to min((currentPage + 1) * pageSize, totalCount),
 * with special handling for totalCount === 0.
 *
 * **Validates: Requirements 4.1, 4.2, 4.3**
 */
describe("Property 4: Record Range Display", () => {
  it("startRecord is correctly calculated", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 100 }), // currentPage
        fc.integer({ min: 1, max: 500 }), // pageSize
        fc.integer({ min: 1, max: 10000 }), // totalCount (> 0)
        (currentPage, pageSize, totalCount) => {
          // 确保 currentPage 在有效范围内
          const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
          if (currentPage >= totalPages) return;

          const state = calculatePaginationState(currentPage, pageSize, totalCount);

          // startRecord 应该是 currentPage * pageSize + 1
          const expectedStart = currentPage * pageSize + 1;
          expect(state.startRecord).toBe(expectedStart);
        }
      ),
      { numRuns: 100 }
    );
  });

  it("endRecord is correctly calculated", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 100 }), // currentPage
        fc.integer({ min: 1, max: 500 }), // pageSize
        fc.integer({ min: 1, max: 10000 }), // totalCount
        (currentPage, pageSize, totalCount) => {
          // 确保 currentPage 在有效范围内
          const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
          if (currentPage >= totalPages) return;

          const state = calculatePaginationState(currentPage, pageSize, totalCount);

          // endRecord 应该是 min((currentPage + 1) * pageSize, totalCount)
          const expectedEnd = Math.min((currentPage + 1) * pageSize, totalCount);
          expect(state.endRecord).toBe(expectedEnd);
        }
      ),
      { numRuns: 100 }
    );
  });

  it("startRecord is 0 when totalCount is 0", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 100 }), // currentPage
        fc.integer({ min: 1, max: 500 }), // pageSize
        (currentPage, pageSize) => {
          const totalCount = 0;

          const state = calculatePaginationState(currentPage, pageSize, totalCount);

          // totalCount 为 0 时，startRecord 应该是 0
          expect(state.startRecord).toBe(0);
        }
      ),
      { numRuns: 100 }
    );
  });

  it("endRecord is 0 when totalCount is 0", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 100 }), // currentPage
        fc.integer({ min: 1, max: 500 }), // pageSize
        (currentPage, pageSize) => {
          const totalCount = 0;

          const state = calculatePaginationState(currentPage, pageSize, totalCount);

          // totalCount 为 0 时，endRecord 应该是 0
          expect(state.endRecord).toBe(0);
        }
      ),
      { numRuns: 100 }
    );
  });

  it("startRecord <= endRecord always", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 100 }), // currentPage
        fc.integer({ min: 1, max: 500 }), // pageSize
        fc.integer({ min: 0, max: 10000 }), // totalCount
        (currentPage, pageSize, totalCount) => {
          const state = calculatePaginationState(currentPage, pageSize, totalCount);

          // startRecord 应该总是 <= endRecord
          expect(state.startRecord).toBeLessThanOrEqual(state.endRecord);
        }
      ),
      { numRuns: 100 }
    );
  });

  it("endRecord <= totalCount always", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 100 }), // currentPage
        fc.integer({ min: 1, max: 500 }), // pageSize
        fc.integer({ min: 0, max: 10000 }), // totalCount
        (currentPage, pageSize, totalCount) => {
          const state = calculatePaginationState(currentPage, pageSize, totalCount);

          // endRecord 应该总是 <= totalCount
          expect(state.endRecord).toBeLessThanOrEqual(totalCount);
        }
      ),
      { numRuns: 100 }
    );
  });
});

/**
 * 额外测试：totalPages 计算正确性
 */
describe("totalPages calculation", () => {
  it("totalPages is at least 1", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 100 }), // currentPage
        fc.integer({ min: 1, max: 500 }), // pageSize
        fc.integer({ min: 0, max: 10000 }), // totalCount
        (currentPage, pageSize, totalCount) => {
          const state = calculatePaginationState(currentPage, pageSize, totalCount);

          // totalPages 应该至少为 1
          expect(state.totalPages).toBeGreaterThanOrEqual(1);
        }
      ),
      { numRuns: 100 }
    );
  });

  it("totalPages is correctly calculated", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 100 }), // currentPage
        fc.integer({ min: 1, max: 500 }), // pageSize
        fc.integer({ min: 0, max: 10000 }), // totalCount
        (currentPage, pageSize, totalCount) => {
          const state = calculatePaginationState(currentPage, pageSize, totalCount);

          // totalPages 应该是 Math.max(1, Math.ceil(totalCount / pageSize))
          const expectedTotalPages = Math.max(1, Math.ceil(totalCount / pageSize));
          expect(state.totalPages).toBe(expectedTotalPages);
        }
      ),
      { numRuns: 100 }
    );
  });
});
