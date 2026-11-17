// Display labels only; API and stored source_type values remain unchanged.
export function getNewsTypeLabel(sourceType) {
  return sourceType === '新能源行业早报' ? '行业报告' : sourceType
}
