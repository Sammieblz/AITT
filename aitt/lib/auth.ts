export interface AuthUser {
  userId: string
  name: string
  email: string
}

export function getAuthUser(): AuthUser | null {
  if (typeof window === 'undefined') return null

  const clientId = process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID
  if (!clientId) return null

  const prefix = `CognitoIdentityServiceProvider.${clientId}`
  const username = localStorage.getItem(`${prefix}.LastAuthUser`)
  if (!username) return null

  const idToken = localStorage.getItem(`${prefix}.${username}.idToken`)
  if (!idToken) return null

  try {
    const payload = JSON.parse(atob(idToken.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
    return {
      userId: payload.sub,
      name: payload.name ?? username,
      email: payload.email ?? username,
    }
  } catch {
    return null
  }
}
