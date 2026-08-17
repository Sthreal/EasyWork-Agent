import { getAuthHeaders } from './auth'
import type { DiffChange } from './confirmation'

export interface TaskItem {
  action: string
  target: string
  params: string
  high_risk: boolean
  tool: string
  args: Record<string, unknown>
  status: string
  result: string
  confirmation_id: number | null
  in_workspace: boolean | null
  preview: DiffChange[] | null
}

export interface TaskResult {
  task_id: string
  status: string
  text: string
  tasks: TaskItem[]
  question?: string | null
  message?: string | null
}

export interface TaskRecord {
  task_id: string
  text: string
  status: string
  question: string | null
  created_at: string | null
  tasks: TaskItem[]
}

export interface TaskListResult {
  items: TaskRecord[]
  total: number
}

export interface TaskListParams {
  userId?: number
  q?: string
  status?: string
  dateFrom?: string
  dateTo?: string
  limit?: number
  offset?: number
}

const TIMEOUT_MS = 30000

export async function createTask(text: string, round = 1, userId?: number, force = false): Promise<TaskResult> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)
  try {
    const resp = await fetch('/api/v1/tasks', {
      method: 'POST',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, round, user_id: userId ?? null, force }),
      signal: controller.signal,
    })
    if (!resp.ok) throw new Error(`任务提交失败：${resp.status}`)
    return resp.json()
  } finally {
    clearTimeout(timer)
  }
}

export async function getTask(taskId: string | number): Promise<TaskResult | null> {
  try {
    const resp = await fetch(`/api/v1/tasks/${taskId}`, { headers: getAuthHeaders() })
    if (!resp.ok) return null
    return resp.json()
  } catch {
    return null
  }
}

export async function listTasks(params: TaskListParams = {}): Promise<TaskListResult> {
  const qs = new URLSearchParams()
  if (params.userId != null) qs.set('user_id', String(params.userId))
  if (params.q) qs.set('q', params.q)
  if (params.status) qs.set('status', params.status)
  if (params.dateFrom) qs.set('date_from', params.dateFrom)
  if (params.dateTo) qs.set('date_to', params.dateTo)
  if (params.limit != null) qs.set('limit', String(params.limit))
  if (params.offset != null) qs.set('offset', String(params.offset))
  const resp = await fetch(`/api/v1/tasks?${qs.toString()}`, { headers: getAuthHeaders() })
  if (!resp.ok) throw new Error(`获取任务历史失败：${resp.status}`)
  const data = await resp.json()
  return { items: data.items || [], total: data.total || 0 }
}

export function exportTasksCsv(records: TaskRecord[]): void {
  const header = ['任务ID', '状态', '任务内容', '追问问题', '创建时间', '子任务']
  const rows = records.map((r) => {
    const steps = (r.tasks || [])
      .map((s) => `${s.action}${s.target ? ' ' + s.target : ''}(${s.status})`)
      .join('; ')
    return [r.task_id, r.status, r.text, r.question || '', r.created_at || '', steps]
  })
  const csv =
    '\uFEFF' +
    [header, ...rows]
      .map((row) => row.map((cell) => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(','))
      .join('\r\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `tasks_${Date.now()}.csv`
  a.click()
  URL.revokeObjectURL(url)
}