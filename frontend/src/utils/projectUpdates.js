const dayFormatter = new Intl.DateTimeFormat('en-CA', {
  timeZone: 'Asia/Shanghai',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
})

export function beijingDay(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return null
  const parts = Object.fromEntries(
    dayFormatter.formatToParts(date).map(({ type, value }) => [type, value]),
  )
  return {
    year: parts.year,
    month: Number(parts.month),
    day: Number(parts.day),
    key: `${parts.year}-${parts.month}-${parts.day}`,
  }
}

export function projectUpdateLabel(value, now = new Date()) {
  if (!value) return ''
  const date = beijingDay(value),
    today = beijingDay(now)
  if (!date || !today) return ''
  if (date.key === today.key) return '今日更新'
  return `${date.year === today.year ? '' : date.year + '年'}${date.month}月${date.day}日更新`
}
