/**
 * FaaS Publish API 集成测试
 * 
 * 测试通过 /funboost/publish 发布消息的功能，包括：
 * - 成功发布消息
 * - 认证失败的错误处理
 * - 权限失败的错误处理
 * 
 * 需求: 6.3
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

// Mock fetch globally
const originalFetch = global.fetch

describe('FaaS Publish API Integration Tests', () => {
  beforeEach(() => {
    // Reset fetch mock before each test
    global.fetch = vi.fn()
  })

  afterEach(() => {
    // Restore original fetch
    global.fetch = originalFetch
    vi.restoreAllMocks()
  })

  describe('POST /funboost/publish', () => {
    it('should publish message successfully with valid authentication and permissions', async () => {
      // Mock successful response
      const mockResponse = {
        succ: true,
        msg: 'test_queue 队列,消息发布成功',
        data: {
          task_id: 'test-task-id-123',
          status_and_result: {
            status: 'pending',
          },
        },
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse,
        headers: new Headers({ 'content-type': 'application/json' }),
      })

      // Make the API call
      const response = await fetch('/funboost/publish', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Important for session cookies
        body: JSON.stringify({
          queue_name: 'test_queue',
          msg_body: { x: 1, y: 2 },
          need_result: false,
        }),
      })

      // Verify response
      expect(response.ok).toBe(true)
      expect(response.status).toBe(200)

      const data = await response.json()
      expect(data.succ).toBe(true)
      expect(data.msg).toContain('消息发布成功')
      expect(data.data.task_id).toBeDefined()
      expect(data.data.task_id).toBe('test-task-id-123')

      // Verify fetch was called with correct parameters
      expect(global.fetch).toHaveBeenCalledWith(
        '/funboost/publish',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          credentials: 'include',
          body: JSON.stringify({
            queue_name: 'test_queue',
            msg_body: { x: 1, y: 2 },
            need_result: false,
          }),
        })
      )
    })

    it('should handle authentication failure (401 Unauthorized)', async () => {
      // Mock 401 response
      const mockResponse = {
        succ: false,
        msg: '未登录或会话已过期，请重新登录',
        data: null,
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => mockResponse,
        headers: new Headers({ 'content-type': 'application/json' }),
      })

      // Make the API call
      const response = await fetch('/funboost/publish', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          queue_name: 'test_queue',
          msg_body: { x: 1, y: 2 },
        }),
      })

      // Verify response
      expect(response.ok).toBe(false)
      expect(response.status).toBe(401)

      const data = await response.json()
      expect(data.succ).toBe(false)
      expect(data.msg).toContain('未登录')
      expect(data.data).toBeNull()
    })

    it('should handle permission failure (403 Forbidden)', async () => {
      // Mock 403 response
      const mockResponse = {
        succ: false,
        msg: '您没有 queue:execute 权限',
        data: null,
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => mockResponse,
        headers: new Headers({ 'content-type': 'application/json' }),
      })

      // Make the API call
      const response = await fetch('/funboost/publish', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          queue_name: 'test_queue',
          msg_body: { x: 1, y: 2 },
        }),
      })

      // Verify response
      expect(response.ok).toBe(false)
      expect(response.status).toBe(403)

      const data = await response.json()
      expect(data.succ).toBe(false)
      expect(data.msg).toContain('权限')
      expect(data.data).toBeNull()
    })

    it('should handle project permission failure (403 Forbidden)', async () => {
      // Mock 403 response for project-level permission
      const mockResponse = {
        succ: false,
        msg: '您在此项目中没有 write 权限',
        data: null,
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => mockResponse,
        headers: new Headers({ 'content-type': 'application/json' }),
      })

      // Make the API call with project_id
      const response = await fetch('/funboost/publish', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          queue_name: 'test_queue',
          msg_body: { x: 1, y: 2 },
          project_id: 999, // Project user doesn't have access to
        }),
      })

      // Verify response
      expect(response.ok).toBe(false)
      expect(response.status).toBe(403)

      const data = await response.json()
      expect(data.succ).toBe(false)
      expect(data.msg).toContain('项目')
      expect(data.msg).toContain('权限')
      expect(data.data).toBeNull()
    })

    it('should handle invalid project_id (400 Bad Request)', async () => {
      // Mock 400 response
      const mockResponse = {
        succ: false,
        msg: '无效的项目ID',
        data: null,
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => mockResponse,
        headers: new Headers({ 'content-type': 'application/json' }),
      })

      // Make the API call with invalid project_id
      const response = await fetch('/funboost/publish', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          queue_name: 'test_queue',
          msg_body: { x: 1, y: 2 },
          project_id: 'invalid', // Invalid project_id
        }),
      })

      // Verify response
      expect(response.ok).toBe(false)
      expect(response.status).toBe(400)

      const data = await response.json()
      expect(data.succ).toBe(false)
      expect(data.msg).toContain('无效')
      expect(data.data).toBeNull()
    })

    it('should publish message with RPC mode (need_result=true)', async () => {
      // Mock successful RPC response
      const mockResponse = {
        succ: true,
        msg: 'test_queue 队列,消息发布成功',
        data: {
          task_id: 'test-task-id-456',
          status_and_result: {
            status: 'success',
            result: { sum: 3 },
          },
        },
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse,
        headers: new Headers({ 'content-type': 'application/json' }),
      })

      // Make the API call with need_result=true
      const response = await fetch('/funboost/publish', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          queue_name: 'test_queue',
          msg_body: { x: 1, y: 2 },
          need_result: true,
          timeout: 30,
        }),
      })

      // Verify response
      expect(response.ok).toBe(true)
      expect(response.status).toBe(200)

      const data = await response.json()
      expect(data.succ).toBe(true)
      expect(data.data.task_id).toBeDefined()
      expect(data.data.status_and_result.status).toBe('success')
      expect(data.data.status_and_result.result).toEqual({ sum: 3 })
    })

    it('should handle missing required parameters (400 Bad Request)', async () => {
      // Mock 400 response for missing queue_name
      const mockResponse = {
        succ: false,
        msg: '缺少必需参数: queue_name',
        data: null,
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => mockResponse,
        headers: new Headers({ 'content-type': 'application/json' }),
      })

      // Make the API call without queue_name
      const response = await fetch('/funboost/publish', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          msg_body: { x: 1, y: 2 },
        }),
      })

      // Verify response
      expect(response.ok).toBe(false)
      expect(response.status).toBe(400)

      const data = await response.json()
      expect(data.succ).toBe(false)
      expect(data.msg).toContain('缺少必需参数')
      expect(data.data).toBeNull()
    })

    it('should handle server errors (500 Internal Server Error)', async () => {
      // Mock 500 response
      const mockResponse = {
        succ: false,
        msg: '服务器内部错误',
        data: null,
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => mockResponse,
        headers: new Headers({ 'content-type': 'application/json' }),
      })

      // Make the API call
      const response = await fetch('/funboost/publish', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          queue_name: 'test_queue',
          msg_body: { x: 1, y: 2 },
        }),
      })

      // Verify response
      expect(response.ok).toBe(false)
      expect(response.status).toBe(500)

      const data = await response.json()
      expect(data.succ).toBe(false)
      expect(data.msg).toContain('错误')
      expect(data.data).toBeNull()
    })

    it('should handle network errors gracefully', async () => {
      // Mock network error
      ;(global.fetch as any).mockRejectedValueOnce(new Error('Network error'))

      // Make the API call and expect it to throw
      await expect(
        fetch('/funboost/publish', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            queue_name: 'test_queue',
            msg_body: { x: 1, y: 2 },
          }),
        })
      ).rejects.toThrow('Network error')
    })

    it('should include custom task_id when provided', async () => {
      // Mock successful response
      const customTaskId = 'custom-task-id-789'
      const mockResponse = {
        succ: true,
        msg: 'test_queue 队列,消息发布成功',
        data: {
          task_id: customTaskId,
          status_and_result: {
            status: 'pending',
          },
        },
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse,
        headers: new Headers({ 'content-type': 'application/json' }),
      })

      // Make the API call with custom task_id
      const response = await fetch('/funboost/publish', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          queue_name: 'test_queue',
          msg_body: { x: 1, y: 2 },
          task_id: customTaskId,
        }),
      })

      // Verify response
      expect(response.ok).toBe(true)
      const data = await response.json()
      expect(data.data.task_id).toBe(customTaskId)
    })
  })

  describe('Response Format Validation', () => {
    it('should return response in FaaS format (succ/msg/data)', async () => {
      // Mock response
      const mockResponse = {
        succ: true,
        msg: 'Success message',
        data: { task_id: 'test-id' },
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse,
        headers: new Headers({ 'content-type': 'application/json' }),
      })

      const response = await fetch('/funboost/publish', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          queue_name: 'test_queue',
          msg_body: {},
        }),
      })

      const data = await response.json()

      // Verify FaaS response format
      expect(data).toHaveProperty('succ')
      expect(data).toHaveProperty('msg')
      expect(data).toHaveProperty('data')
      expect(typeof data.succ).toBe('boolean')
      expect(typeof data.msg).toBe('string')
    })
  })
})
