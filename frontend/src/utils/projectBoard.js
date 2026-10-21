import { displayValue } from './projectDisplay.js'
import { firstActiveNode } from './projectNodes.js'

export const businessGroups = [
  {
    name: '光伏',
    fields: [
      ['pvArea', '预计可利用面积（㎡）'],
      ['pvCapacity', '预计装机规模（MW）'],
    ],
  },
  { name: '储能', fields: [['storageCapacity', '预计装机容量（原表数值 / 单位）']] },
  { name: '充电桩', fields: [['chargingScale', '预计规模']] },
  {
    name: '分布式能源',
    fields: [
      ['energyType', '类型'],
      ['energyScale', '规模 / 方案'],
    ],
  },
]

// Display-only: never rewrite the raw import value or guess a missing unit.
export function metricValue(value) {
  if (value == null || String(value).trim() === '') return displayValue(value)
  const raw = String(value).trim()
  if (!/^[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?$/i.test(raw)) return raw
  const number = Number(raw)
  if (!Number.isFinite(number) || Math.abs(number) > Number.MAX_SAFE_INTEGER) return raw
  return new Intl.NumberFormat('en-US', {
    useGrouping: false,
    maximumSignificantDigits: 12,
  }).format(number)
}

export function currentPosition(project, stages) {
  const active = firstActiveNode(project.stages)
  if (active >= 0) return active + 1
  const stage = String(project.currentStage || '')
    .trim()
    .replace(/[&＆]/g, '与')
  const exact = stages.indexOf(stage)
  return exact >= 0 ? exact + 1 : null
}

export function groupsFor(project) {
  return businessGroups.filter((group) => (project.businessTypes || []).includes(group.name))
}

export function currentStageName(project, stages) {
  const active = firstActiveNode(project.stages)
  return active >= 0 ? stages[active] : project.currentStage
}

export const businessLabel = (name) => (name === '光伏' ? '分布式光伏' : name)
export const shortStages = [
  '客户对接',
  '实地勘察',
  '资料方案',
  '商务洽谈',
  '可研编制',
  '项目审批',
  '合同签约',
  '项目备案',
  '招标',
  '施工',
  '竣工投运',
]

// Display-only V2.8 metrics; narratives and original values are never rewritten.
export function businessPresentation(project, group) {
  const kpis = [],
    descriptions = []
  for (const [field, label] of group.fields) {
    const raw = project[field]
    if (raw == null || ['', '/', '／', '-', '—', '未填写'].includes(String(raw).trim())) continue
    if (field === 'energyType') continue
    const match = String(raw)
      .trim()
      .match(/^([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)\s*(㎡|m²|MW|MWh|KW|kW|台|套)?$/i)
    if (
      match &&
      Number.isFinite(Number(match[1])) &&
      Math.abs(Number(match[1])) <= Number.MAX_SAFE_INTEGER
    ) {
      kpis.push({
        label: label.replace(/^预计/, '').replace(/（.*?）/g, ''),
        number: new Intl.NumberFormat('zh-CN', { maximumSignificantDigits: 15 }).format(
          Number(match[1]),
        ),
        unit: match[2] || (field === 'pvArea' ? '㎡' : field === 'pvCapacity' ? 'MW' : ''),
      })
    } else {
      descriptions.push({
        label: field === 'energyScale' ? '业务方案 / 原表规模' : label,
        value: String(raw),
      })
      if (field === 'energyScale') {
        const rate = String(raw).match(/节能率(?:达|达到|约|为)?\s*(\d+(?:\.\d+)?)\s*%/)
        const saving = String(raw).match(
          /(年)?(?:节约电费|节省电费|节电费)\s*(约)?\s*(\d+(?:\.\d+)?)\s*万元/,
        )
        if (rate) kpis.push({ label: '节能率（预计）', number: rate[1], unit: '%' })
        if (saving)
          kpis.push({
            label: saving[1] ? '年节约电费' : '节约电费（约）',
            number: saving[3],
            unit: '万元',
          })
      }
    }
  }
  return {
    kpis,
    descriptions,
    classification: group.name === '分布式能源' ? project.energyType : null,
  }
}
