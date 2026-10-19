export function shuffle(items, rng = Math.random) {
  const result = [...items]
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1))
    ;[result[i], result[j]] = [result[j], result[i]]
  }
  return result
}
export function createDiscovery(ids, preferred = null, rng = Math.random) {
  const unique = [...new Set(ids)]
  let queue = shuffle(unique, rng),
    current = null
  function select(id) {
    if (!unique.includes(id)) return current
    current = id
    queue = queue.filter((candidate) => candidate !== id)
    return current
  }
  function draw() {
    if (!unique.length) return null
    if (unique.length === 1) return select(unique[0])
    if (!queue.length) {
      queue = shuffle(unique, rng)
      if (queue[0] === current) [queue[0], queue[1]] = [queue[1], queue[0]]
    }
    current = queue.shift()
    return current
  }
  if (unique.includes(preferred)) select(preferred)
  return { draw, select, current: () => current }
}
export function selectResources(all, query) {
  const q = query.trim().toLocaleLowerCase()
  return all.filter(
    (r) =>
      !q ||
      (/^\d+$/.test(q)
        ? Number(q) === r.id
        : [r.title, r.description, ...r.tags].some((v) => v.toLocaleLowerCase().includes(q))),
  )
}
export function formatAddedDate(value) {
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value))
    return value.replace(/-/g, '.')
  return formatExchangeTimestamp(value).split(' ')[0]
}
export function formatExchangeTimestamp(value) {
  if (typeof value !== 'string' || !value.endsWith('Z')) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat('en-GB', {
      timeZone: 'Asia/Shanghai',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hourCycle: 'h23',
    })
      .formatToParts(date)
      .map((part) => [part.type, part.value]),
  )
  return `${parts.year}.${parts.month}.${parts.day} ${parts.hour}:${parts.minute}:${parts.second}`
}
export function safeUrl(value) {
  try {
    const url = new URL(value)
    return ['http:', 'https:'].includes(url.protocol) ? url.href : ''
  } catch {
    return ''
  }
}
export const EXCHANGE_CROP = Object.freeze({
  key: 'exchange-cover',
  title: '分享封面',
  width: 528,
  height: 480,
  outputWidth: 1320,
  outputHeight: 1200,
})
export const EXCHANGE_DOMAINS = ['光伏与储能', 'AI 与办公', '软件运维', '项目与管理', '工作方法']
export const EXCHANGE_TYPES = ['文章', '工具', '视频', '书籍', '工作经验']

export function validateExchangeFields(fields) {
  const title = String(fields.title || '').trim()
  const description = String(fields.description || '').trim()
  const reason = String(fields.reason || '').trim()
  const rawUrl = String(fields.externalUrl || '').trim()
  const externalUrl = rawUrl ? safeUrl(rawUrl) : ''
  if (!title || !description) throw new Error('请填写标题和内容描述，不能只输入空格。')
  if (title.length > 90 || description.length > 1500 || reason.length > 600)
    throw new Error('内容超过允许的长度，请精简后重试。')
  if (!EXCHANGE_DOMAINS.includes(fields.domain) || !EXCHANGE_TYPES.includes(fields.type))
    throw new Error('请选择有效的领域和资源类型。')
  if (rawUrl && !externalUrl) throw new Error('链接仅支持完整的 http:// 或 https:// 地址。')
  const tags = [
    ...new Set(
      String(fields.tags || '')
        .split(/[,，、]/)
        .map((tag) => tag.trim())
        .filter(Boolean),
    ),
  ]
  if (tags.length > 8 || tags.some((tag) => tag.length > 40))
    throw new Error('最多填写 8 个关键词，每个不超过 40 字。')
  return {
    title,
    description,
    reason,
    domain: fields.domain,
    type: fields.type,
    externalUrl,
    tags,
  }
}
