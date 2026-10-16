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

/** Turn a YouTube / Vimeo watch URL into an embeddable iframe src. */
export function toEmbedSrc(url) {
  if (!url) return null
  const trimmed = String(url).trim()
  if (!trimmed) return null

  try {
    const u = new URL(trimmed)
    const host = u.hostname.replace(/^www\./, '')

    if (host === 'youtu.be') {
      const id = u.pathname.slice(1).split('/')[0]
      return id ? `https://www.youtube.com/embed/${id}` : null
    }

    if (host === 'youtube.com' || host === 'm.youtube.com' || host === 'youtube-nocookie.com') {
      if (u.pathname.startsWith('/embed/')) return trimmed
      const id = u.searchParams.get('v')
      if (id) return `https://www.youtube.com/embed/${id}`
      const shorts = u.pathname.match(/^\/shorts\/([^/]+)/)
      if (shorts) return `https://www.youtube.com/embed/${shorts[1]}`
      return null
    }

    if (host === 'vimeo.com') {
      const id = u.pathname.split('/').filter(Boolean)[0]
      return id && /^\d+$/.test(id) ? `https://player.vimeo.com/video/${id}` : null
    }

    if (host === 'player.vimeo.com') return trimmed
  } catch {
    // Not an absolute URL — treat as a site path below.
  }

  return null
}

function isDirectVideo(src) {
  if (!src) return false
  if (src.startsWith('/')) return true
  return /\.(mp4|webm|ogg)(\?|$)/i.test(src)
}

export function Video({
  url = '',
  src = '',
  caption = '',
  size = 'medium',
  align = 'center',
  controls = true
}) {
  const fileOrPath = src || ''
  const embed = toEmbedSrc(url)
  const direct = isDirectVideo(fileOrPath)
    ? fileOrPath
    : !embed && isDirectVideo(url)
      ? url
      : null

  if (!embed && !direct) return null

  const width = SIZE[size] || SIZE.medium
  const alignClass = ALIGN[align] || ALIGN.center

  return (
    <figure
      className={`media-figure media-video ${alignClass}`}
      style={{ width, maxWidth: '100%' }}
    >
      {embed ? (
        <div className="media-video-frame">
          <iframe
            src={embed}
            title={caption || 'Embedded video'}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            allowFullScreen
            loading="lazy"
          />
        </div>
      ) : (
        <video className="media-video-file" src={direct} controls={controls} playsInline />
      )}
      {caption ? <figcaption>{caption}</figcaption> : null}
    </figure>
  )
}
