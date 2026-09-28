const CLASSES = {
  default:
    'x:bg-green-100 x:dark:bg-green-900/30 x:text-green-700 x:dark:text-green-500 x:border-green-700 x:dark:border-green-800',
  error:
    'x:bg-red-100 x:dark:bg-red-900/30 x:text-red-700 x:dark:text-red-500 x:border-red-600 x:dark:border-red-600',
  info: 'x:bg-blue-100 x:dark:bg-blue-900/30 x:text-blue-700 x:dark:text-blue-400 x:border-blue-700 x:dark:border-blue-600',
  warning:
    'x:bg-yellow-50 x:dark:bg-yellow-700/30 x:text-yellow-700 x:dark:text-yellow-500 x:border-yellow-700',
  important:
    'x:bg-purple-50 x:dark:bg-purple-900/30 x:text-purple-600 x:dark:text-purple-400 x:border-purple-600'
}

const EMOJI = {
  default: '💡',
  error: '🛑',
  info: 'ℹ️',
  warning: '⚠️',
  important: '❗'
}

const EMOJI_STYLE = {
  fontFamily: '"Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"'
}

export function Callout({
  type = 'default',
  emoji,
  className = '',
  children,
  ...props
}) {
  return (
    <div
      className={`nextra-callout x:overflow-x-auto x:not-first:mt-[1.25em] x:flex x:rounded-lg x:border x:py-[.5em] x:pe-[1em] x:contrast-more:border-current! ${CLASSES[type] || ''}`}
    >
      <div
        className="x:select-none x:text-[1.25em] x:ps-[.6em] x:pe-[.4em]"
        style={EMOJI_STYLE}
        data-pagefind-ignore="all"
      >
        {emoji ?? EMOJI[type]}
      </div>
      <div className={`x:w-full x:min-w-0 ${className}`} {...props}>
        {children}
      </div>
    </div>
  )
}
