'use client'

import { createContext, useContext, useEffect, useState } from 'react'
import { getAuthUser, type AuthUser } from './auth'

interface AuthContextValue {
  user: AuthUser | null
  loading: boolean
}

const AuthContext = createContext<AuthContextValue>({ user: null, loading: true })

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setUser(getAuthUser())
    setLoading(false)
  }, [])

  return <AuthContext.Provider value={{ user, loading }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
