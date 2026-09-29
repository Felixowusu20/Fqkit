'use client'

const STORAGE_KEY = 'fqkit-banner'

function dismiss(event) {
  event.currentTarget.closest('.fqkit-banner')?.setAttribute('hidden', '')
  document.documentElement.setAttribute('data-banner', 'off')
  try {
    localStorage.setItem(STORAGE_KEY, '1')
  } catch {
    // Private browsing can block storage. The banner still closes for this visit.
  }
}

export function SiteBanner({ children }) {
  return (
    <div className="nextra-banner fqkit-banner x:max-md:sticky x:top-0 x:z-30 x:flex x:items-center x:px-2 x:text-slate-50 x:dark:text-white x:bg-neutral-900 x:dark:bg-[linear-gradient(1deg,#383838,#212121)] x:print:[display:none]">
      <div className="x:w-full x:text-center x:font-medium x:text-sm x:py-2.5">
        {children}
      </div>
      <button
        type="button"
        className="fqkit-banner-close"
        aria-label="Dismiss banner"
        onClick={dismiss}
      >
        ×
      </button>
    </div>
  )
}
