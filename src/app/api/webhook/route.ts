/**
 * WhatsApp Webhook Endpoint
 *
 * This Next.js API route handles WhatsApp Business API webhook notifications
 *
 * DEPLOYMENT: This runs on Vercel as a serverless function
 */

import { NextRequest, NextResponse } from "next/server";
import { Anthropic } from "@anthropic-ai/sdk";

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
  const mode = searchParams.get("hub.mode");
  const token = searchParams.get("hub.verify_token");
  const challenge = searchParams.get("hub.challenge");

  // Enhanced debugging - show exact values
  console.log("=== WEBHOOK VERIFICATION DEBUG ===");
  console.log("Received mode:", mode);
  console.log("Received token:", token);
  console.log("Expected token:", process.env.WHATSAPP_WEBHOOK_VERIFY_TOKEN);
  console.log(
    "Tokens match:",
    token === process.env.WHATSAPP_WEBHOOK_VERIFY_TOKEN
  );
  console.log("Challenge:", challenge);
  console.log("Env var exists:", !!process.env.WHATSAPP_WEBHOOK_VERIFY_TOKEN);
  console.log("================================");

  // Verify the token matches your environment variable
  if (
    mode === "subscribe" &&
    token === process.env.WHATSAPP_WEBHOOK_VERIFY_TOKEN
  ) {
    console.log("✅ Webhook verified successfully!");
    // Return the challenge to WhatsApp to confirm verification
    return new NextResponse(challenge, { status: 200 });
  }

  // If verification fails, return detailed error for debugging
  console.error("❌ Webhook verification failed");
  console.error("Failure reason:", {
    modeCorrect: mode === "subscribe",
    tokenCorrect: token === process.env.WHATSAPP_WEBHOOK_VERIFY_TOKEN,
  });

  return new NextResponse("Forbidden", { status: 403 });
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

    console.log("Received webhook:", JSON.stringify(body, null, 2));

    // Extract message data from nested structure
    const entry = body.entry?.[0];
    const changes = entry?.changes?.[0];
    const value = changes?.value;
    const messages = value?.messages?.[0];

    // Ignore if no message (could be status update)
    if (!messages) {
      console.log("No message found, ignoring webhook");
      return NextResponse.json({ status: "ok" }, { status: 200 });
    }

    // Extract message details
    const from = messages.from; // Phone number of sender
    const messageId = messages.id;
    const messageText = messages.text?.body;

    console.log("Message received:", { from, messageText, messageId });

    // Process message with Claude AI
    const aiResponse = await processWithClaude(messageText, from);

    // Send response back to user via WhatsApp API
    await sendWhatsAppMessage(from, aiResponse);

    // Return 200 OK quickly (WhatsApp requires response within 20 seconds)
    return NextResponse.json({ status: "ok" }, { status: 200 });
  } catch (error) {
    console.error("Webhook error:", error);
    // Still return 200 to prevent WhatsApp from retrying
    return NextResponse.json({ status: "error" }, { status: 200 });
  }
}

/**
 * Store conversation history per user
 * In production: use Redis or database for persistence across serverless invocations
 */
const conversationHistory = new Map<
  string,
  Array<{ role: "user" | "assistant"; content: string }>
>();

/**
 * Process message with Anthropic SDK
 * Uses Messages API with streaming for efficient responses
 */
async function processWithClaude(
  userMessage: string,
  phoneNumber: string
): Promise<string> {
  try {
    console.log(`Processing message from ${phoneNumber} with Anthropic SDK...`);

    const systemPrompt =
      process.env.AGENT_SYSTEM_PROMPT ||
      "You are a helpful WhatsApp assistant. Keep responses concise and friendly since messages are sent via WhatsApp. Aim for 1-3 paragraphs maximum.";

    // Initialize the Anthropic client
    const anthropic = new Anthropic({
      apiKey: process.env.ANTHROPIC_API_KEY,
    });

    // Get conversation history for this user
    const history = conversationHistory.get(phoneNumber) || [];

    // Convert history to Anthropic messages format
    const messages = history.map((msg) => ({
      role: msg.role,
      content: msg.content,
    }));

    // Add the new user message
    messages.push({
      role: "user",
      content: userMessage,
    });

    console.log("Starting Anthropic API call...");
    console.log("API Key exists:", !!process.env.ANTHROPIC_API_KEY);
    console.log("Message count:", messages.length);

    // Make the API call with streaming
    const stream = await anthropic.messages.create({
      model: "claude-3-5-sonnet-20241022",
      system: systemPrompt,
      messages: messages,
      max_tokens: 1000,
      stream: true,
    });

    let responseText = "";

    // Process the stream
    for await (const chunk of stream) {
      if (chunk.type === "content_block_delta" && chunk.delta.type === "text") {
        responseText += chunk.delta.text;
      }
    }

    if (!responseText) {
      responseText = "Sorry, I could not generate a response.";
    }

    // Store in conversation history
    history.push({ role: "user", content: userMessage });
    history.push({ role: "assistant", content: responseText });

    // Keep only last 10 messages (5 exchanges) to avoid context getting too large
    if (history.length > 10) {
      history.splice(0, history.length - 10);
    }

    conversationHistory.set(phoneNumber, history);

    console.log(
      "Anthropic response received:",
      responseText.substring(0, 100) + "..."
    );

    return responseText;
  } catch (error) {
    console.error("Error calling Anthropic API:", error);
    return "Sorry, I encountered an error processing your message. Please try again.";
  }
}

/**
 * Send a WhatsApp message via Cloud API
 */
async function sendWhatsAppMessage(to: string, text: string) {
  const url = `https://graph.facebook.com/v18.0/${process.env.WHATSAPP_PHONE_NUMBER_ID}/messages`;

  const payload = {
    messaging_product: "whatsapp",
    to: to,
    type: "text",
    text: { body: text },
  };

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.WHATSAPP_ACCESS_TOKEN}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      console.error("WhatsApp API error:", data);
      throw new Error(`WhatsApp API error: ${JSON.stringify(data)}`);
    }

    console.log("Message sent successfully:", data);
    return data;
  } catch (error) {
    console.error("Error sending WhatsApp message:", error);
    throw error;
  }
}
