'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  CognitoUserPool,
  CognitoUser,
  AuthenticationDetails,
} from 'amazon-cognito-identity-js'

export default function LoginPage() {
  const router = useRouter()
  const pool = new CognitoUserPool({
    UserPoolId: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID!,
    ClientId: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID!,
  })
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  function handleSubmit(e: { preventDefault(): void }) {
    e.preventDefault()
    setError(null)
    setLoading(true)

    const user = new CognitoUser({ Username: email, Pool: pool })
    const authDetails = new AuthenticationDetails({ Username: email, Password: password })

    user.authenticateUser(authDetails, {
      onSuccess: async () => {
        const clientId = process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID!
        const prefix = `CognitoIdentityServiceProvider.${clientId}`
        const username = localStorage.getItem(`${prefix}.LastAuthUser`)
        const idToken = username ? localStorage.getItem(`${prefix}.${username}.idToken`) : null
        let userId: string | null = null
        if (idToken) {
          try {
            const payload = JSON.parse(atob(idToken.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
            userId = payload.sub
          } catch { /* ignore */ }
        }
        if (userId) {
          const res = await fetch(`/api/user?userId=${userId}`)
          router.replace(res.ok ? '/dashboard' : '/setup')
        } else {
          router.replace('/dashboard')
        }
      },
      onFailure: (err) => {
        setError(err.message ?? 'Login failed')
        setLoading(false)
      },
    })
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', width: '320px' }}>
        <h1 style={{ fontWeight: 700, fontSize: '1.5rem' }}>Sign in</h1>

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          required
          style={{ padding: '0.75rem', borderRadius: '8px', border: '1px solid #333', background: '#111', color: '#fff' }}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          required
          style={{ padding: '0.75rem', borderRadius: '8px', border: '1px solid #333', background: '#111', color: '#fff' }}
        />

        {error && <p style={{ color: '#ff4444', fontSize: '0.875rem' }}>{error}</p>}

        <button
          type="submit"
          disabled={loading}
          style={{ padding: '0.75rem', borderRadius: '8px', background: '#B4FF5B', color: '#000', fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1 }}
        >
          {loading ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </div>
  )
}
