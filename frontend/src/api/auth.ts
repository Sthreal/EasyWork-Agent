export interface User {
  user_id: number
  open_id: string
  name: string
  avatar_url: string
}

const KEY = 'office_agent_user'

export function getStoredUser(): User | null {
  const raw = localStorage.getItem(KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as User
  } catch {
    return null
  }
}

export function saveStoredUser(user: User): void {
  localStorage.setItem(KEY, JSON.stringify(user))
}

export function clearStoredUser(): void {
  localStorage.removeItem(KEY)
}