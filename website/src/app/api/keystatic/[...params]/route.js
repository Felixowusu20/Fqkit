import { makeRouteHandler } from '@keystatic/next/route-handler'
import config from '../../../../../keystatic.config.mjs'

export const { GET, POST } = makeRouteHandler({ config })

export const dynamic = 'force-dynamic'
