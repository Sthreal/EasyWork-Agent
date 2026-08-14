export interface MailConfig {
  qq_mail_address: string
  qq_mail_auth_code_masked: string
}

export async function getMail(userId: number): Promise<MailConfig> {
  const resp = await fetch(`/api/v1/users/me/mail?user_id=${userId}`)
  if (!resp.ok) throw new Error(`读取邮箱配置失败：${resp.status}`)
  return resp.json()
}

export async function saveMail(userId: number, address: string, code: string): Promise<MailConfig> {
  const resp = await fetch('/api/v1/users/me/mail', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, qq_mail_address: address, qq_mail_auth_code: code }),
  })
  if (!resp.ok) throw new Error(`保存失败：${resp.status}`)
  return resp.json()
}

export async function testMail(userId: number, address: string, code: string): Promise<{ ok: boolean; message: string }> {
  const resp = await fetch('/api/v1/users/me/mail/test', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, qq_mail_address: address, qq_mail_auth_code: code }),
  })
  const data = await resp.json()
  return data
}