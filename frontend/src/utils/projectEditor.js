export const projectFields = [
  ['name', '项目名称'],
  ['resource', '资源名称 / 来源'],
  ['leader', '项目组长'],
  ['owner', '项目负责人'],
  ['management', '管理权'],
  ['ownership', '资产所有权'],
  ['priority', '开发时序评级'],
  ['valueRating', '开发价值评级'],
  ['customerType', '客户性质'],
  ['district', '所属行政片区'],
  ['pvArea', '光伏可利用面积（㎡）'],
  ['pvCapacity', '光伏预计装机规模（MW）'],
  ['storageCapacity', '储能预计装机容量（请保留原始单位/描述）'],
  ['chargingScale', '充电桩预计规模'],
  ['energyType', '分布式能源类型'],
  ['energyScale', '分布式能源规模 / 方案'],
  ['currentStage', '目前所处阶段'],
  ['situation', '当前实施情况'],
  ['nextStep', '下一步打算'],
  ['coordination', '需上级协调事项'],
]
export const editorStages = [
  '客户对接',
  '实地勘察',
  '资料收集&方案设计',
  '商务洽谈',
  '可研编制',
  '项目审批',
  '合同签约',
  '项目备案',
  '招标',
  '施工',
  '竣工投运',
]
export function editableProject(project = {}) {
  return {
    ...Object.fromEntries(projectFields.map(([field]) => [field, project[field] ?? null])),
    stages: project.stages ? [...project.stages] : Array(11).fill(null),
  }
}
export function projectChanges(form, original) {
  return Object.fromEntries(
    Object.entries(form).filter(
      ([key, value]) => JSON.stringify(value) !== JSON.stringify(original[key]),
    ),
  )
}
