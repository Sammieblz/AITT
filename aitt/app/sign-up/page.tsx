'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  CognitoUserPool,
  CognitoUser,
  CognitoUserAttribute,
} from 'amazon-cognito-identity-js'

export default function SignUpPage() {
  const router = useRouter()
  const pool = new CognitoUserPool({
    UserPoolId: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID!,
    ClientId: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID!,
  })

  const [step, setStep] = useState<'register' | 'confirm'>('register')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [code, setCode] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  function handleRegister(e: { preventDefault(): void }) {
    e.preventDefault()
    setError(null)

    if (password !== confirm) {
      setError('Passwords do not match')
      return
    }

    setLoading(true)
    const attributes = [
      new CognitoUserAttribute({ Name: 'email', Value: email }),
      new CognitoUserAttribute({ Name: 'name', Value: name }),
    ]

    pool.signUp(email, password, attributes, [], (err) => {
      if (err) {
        setError(err.message ?? 'Sign up failed')
        setLoading(false)
        return
      }
      setLoading(false)
      setStep('confirm')
    })
  }

  function handleConfirm(e: { preventDefault(): void }) {
    e.preventDefault()
    setError(null)
    setLoading(true)

    const user = new CognitoUser({ Username: email, Pool: pool })
    user.confirmRegistration(code, true, (err) => {
      if (err) {
        setError(err.message ?? 'Confirmation failed')
        setLoading(false)
        return
      }
      router.replace('/login')
    })
  }

  const inputStyle = {
    padding: '0.75rem',
    borderRadius: '8px',
    border: '1px solid #333',
    background: '#111',
    color: '#fff',
  }

  const submitStyle = {
    padding: '0.75rem',
    borderRadius: '8px',
    background: '#B4FF5B',
    color: '#000',
    fontWeight: 600 as const,
    cursor: loading ? ('not-allowed' as const) : ('pointer' as const),
    opacity: loading ? 0.7 : 1,
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
      {step === 'register' ? (
        <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', width: '320px' }}>
          <h1 style={{ fontWeight: 700, fontSize: '1.5rem' }}>Create account</h1>

          <input
            type="text"
            placeholder="Full name"
            value={name}
            onChange={e => setName(e.target.value)}
            required
            style={inputStyle}
          />
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
            style={inputStyle}
          />
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              style={inputStyle}
            />
            <p style={{ fontSize: '0.75rem', color: '#666', lineHeight: 1.5 }}>
              Must be 8+ characters and include an uppercase letter, a lowercase letter, a number, and a special character (e.g. !@#$%).
            </p>
          </div>
          <input
            type="password"
            placeholder="Confirm password"
            value={confirm}
            onChange={e => setConfirm(e.target.value)}
            required
            style={inputStyle}
          />

          {error && <p style={{ color: '#ff4444', fontSize: '0.875rem' }}>{error}</p>}

          <button type="submit" disabled={loading} style={submitStyle}>
            {loading ? 'Creating account…' : 'Sign up'}
          </button>

          <p style={{ textAlign: 'center', fontSize: '0.875rem', color: '#888' }}>
            Already have an account?{' '}
            <Link href="/login" style={{ color: '#B4FF5B' }}>Sign in</Link>
          </p>
        </form>
      ) : (
        <form onSubmit={handleConfirm} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', width: '320px' }}>
          <h1 style={{ fontWeight: 700, fontSize: '1.5rem' }}>Verify your email</h1>
          <p style={{ color: '#888', fontSize: '0.875rem' }}>
            We sent a confirmation code to <strong style={{ color: '#fff' }}>{email}</strong>.
          </p>

          <input
            type="text"
            placeholder="Confirmation code"
            value={code}
            onChange={e => setCode(e.target.value)}
            required
            style={inputStyle}
          />

          {error && <p style={{ color: '#ff4444', fontSize: '0.875rem' }}>{error}</p>}

          <button type="submit" disabled={loading} style={submitStyle}>
            {loading ? 'Verifying…' : 'Confirm'}
          </button>
        </form>
      )}
    </div>
  )
}
