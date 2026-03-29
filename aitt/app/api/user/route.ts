import { NextRequest, NextResponse } from 'next/server'
import { GetCommand, PutCommand } from '@aws-sdk/lib-dynamodb'
import { ddb } from '@/lib/dynamodb'

const TABLE = 'aitt-users'

export async function GET(req: NextRequest) {
  const userId = req.nextUrl.searchParams.get('userId')
  if (!userId) return NextResponse.json({ error: 'Missing userId' }, { status: 400 })

  try {
    const result = await ddb.send(new GetCommand({ TableName: TABLE, Key: { userId } }))
    if (!result.Item) return NextResponse.json({ error: 'Not found' }, { status: 404 })
    return NextResponse.json(result.Item)
  } catch (err) {
    console.error('[GET /api/user]', err)
    return NextResponse.json({ error: String(err) }, { status: 500 })
  }
}

export async function PUT(req: NextRequest) {
  const body = await req.json()
  const { userId } = body
  if (!userId) return NextResponse.json({ error: 'Missing userId' }, { status: 400 })

  try {
    await ddb.send(new PutCommand({ TableName: TABLE, Item: body }))
    return NextResponse.json({ ok: true })
  } catch (err) {
    console.error('[PUT /api/user]', err)
    return NextResponse.json({ error: String(err) }, { status: 500 })
  }
}
