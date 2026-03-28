'use client'

import { useConversation } from '@elevenlabs/react'
import { useCallback, useState } from 'react'

export function VoiceInterview() {
  const [transcript, setTranscript] = useState<{role: string, text: string}[]>([])

  const conversation = useConversation({
    onConnect: () => console.log('Connected'),
    onDisconnect: () => console.log('Disconnected'),
    onError: (err) => console.error('🔴 Error:', err),
    onMessage: (message) => {
      console.log('Got transcript:', message)
      setTranscript(prev => [...prev, {
        role: message.source,
        text: message.message
      }])
    }
  })

  const start = useCallback(async () => {
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true })
      await conversation.startSession({
        agentId: process.env.NEXT_PUBLIC_ELEVENLABS_AGENT_ID!,
        overrides: {
          agent: {
            firstMessage: "Hi! I'm Alex, your interview coach. Are you ready for a few questions?",
          },
        }
      })
    } catch (err) {
      alert('Mic access required — please allow it in your browser.')
    }
  }, [conversation])

  const stop = useCallback(async () => {
    await conversation.endSession()  // ← just this, nothing else
  }, [conversation])

  return (
  <div>
    <p>Status: {conversation.status}</p>
    <p>Agent speaking: {conversation.isSpeaking ? '🔊 YES' : '🔇 NO'}</p>
    <button onClick={conversation.status === 'connected' ? stop : start}>
      {conversation.status === 'connected' ? 'Stop' : 'Start'}
    </button>
    <div>
      {transcript.map((msg, i) => (
        <p key={i}><strong>{msg.role}:</strong> {msg.text}</p>
      ))}
    </div>
  </div>
)
}