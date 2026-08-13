export interface ConfirmationItem {
  id: number
  task_id: string | null
  action: string
  target: string
  params: string
  status: string
  created_at: string | null
}

export async function listPending(): Promise<ConfirmationItem[]> {
  const resp = await fetch('/api/v1/confirmations')
  if (!resp.ok) throw new Error(`获取待确认列表失败：${resp.status}`)
  const data = await resp.json()
  return data.items
}

export async function decide(id: number, approve: boolean): Promise<void> {
  const resp = await fetch(`/api/v1/confirmations/${id}/decide`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approve }),
  })
  if (!resp.ok) throw new Error(`确认操作失败：${resp.status}`)
}