import { makeRouteHandler } from '@keystatic/next/route-handler'
import config from '../../../../../keystatic.config.mjs'

export const dynamic = 'force-dynamic'
export const runtime = 'nodejs'

// Keystatic reads the GitHub secrets when the handler is created. On Vercel those
// secrets are for requests, not the build, so creating the handler at import time
// fails the build. Create it on the first request instead.
let handlers

function getHandlers() {
  if (!handlers) {
    handlers = makeRouteHandler({ config })
  }
  return handlers
}

export async function GET(request) {
  return getHandlers().GET(request)
}

export async function POST(request) {
  return getHandlers().POST(request)
}
