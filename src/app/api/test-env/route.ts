import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    hasToken: !!process.env.WHATSAPP_WEBHOOK_VERIFY_TOKEN,
    tokenLength: process.env.WHATSAPP_WEBHOOK_VERIFY_TOKEN?.length || 0,
    // Only show first and last 3 chars for security
    tokenPreview: process.env.WHATSAPP_WEBHOOK_VERIFY_TOKEN
      ? process.env.WHATSAPP_WEBHOOK_VERIFY_TOKEN.substring(0, 3) + '...' + process.env.WHATSAPP_WEBHOOK_VERIFY_TOKEN.slice(-3)
      : 'NOT SET',
    allEnvVars: Object.keys(process.env).filter(key => key.startsWith('WHATSAPP_'))
  });
}
