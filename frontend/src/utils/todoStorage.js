export const TODO_STORAGE_KEY = 'ai-portal-todos-v1'
export const TODO_UPDATED_EVENT = 'ai-portal-todos-updated'
const DATE_KEY_PATTERN = /^\d{4}-\d{2}-\d{2}$/

export function getLocalDateKey(date = new Date()) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function sanitizeTodoStore(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {}

  return Object.fromEntries(
    Object.entries(value).flatMap(([dateKey, todos]) => {
      if (!DATE_KEY_PATTERN.test(dateKey) || !Array.isArray(todos)) return []

      const validTodos = todos.flatMap((todo, index) => {
        if (!todo || typeof todo !== 'object' || typeof todo.text !== 'string') return []

        const text = todo.text.trim().slice(0, 60)
        if (!text) return []

        return [
          {
            id: String(todo.id ?? `${dateKey}-${index}`),
            text,
            done: Boolean(todo.done),
          },
        ]
      })

      return validTodos.length ? [[dateKey, validTodos]] : []
    }),
  )
}

export function rollOverUnfinishedTodos(value, todayKey = getLocalDateKey()) {
  const todosByDate = sanitizeTodoStore(value)
  if (!DATE_KEY_PATTERN.test(todayKey)) {
    return { todos: todosByDate, changed: false }
  }

  const nextTodosByDate = {}
  const overdueTodos = []

  Object.entries(todosByDate).forEach(([dateKey, todos]) => {
      if (dateKey >= todayKey) {
        nextTodosByDate[dateKey] = todos
        return
      }

      const completedTodos = todos.filter((todo) => todo.done)
      const unfinishedTodos = todos.filter((todo) => !todo.done)

      if (completedTodos.length) nextTodosByDate[dateKey] = completedTodos
      overdueTodos.push(...unfinishedTodos)
  })

  if (!overdueTodos.length) {
    return { todos: nextTodosByDate, changed: false }
  }

  nextTodosByDate[todayKey] = [
    ...overdueTodos,
    ...(nextTodosByDate[todayKey] || []),
  ]

  return { todos: nextTodosByDate, changed: true }
}

export function readTodoStore() {
  let storedTodos

  try {
    storedTodos = localStorage.getItem(TODO_STORAGE_KEY)
  } catch {
    return {}
  }

  if (!storedTodos) return {}

  let parsedTodos
  try {
    parsedTodos = JSON.parse(storedTodos)
  } catch {
    return {}
  }

  const { todos, changed } = rollOverUnfinishedTodos(parsedTodos)

  if (changed) {
    try {
      localStorage.setItem(TODO_STORAGE_KEY, JSON.stringify(todos))
    } catch {
      // The normalized in-memory data remains usable when local storage is unavailable.
    }
  }

  return todos
}

export function notifyTodosUpdated(todos) {
  window.dispatchEvent(
    new CustomEvent(TODO_UPDATED_EVENT, {
      detail: { todos: sanitizeTodoStore(todos) },
    }),
  )
}
