import { createElement } from 'react'

export function FqkitMark({ colorScheme }) {
  const onDark = colorScheme === 'dark'
  const ink = onDark ? '#f4f1ea' : '#171717'
  const shade = onDark ? '#8d887f' : '#6f6b64'
  return createElement(
    'svg',
    {
      className: 'fqkit-mark',
      width: 36,
      height: 36,
      viewBox: '-1 -1 34 34',
      'aria-hidden': 'true'
    },
    createElement(
      'g',
      { className: 'fqkit-mark-bolt' },
      createElement('path', {
        d: 'M18 8L14 24L12 32L30 14L18 8Z',
        fill: ink
      }),
      createElement('path', {
        d: 'M2 18L20 0L18 8L2 18Z',
        fill: ink
      }),
      createElement('path', {
        className: 'fqkit-mark-shade',
        d: 'M18 8L2 18L14 24L18 8Z',
        fill: shade
      })
    )
  )
}
