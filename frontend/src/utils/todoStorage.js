export const TODO_STORAGE_KEY = 'ai-portal-todos-v1'
export const TODO_UPDATED_EVENT = 'ai-portal-todos-updated'

export function sanitizeTodoStore(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {}

  return Object.fromEntries(
    Object.entries(value).flatMap(([dateKey, todos]) => {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(dateKey) || !Array.isArray(todos)) return []

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

export function readTodoStore() {
  try {
    const storedTodos = localStorage.getItem(TODO_STORAGE_KEY)
    return storedTodos ? sanitizeTodoStore(JSON.parse(storedTodos)) : {}
  } catch {
    return {}
  }
}

export function notifyTodosUpdated(todos) {
  window.dispatchEvent(
    new CustomEvent(TODO_UPDATED_EVENT, {
      detail: { todos: sanitizeTodoStore(todos) },
    }),
  )
}
