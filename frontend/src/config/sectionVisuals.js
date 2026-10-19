import newsImage from '../assets/home/news-masthead.png'
import toolsImage from '../assets/home/tools-masthead.png'
import { API_BASE_URL } from './api'

// Max-width desktop grid: (1200 - 40) * 2.2 / (2.2 + .9) = 823.226px.
// Rounded two-times output: 1646 × 256. This is not a fixed homepage width.
export const SECTION_VISUALS = [
  {
    key: 'home_news', title: '最新动态', navigationLabel: '全部', navigationAriaLabel: '查看全部新闻',
    description: '关注内部通知、信息宣贯及行业动态', to: '/news',
    defaultImage: newsImage, width: 823, height: 128, outputWidth: 1646, outputHeight: 256,
  },
  {
    key: 'home_tools', title: 'AI 与常用工具', navigationLabel: '全部', navigationAriaLabel: '查看全部工具',
    description: '让智能工具更自然地融入日常工作', to: '/tools',
    defaultImage: toolsImage, width: 1200, height: 128, outputWidth: 2400, outputHeight: 256,
  },
]

export function resolveSectionImage(path) {
  return typeof path === 'string' && path.startsWith('/uploads/sections/')
    ? `${API_BASE_URL}${path}` : ''
}
