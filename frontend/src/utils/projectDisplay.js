export const stageTone = (status) =>
  status === '已完成' ? 'done' : status === '进行中' ? 'active' : status ? 'other' : 'blank'
export const displayValue = (value) =>
  value == null || String(value).trim() === '' ? '未填写' : String(value)
export function importTime(value) {
  if (!value) return '尚未导入'
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? '时间不可用'
    : new Intl.DateTimeFormat('zh-CN', {
        timeZone: 'Asia/Shanghai',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      }).format(date)
}
export function scaleValue(value, unit) {
  if (value == null) return '未填写'
  return /^[-+]?\d+(\.\d+)?$/.test(String(value).trim()) && unit
    ? `${value} ${unit}`
    : String(value)
}
