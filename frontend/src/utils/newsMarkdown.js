import MarkdownIt from 'markdown-it'
import { h } from 'vue'

const parser = new MarkdownIt({ html: false, linkify: false, typographer: false })
parser.disable(['image', 'table'])
const tags = new Set(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'em', 'ol', 'ul', 'li', 'blockquote', 's'])

export function safeNewsLink(value) {
  try {
    const url = new URL(value)
    return ['https:', 'http:'].includes(url.protocol) ? url.href : null
  } catch {
    return null
  }
}

// Never render parser-generated HTML or copy arbitrary token attributes to the DOM.
export function markdownNodes(content, title = '') {
  const tokens = parser.parse(String(content || ''), {})
  if (tokens[0]?.type === 'heading_open' && tokens[0].tag === 'h1' &&
      tokens[1]?.type === 'inline' && tokens[2]?.type === 'heading_close') {
    const text = (tokens[1].children || []).map(t => t.content).join('').trim()
    if (title.trim() && text === title.trim()) tokens.splice(0, 3)
  }
  function render(list) {
    const root = []
    const stack = [{ children: root }]
    for (const token of list) {
      const current = () => stack[stack.length - 1].children
      if (token.type === 'inline') current().push(...render(token.children || []))
      else if (token.nesting === 1) {
        const props = {}
        let tag = tags.has(token.tag) ? token.tag : 'span'
        if (token.type === 'link_open') {
          const href = safeNewsLink(token.attrGet('href'))
          tag = href ? 'a' : 'span'
          if (href) Object.assign(props, { href, target: '_blank', rel: 'noopener noreferrer' })
        }
        if (tag === 'ol' && /^\d+$/.test(token.attrGet('start') || '')) props.start = Number(token.attrGet('start'))
        stack.push({ tag, props, children: [] })
      } else if (token.nesting === -1 && stack.length > 1) {
        const node = stack.pop()
        current().push(h(node.tag, node.props, node.children))
      } else if (token.type === 'hr') current().push(h('hr'))
      else if (token.type === 'hardbreak') current().push(h('br'))
      else if (token.type === 'softbreak') current().push('\n')
      else if (token.type === 'code_inline') current().push(h('code', token.content))
      else if (['fence', 'code_block'].includes(token.type)) current().push(h('pre', [h('code', token.content)]))
      else current().push(token.content || '')
    }
    return root
  }
  return render(tokens)
}
