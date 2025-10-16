/**
 * WhatsApp Webhook Endpoint
 *
 * This Next.js API route handles WhatsApp Business API webhook notifications
 *
 * DEPLOYMENT: This runs on Vercel as a serverless function
 */

import { NextRequest, NextResponse } from 'next/server';
import { query } from '@anthropic-ai/claude-agent-sdk';
import path from 'path';

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
  // Extract query parameters from WhatsApp verification request
  const searchParams = request.nextUrl.searchParams;
  const mode = searchParams.get('hub.mode');
  const token = searchParams.get('hub.verify_token');
  const challenge = searchParams.get('hub.challenge');

  // Enhanced debugging - show exact values
  console.log('=== WEBHOOK VERIFICATION DEBUG ===');
  console.log('Received mode:', mode);
  console.log('Received token:', token);
  console.log('Expected token:', process.env.WHATSAPP_WEBHOOK_VERIFY_TOKEN);
  console.log('Tokens match:', token === process.env.WHATSAPP_WEBHOOK_VERIFY_TOKEN);
  console.log('Challenge:', challenge);
  console.log('Env var exists:', !!process.env.WHATSAPP_WEBHOOK_VERIFY_TOKEN);
  console.log('================================');

  // Verify the token matches your environment variable
  if (mode === 'subscribe' && token === process.env.WHATSAPP_WEBHOOK_VERIFY_TOKEN) {
    console.log('✅ Webhook verified successfully!');
    // Return the challenge to WhatsApp to confirm verification
    return new NextResponse(challenge, { status: 200 });
  }

  // If verification fails, return detailed error for debugging
  console.error('❌ Webhook verification failed');
  console.error('Failure reason:', {
    modeCorrect: mode === 'subscribe',
    tokenCorrect: token === process.env.WHATSAPP_WEBHOOK_VERIFY_TOKEN,
  });

  return new NextResponse('Forbidden', { status: 403 });
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
    // Parse the webhook payload from WhatsApp
    const body = await request.json();

    console.log('Received webhook:', JSON.stringify(body, null, 2));

    // Extract message data from nested structure
    const entry = body.entry?.[0];
    const changes = entry?.changes?.[0];
    const value = changes?.value;
    const messages = value?.messages?.[0];

    // Ignore if no message (could be status update)
    if (!messages) {
      console.log('No message found, ignoring webhook');
      return NextResponse.json({ status: 'ok' }, { status: 200 });
    }

    // Extract message details
    const from = messages.from; // Phone number of sender
    const messageId = messages.id;
    const messageText = messages.text?.body;

    console.log('Message received:', { from, messageText, messageId });

    // Process message with Claude AI
    const aiResponse = await processWithClaude(messageText, from);

    // Send response back to user via WhatsApp API
    await sendWhatsAppMessage(from, aiResponse);

    // Return 200 OK quickly (WhatsApp requires response within 20 seconds)
    return NextResponse.json({ status: 'ok' }, { status: 200 });

  } catch (error) {
    console.error('Webhook error:', error);
    // Still return 200 to prevent WhatsApp from retrying
    return NextResponse.json({ status: 'error' }, { status: 200 });
  }
}

/**
 * Store conversation history per user
 * In production: use Redis or database for persistence across serverless invocations
 */
const conversationSessions = new Map<string, string>();

/**
 * Process message with Claude Agent SDK using query()
 *
 * The SDK reads ANTHROPIC_API_KEY from environment variables automatically
 * Maintains conversation history per phone number using session resumption
 */
async function processWithClaude(userMessage: string, phoneNumber: string): Promise<string> {
  try {
    console.log(`Processing message from ${phoneNumber} with Claude Agent SDK...`);

    const systemPrompt = process.env.AGENT_SYSTEM_PROMPT ||
      'You are a helpful WhatsApp assistant. Keep responses concise and friendly since messages are sent via WhatsApp. Aim for 1-3 paragraphs maximum.';

    // Get previous session ID for this user (for conversation continuity)
    const previousSession = conversationSessions.get(phoneNumber);

    // Set path to Claude Code CLI executable
    // In production (Vercel), it's bundled in node_modules
    const cliPath = path.join(process.cwd(), 'node_modules', '@anthropic-ai', 'claude-agent-sdk', 'cli.js');

    console.log('Claude CLI path:', cliPath);

    // Use query() function to get response from Claude
    // API key is read from ANTHROPIC_API_KEY environment variable
    const result = query({
      prompt: userMessage,
      options: {
        model: 'claude-3-5-sonnet-20241022',
        systemPrompt: systemPrompt,
        maxTurns: 5, // Allow multi-turn conversations
        pathToClaudeCodeExecutable: cliPath,
        executable: 'node',
        env: {
          ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY || '',
        },
        // Resume previous conversation if exists
        ...(previousSession && { resume: previousSession }),
      },
    });

    let responseText = '';
    let sessionId = '';

    // Stream messages and collect assistant responses
    for await (const message of result) {
      if (message.type === 'system') {
        // Store session ID for conversation continuity
        sessionId = message.session_id;
        console.log(`Session ID for ${phoneNumber}:`, sessionId);
      } else if (message.type === 'assistant') {
        // Extract text content from assistant message
        const content = message.message.content;
        for (const block of content) {
          if (block.type === 'text') {
            responseText += block.text;
          }
        }
      } else if (message.type === 'result') {
        console.log('Query completed. Cost:', message.total_cost_usd, 'Tokens:', message.usage);
      }
    }

    // Store session for next message from this user
    if (sessionId) {
      conversationSessions.set(phoneNumber, sessionId);
    }

    console.log('Agent response received:', responseText.substring(0, 100) + '...');

    return responseText || 'Sorry, I could not generate a response.';
  } catch (error) {
    console.error('Error calling Claude Agent:', error);
    return 'Sorry, I encountered an error processing your message. Please try again.';
  }
}

/**
 * Send a WhatsApp message via Cloud API
 */
async function sendWhatsAppMessage(to: string, text: string) {
  const url = `https://graph.facebook.com/v18.0/${process.env.WHATSAPP_PHONE_NUMBER_ID}/messages`;

  const payload = {
    messaging_product: 'whatsapp',
    to: to,
    type: 'text',
    text: { body: text }
  };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.WHATSAPP_ACCESS_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      console.error('WhatsApp API error:', data);
      throw new Error(`WhatsApp API error: ${JSON.stringify(data)}`);
    }

    console.log('Message sent successfully:', data);
    return data;
  } catch (error) {
    console.error('Error sending WhatsApp message:', error);
    throw error;
  }
}
