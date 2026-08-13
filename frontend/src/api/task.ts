export interface TaskResult {
  task_id: string
  status: string
  text: string
}

export async function createTask(text: string): Promise<TaskResult> {
  const resp = await fetch('/api/v1/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!resp.ok) {
    throw new Error(`任务提交失败：${resp.status}`)
  }
  return resp.json()
}