/**
 * Test script for Claude Agent SDK
 * Run with: node test-claude-sdk.js
 */

import { query } from '@anthropic-ai/claude-agent-sdk';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function testClaudeSDK() {
  console.log('🧪 Testing Claude Agent SDK...\n');

  try {
    const result = query({
      prompt: 'Say hello and tell me what you are',
      options: {
        model: 'claude-3-5-sonnet-20241022',
        systemPrompt: 'You are a helpful assistant.',
        maxTurns: 1,
        executable: '/usr/local/bin/node', // Explicit path to node
        env: {
          ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY || '',
        },
      },
    });

    let responseText = '';
    let sessionId = '';

    console.log('📡 Streaming messages...\n');

    for await (const message of result) {
      console.log('Message type:', message.type);

      if (message.type === 'system') {
        sessionId = message.session_id;
        console.log('  Session ID:', sessionId);
      } else if (message.type === 'assistant') {
        const content = message.message.content;
        for (const block of content) {
          if (block.type === 'text') {
            responseText += block.text;
            console.log('  Text block:', block.text.substring(0, 50) + '...');
          }
        }
      } else if (message.type === 'result') {
        console.log('  Cost:', message.total_cost_usd);
        console.log('  Tokens:', message.usage);
      }
    }

    console.log('\n✅ Test completed successfully!\n');
    console.log('Full response:\n', responseText);

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.error('Full error:', error);
  }
}

testClaudeSDK();
