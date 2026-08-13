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
}

export interface TaskResult {
  task_id: string
  status: string
  text: string
  tasks: TaskItem[]
  question?: string | null
  message?: string | null
}

const TIMEOUT_MS = 30000

export async function createTask(text: string, round = 1): Promise<TaskResult> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)
  try {
    const resp = await fetch('/api/v1/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, round }),
      signal: controller.signal,
    })
    if (!resp.ok) throw new Error(`任务提交失败：${resp.status}`)
    return resp.json()
  } finally {
    clearTimeout(timer)
  }
}