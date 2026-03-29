import { NextRequest, NextResponse } from 'next/server'
import { QueryCommand, PutCommand } from '@aws-sdk/lib-dynamodb'
import { ddb } from '@/lib/dynamodb'

const TABLE = 'aitt-sessions'

export async function GET(req: NextRequest) {
  const userId = req.nextUrl.searchParams.get('userId')
  if (!userId) return NextResponse.json({ error: 'Missing userId' }, { status: 400 })

  try {
    const result = await ddb.send(new QueryCommand({
      TableName: TABLE,
      KeyConditionExpression: 'userId = :uid',
      ExpressionAttributeValues: { ':uid': userId },
      ScanIndexForward: false,
      Limit: 50,
    }))
    return NextResponse.json(result.Items ?? [])
  } catch (err) {
    console.error('[GET /api/sessions]', err)
    return NextResponse.json({ error: String(err) }, { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  const { userId, scores, durationMinutes, categories } = await req.json()
  if (!userId || !scores) return NextResponse.json({ error: 'Missing required fields' }, { status: 400 })

  const sessionId = crypto.randomUUID()
  const avg = scores.reduce((s: number, v: number) => s + v, 0) / scores.length
  const score = Math.round(avg * 10) / 10

  const topInsight = score >= 4
    ? 'Strong performance — your STAR structure was clear and compelling.'
    : score >= 3
    ? 'Good foundation — focus on quantifying your results more specifically.'
    : 'Keep practicing — try to include a concrete outcome in every answer.'

  const item = {
    userId,
    sessionId,
    date: new Date().toISOString().split('T')[0],
    scores,
    score,
    durationMinutes: durationMinutes ?? 0,
    categories: categories ?? [],
    topInsight,
  }

  await ddb.send(new PutCommand({ TableName: TABLE, Item: item }))
  return NextResponse.json({ sessionId })
}
