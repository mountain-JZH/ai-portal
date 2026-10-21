// Exact states only: legacy free text is never normalized on read.
export const firstActiveNode = (nodes = []) => nodes.findIndex((value) => value === '进行中')

export function nextNodeStatus(value) {
  return value === '进行中' ? '已完成' : value === '已完成' ? null : '进行中'
}

export function nodeDraftStage(nodes, baseline, originalStage, names) {
  if (JSON.stringify(nodes) === JSON.stringify(baseline)) return originalStage
  const index = firstActiveNode(nodes)
  return index < 0 ? originalStage : names[index].replace(/[&＆]/g, '与')
}
