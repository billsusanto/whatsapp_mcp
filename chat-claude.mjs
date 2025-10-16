/**
 * Interactive Claude Agent SDK CLI
 * Run with: node chat-claude.mjs
 */

import { query } from '@anthropic-ai/claude-agent-sdk';
import dotenv from 'dotenv';
import readline from 'readline';

// Load environment variables
dotenv.config();

// Session storage
let sessionId = null;

// Create readline interface
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

console.log('🤖 Claude Agent SDK - Interactive Chat');
console.log('=====================================');
console.log('Type your messages and press Enter.');
console.log('Type "exit" or "quit" to end the session.\n');

async function chat(userMessage) {
  try {
    const result = query({
      prompt: userMessage,
      options: {
        model: 'claude-3-5-sonnet-20241022',
        systemPrompt: 'You are a helpful assistant. Keep responses concise and friendly.',
        maxTurns: 5,
        executable: '/usr/local/bin/node',
        env: {
          ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY || '',
        },
        // Resume previous session for conversation continuity
        ...(sessionId && { resume: sessionId }),
      },
    });

    let responseText = '';

    for await (const message of result) {
      if (message.type === 'system') {
        sessionId = message.session_id;
        console.log(`\n[Session: ${sessionId.substring(0, 8)}...]`);
      } else if (message.type === 'assistant') {
        const content = message.message.content;
        for (const block of content) {
          if (block.type === 'text') {
            responseText += block.text;
          }
        }
      } else if (message.type === 'result') {
        console.log(`[Cost: $${message.total_cost_usd.toFixed(6)} | Tokens: ${message.usage.output_tokens}]`);
      }
    }

    console.log('\n🤖 Claude:', responseText);

  } catch (error) {
    console.error('\n❌ Error:', error.message);
  }
}

function prompt() {
  rl.question('\n💬 You: ', async (input) => {
    const message = input.trim();

    if (!message) {
      prompt();
      return;
    }

    if (message.toLowerCase() === 'exit' || message.toLowerCase() === 'quit') {
      console.log('\n👋 Goodbye!');
      rl.close();
      process.exit(0);
    }

    await chat(message);
    prompt();
  });
}

// Start the interactive chat
prompt();
