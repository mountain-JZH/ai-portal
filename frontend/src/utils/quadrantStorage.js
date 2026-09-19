export const QUADRANT_STORAGE_KEY = 'ai-portal-quadrant-v1'
export const QUADRANT_UPDATED_EVENT = 'ai-portal-quadrants-updated'
export const QUADRANT_STATUS_COLORS = {
  empty: '#8B95A7',
  completed: '#4FA879',
}

export const QUADRANTS = [
  {
    key: 'important_urgent',
    label: '重要 · 紧急',
    color: '#D95C5C',
    symbolType: 'triangle',
    description: '优先处理',
    symbolPosition: 'bottom-right',
  },
  {
    key: 'important_not_urgent',
    label: '重要 · 不紧急',
    color: '#D59A32',
    symbolType: 'circle',
    description: '计划推进',
    symbolPosition: 'bottom-left',
  },
  {
    key: 'not_important_urgent',
    label: '不重要 · 紧急',
    color: '#4D7ED9',
    symbolType: 'square',
    description: '及时响应',
    symbolPosition: 'top-right',
  },
  {
    key: 'not_important_not_urgent',
    label: '不重要 · 不紧急',
    color: '#4FA879',
    symbolType: 'diamond',
    description: '灵活安排',
    symbolPosition: 'top-left',
  },
]

const QUADRANT_KEYS = new Set(QUADRANTS.map((quadrant) => quadrant.key))

export function sanitizeQuadrantStore(value, todosByDate = {}) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {}

  return Object.fromEntries(
    Object.entries(value).flatMap(([dateKey, mapping]) => {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(dateKey) || !mapping || typeof mapping !== 'object') {
        return []
      }

      const validIds = new Set((todosByDate[dateKey] || []).map((todo) => String(todo.id)))
      const validMapping = Object.fromEntries(
        Object.entries(mapping).filter(
          ([todoId, quadrantKey]) => validIds.has(String(todoId)) && QUADRANT_KEYS.has(quadrantKey),
        ),
      )

      return Object.keys(validMapping).length ? [[dateKey, validMapping]] : []
    }),
  )
}

export function readQuadrantStore(todosByDate = {}) {
  try {
    const storedMappings = localStorage.getItem(QUADRANT_STORAGE_KEY)
    return storedMappings
      ? sanitizeQuadrantStore(JSON.parse(storedMappings), todosByDate)
      : {}
  } catch {
    return {}
  }
}

export function notifyQuadrantsUpdated(mappings) {
  window.dispatchEvent(
    new CustomEvent(QUADRANT_UPDATED_EVENT, {
      detail: { mappings },
    }),
  )
}

export function writeQuadrantStore(mappings) {
  let saved = true

  try {
    localStorage.setItem(QUADRANT_STORAGE_KEY, JSON.stringify(mappings))
  } catch {
    saved = false
  }

  notifyQuadrantsUpdated(mappings)
  return saved
}
