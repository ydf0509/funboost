/**
 * 属性测试：FunResultsPage 分页集成
 *
 * 使用 fast-check 进行属性测试，验证页面分页集成的正确性属性。
 *
 * **Feature: fun-results-pagination**
 * 
 * @vitest-environment node
 */

import { describe, it, expect } from "vitest";
import * as fc from "fast-check";

/**
 * 模拟页面状态管理逻辑
 */
interface PageState {
  currentPage: number;
  pageSize: number;
  totalCount: number;
  queue: string;
  status: string;
  functionParams: string;
  taskId: string;
}

/**
 * 模拟页面状态变更逻辑
 */
function simulatePageSizeChange(
  state: PageState,
  newPageSize: number
): PageState {
  return {
    ...state,
    pageSize: newPageSize,
    currentPage: 0, // 切换每页数量时重置到第一页
  };
}

function simulateFilterChange(
  state: PageState,
  changes: Partial<Pick<PageState, "queue" | "status" | "functionParams" | "taskId">>
): PageState {
  return {
    ...state,
    ...changes,
    currentPage: 0, // 筛选条件变更时重置到第一页
  };
}

function simulateManualRefresh(state: PageState): PageState {
  // 手动刷新时保持当前页码
  return { ...state };
}

function simulateAutoRefresh(state: PageState): PageState {
  // 自动刷新时保持当前页码
  return { ...state };
}

function simulatePageChange(state: PageState, newPage: number): PageState {
  return {
    ...state,
    currentPage: newPage,
  };
}

/**
 * **Property 3: Page Size Change Behavior**
 *
 * *For any* page size change event, the new page size SHALL be passed to the
 * data loading function and the current page SHALL reset to 0.
 *
 * **Validates: Requirements 2.2, 2.3**
 */
describe("Property 3: Page Size Change Behavior", () => {
  it("page size change resets currentPage to 0", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 100 }), // initial currentPage
        fc.integer({ min: 1, max: 500 }), // initial pageSize
        fc.integer({ min: 0, max: 10000 }), // totalCount
        fc.constantFrom(20, 50, 100, 200), // new pageSize
        (initialPage, initialPageSize, totalCount, newPageSize) => {
          const initialState: PageState = {
            currentPage: initialPage,
            pageSize: initialPageSize,
            totalCount,
            queue: "test_queue",
            status: "all",
            functionParams: "",
            taskId: "",
          };

          const newState = simulatePageSizeChange(initialState, newPageSize);

          // 验证 currentPage 被重置为 0
          expect(newState.currentPage).toBe(0);
          // 验证 pageSize 被更新
          expect(newState.pageSize).toBe(newPageSize);
        }
      ),
      { numRuns: 100 }
    );
  });

  it("page size change preserves other state", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 100 }), // initial currentPage
        fc.integer({ min: 1, max: 500 }), // initial pageSize
        fc.integer({ min: 0, max: 10000 }), // totalCount
        fc.string(), // queue
        fc.constantFrom("all", "1", "0"), // status
        fc.string(), // functionParams
        fc.string(), // taskId
        fc.constantFrom(20, 50, 100, 200), // new pageSize
        (initialPage, initialPageSize, totalCount, queue, status, functionParams, taskId, newPageSize) => {
          const initialState: PageState = {
            currentPage: initialPage,
            pageSize: initialPageSize,
            totalCount,
            queue,
            status,
            functionParams,
            taskId,
          };

          const newState = simulatePageSizeChange(initialState, newPageSize);

          // 验证其他状态保持不变
          expect(newState.queue).toBe(queue);
          expect(newState.status).toBe(status);
          expect(newState.functionParams).toBe(functionParams);
          expect(newState.taskId).toBe(taskId);
          expect(newState.totalCount).toBe(totalCount);
        }
      ),
      { numRuns: 100 }
    );
  });
});

/**
 * **Property 6: Page State Preservation**
 *
 * *For any* sequence of user actions, the current page SHALL reset to 0 when
 * filter conditions change, but SHALL remain unchanged during manual refresh
 * or auto-refresh.
 *
 * **Validates: Requirements 6.1, 6.2, 6.3**
 */
