import { DynamoDBClient } from '@aws-sdk/client-dynamodb'
import { DynamoDBDocumentClient } from '@aws-sdk/lib-dynamodb'

const client = new DynamoDBClient({ region: process.env.AWS_DEFAULT_REGION ?? 'us-east-1' })
export const ddb = DynamoDBDocumentClient.from(client)
