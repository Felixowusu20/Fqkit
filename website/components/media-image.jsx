const SIZE = {
  xs: '40%',
  small: '55%',
  medium: '75%',
  large: '90%',
  full: '100%'
}

const ALIGN = {
  left: 'media-align-left',
  center: 'media-align-center',
  right: 'media-align-right'
}

export function Image({
  src,
  alt = '',
  caption = '',
  size = 'medium',
  align = 'center'
}) {
  if (!src) return null

  const width = SIZE[size] || SIZE.medium
  const alignClass = ALIGN[align] || ALIGN.center

  return (
    <figure
      className={`media-figure media-image ${alignClass}`}
      style={{ width, maxWidth: '100%' }}
    >
      <img src={src} alt={alt} loading="lazy" />
      {caption ? <figcaption>{caption}</figcaption> : null}
    </figure>
  )
}