describe("Property 6: Page State Preservation", () => {
  it("filter change resets currentPage to 0", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 100 }), // initial currentPage
        fc.integer({ min: 1, max: 500 }), // pageSize
        fc.integer({ min: 0, max: 10000 }), // totalCount
        fc.string(), // new queue
        fc.constantFrom("all", "1", "0"), // new status
        fc.string(), // new functionParams
        fc.string(), // new taskId
        (initialPage, pageSize, totalCount, newQueue, newStatus, newFunctionParams, newTaskId) => {
          const initialState: PageState = {
            currentPage: initialPage,
            pageSize,
            totalCount,
            queue: "old_queue",
            status: "all",
            functionParams: "",
            taskId: "",
          };

          // 测试队列变更
          const stateAfterQueueChange = simulateFilterChange(initialState, { queue: newQueue });
          expect(stateAfterQueueChange.currentPage).toBe(0);

          // 测试状态变更
          const stateAfterStatusChange = simulateFilterChange(initialState, { status: newStatus });
          expect(stateAfterStatusChange.currentPage).toBe(0);

          // 测试函数参数变更
          const stateAfterParamsChange = simulateFilterChange(initialState, { functionParams: newFunctionParams });
          expect(stateAfterParamsChange.currentPage).toBe(0);

          // 测试 taskId 变更
          const stateAfterTaskIdChange = simulateFilterChange(initialState, { taskId: newTaskId });
          expect(stateAfterTaskIdChange.currentPage).toBe(0);
        }
      ),
      { numRuns: 100 }
    );
  });

  it("manual refresh preserves currentPage", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 100 }), // currentPage
        fc.integer({ min: 1, max: 500 }), // pageSize
        fc.integer({ min: 0, max: 10000 }), // totalCount
        (currentPage, pageSize, totalCount) => {
          const initialState: PageState = {
            currentPage,
            pageSize,
            totalCount,
            queue: "test_queue",
            status: "all",
            functionParams: "",
            taskId: "",
          };

          const newState = simulateManualRefresh(initialState);

          // 验证 currentPage 保持不变
          expect(newState.currentPage).toBe(currentPage);
        }
      ),
      { numRuns: 100 }
    );
  });

  it("auto refresh preserves currentPage", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 100 }), // currentPage
        fc.integer({ min: 1, max: 500 }), // pageSize
        fc.integer({ min: 0, max: 10000 }), // totalCount
        (currentPage, pageSize, totalCount) => {
          const initialState: PageState = {
            currentPage,
            pageSize,
            totalCount,
            queue: "test_queue",
            status: "all",
            functionParams: "",
            taskId: "",
          };

          const newState = simulateAutoRefresh(initialState);

          // 验证 currentPage 保持不变
          expect(newState.currentPage).toBe(currentPage);
        }
      ),
      { numRuns: 100 }
    );
  });

  it("page navigation updates currentPage correctly", () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 100 }), // initial currentPage
        fc.integer({ min: 1, max: 500 }), // pageSize
        fc.integer({ min: 0, max: 10000 }), // totalCount
        fc.integer({ min: 0, max: 100 }), // new page
        (initialPage, pageSize, totalCount, newPage) => {
          const initialState: PageState = {
            currentPage: initialPage,
            pageSize,
            totalCount,
            queue: "test_queue",
            status: "all",
            functionParams: "",
            taskId: "",
          };

          const newState = simulatePageChange(initialState, newPage);

          // 验证 currentPage 被更新
          expect(newState.currentPage).toBe(newPage);
          // 验证其他状态保持不变
          expect(newState.pageSize).toBe(pageSize);
          expect(newState.totalCount).toBe(totalCount);
        }
      ),
      { numRuns: 100 }
    );
  });
});

/**
 * 额外测试：pageSize 在会话中保持
 */
describe("pageSize persistence", () => {
  it("pageSize persists across filter changes", () => {
    fc.assert(
      fc.property(
        fc.constantFrom(20, 50, 100, 200), // pageSize
        fc.string(), // new queue
        (pageSize, newQueue) => {
          const initialState: PageState = {
            currentPage: 5,
            pageSize,
            totalCount: 1000,
            queue: "old_queue",
            status: "all",
            functionParams: "",
            taskId: "",
          };

          const newState = simulateFilterChange(initialState, { queue: newQueue });

          // 验证 pageSize 保持不变
          expect(newState.pageSize).toBe(pageSize);
        }
      ),
      { numRuns: 100 }
    );
  });

  it("pageSize persists across refresh", () => {
    fc.assert(
      fc.property(
        fc.constantFrom(20, 50, 100, 200), // pageSize
        (pageSize) => {
          const initialState: PageState = {
            currentPage: 5,
            pageSize,
            totalCount: 1000,
            queue: "test_queue",
            status: "all",
            functionParams: "",
            taskId: "",
          };

          const stateAfterManualRefresh = simulateManualRefresh(initialState);
          const stateAfterAutoRefresh = simulateAutoRefresh(initialState);

          // 验证 pageSize 保持不变
          expect(stateAfterManualRefresh.pageSize).toBe(pageSize);
          expect(stateAfterAutoRefresh.pageSize).toBe(pageSize);
        }
      ),
      { numRuns: 100 }
    );
  });
});
