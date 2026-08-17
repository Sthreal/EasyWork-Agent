import { getAuthHeaders } from './auth'

export interface ChatMessage {
  id: number
  role: 'user' | 'agent'
  text: string
  payload: Record<string, unknown> | null
  created_at: string | null
}

export async function saveMessage(
  userId: number | undefined,
  role: string,
  text: string,
  payload?: unknown
): Promise<void> {
  try {
    await fetch('/api/v1/chat/messages', {
      method: 'POST',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId ?? null, role, text, payload: payload ?? null }),
    })
  } catch {
    // best-effort：保存失败不影响聊天
  }
}

export async function listMessages(userId: number | undefined, limit = 100): Promise<ChatMessage[]> {
  try {
    const resp = await fetch(`/api/v1/chat/messages?user_id=${userId ?? ''}&limit=${limit}`, {
      headers: getAuthHeaders(),
    })
    if (!resp.ok) return []
    const data = await resp.json()
    return data.items || []
  } catch {
    return []
  }
}
