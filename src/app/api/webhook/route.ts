/**
 * WhatsApp Webhook Endpoint
 *
 * This Next.js API route handles WhatsApp Business API webhook notifications
 *
 * DEPLOYMENT: This runs on Vercel as a serverless function
 */

import { NextRequest, NextResponse } from 'next/server';

/**
 * GET handler for webhook verification
 *
 * WhatsApp will send a GET request to verify your webhook endpoint
 *
 * TODO:
 * - Extract query parameters: hub.mode, hub.verify_token, hub.challenge
 * - Check if hub.mode === 'subscribe'
 * - Check if hub.verify_token === process.env.WHATSAPP_WEBHOOK_VERIFY_TOKEN
 * - If valid, return hub.challenge (as plain text with 200 status)
 * - If invalid, return 403 Forbidden
 *
 * DOCS: https://developers.facebook.com/docs/graph-api/webhooks/getting-started#verification-requests
 */
export async function GET(request: NextRequest) {
  // TODO: Implement webhook verification

  return new NextResponse('Not implemented', { status: 501 });
}

/**
 * POST handler for receiving WhatsApp messages
 *
 * WhatsApp sends a POST request when a user sends a message
 *
 * TODO:
 * 1. Parse the webhook payload (JSON body)
 * 2. Check if it's a message or status update (ignore status updates)
 * 3. Extract: phone_number, message_text, message_id
 * 4. Call Python agent system to process message:
 *    - Option A: Make HTTP request to separate Python service
 *    - Option B: Use child_process to run Python script
 *    - Option C: For now, use TypeScript implementation
 * 5. Get agent response
 * 6. Send response back via WhatsApp API
 * 7. Return 200 OK to WhatsApp (they require quick response)
 *
 * WEBHOOK PAYLOAD STRUCTURE:
 * {
 *   "object": "whatsapp_business_account",
 *   "entry": [{
 *     "changes": [{
 *       "value": {
 *         "messages": [{
 *           "from": "1234567890",
 *           "id": "wamid.xxx",
 *           "text": { "body": "Hello" },
 *           "timestamp": "1234567890"
 *         }]
 *       }
 *     }]
 *   }]
 * }
 *
 * DOCS: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples
 */
export async function POST(request: NextRequest) {
  try {
    // TODO: Parse body
    const body = await request.json();

    // TODO: Extract message data

    // TODO: Process with agent (temporary TypeScript implementation)
    // Later: Call Python agent system

    // TODO: Send response via WhatsApp API

    // Return 200 OK quickly (WhatsApp requires response within 20 seconds)
    return NextResponse.json({ status: 'ok' }, { status: 200 });

  } catch (error) {
    console.error('Webhook error:', error);
    // Still return 200 to prevent WhatsApp from retrying
    return NextResponse.json({ status: 'error' }, { status: 200 });
  }
}
