let backgroundScroll
const owners = new Set()

function lockBackground() {
  if (backgroundScroll) return
  const html = document.documentElement
  const body = document.body
  const rect = body.getBoundingClientRect()
  const capture = (element, names) =>
    names.map((name) => [
      name,
      element.style.getPropertyValue(name),
      element.style.getPropertyPriority(name),
    ])
  backgroundScroll = {
    html,
    body,
    x: window.scrollX,
    y: window.scrollY,
    htmlStyles: capture(html, ['overflow-x', 'overflow-y', 'scroll-behavior']),
    bodyStyles: capture(body, ['position', 'top', 'left', 'width', 'overflow-x', 'overflow-y']),
  }
  html.style.setProperty('overflow-x', 'hidden')
  html.style.setProperty('overflow-y', 'hidden')
  html.style.setProperty('scroll-behavior', 'auto')
  // Freeze the existing geometry; do not add scrollbar padding on top of stable gutter.
  body.style.setProperty('position', 'fixed')
  body.style.setProperty('top', `${rect.top}px`)
  body.style.setProperty('left', `${rect.left}px`)
  body.style.setProperty('width', `${rect.width}px`)
  body.style.setProperty('overflow-x', 'hidden')
  body.style.setProperty('overflow-y', 'hidden')
}

function unlockBackground() {
  if (!backgroundScroll) return
  const state = backgroundScroll
  backgroundScroll = null
  const restore = (element, entries) =>
    entries.forEach(([name, value, priority]) => {
      if (value) element.style.setProperty(name, value, priority)
      else element.style.removeProperty(name)
    })
  restore(state.body, state.bodyStyles)
  restore(
    state.html,
    state.htmlStyles.filter(([name]) => name !== 'scroll-behavior'),
  )
  window.scrollTo({ left: state.x, top: state.y, behavior: 'instant' })
  restore(
    state.html,
    state.htmlStyles.filter(([name]) => name === 'scroll-behavior'),
  )
}

export function acquireModalPageLock() {
  const owner = Symbol('modal')
  if (!owners.size) lockBackground()
  owners.add(owner)
  return () => {
    if (!owners.delete(owner)) return
    if (!owners.size) unlockBackground()
  }
}
