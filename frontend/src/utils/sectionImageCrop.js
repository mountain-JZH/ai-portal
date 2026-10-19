export const MAX_IMAGE_BYTES = 5 * 1024 * 1024
export const IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']

export function cropGeometry(imageWidth, imageHeight, frameWidth, frameHeight, zoom = 1, x = 0, y = 0) {
  const scale = Math.max(frameWidth / imageWidth, frameHeight / imageHeight) * Math.min(4, Math.max(1, zoom))
  const width = imageWidth * scale
  const height = imageHeight * scale
  const limitX = Math.max(0, (width - frameWidth) / 2)
  const limitY = Math.max(0, (height - frameHeight) / 2)
  const offsetX = Math.min(limitX, Math.max(-limitX, x))
  const offsetY = Math.min(limitY, Math.max(-limitY, y))
  return {
    scale, width, height, x: offsetX, y: offsetY,
    left: (frameWidth - width) / 2 + offsetX,
    top: (frameHeight - height) / 2 + offsetY,
    sourceX: ((width - frameWidth) / 2 - offsetX) / scale,
    sourceY: ((height - frameHeight) / 2 - offsetY) / scale,
    sourceWidth: frameWidth / scale, sourceHeight: frameHeight / scale,
  }
}

export async function exportSectionCrop(image, geometry, width, height) {
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const context = canvas.getContext('2d')
  if (!context) throw new Error('当前浏览器无法处理图片，请更换浏览器重试')
  context.drawImage(image, geometry.sourceX, geometry.sourceY,
    geometry.sourceWidth, geometry.sourceHeight, 0, 0, width, height)
  const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/webp', 0.82))
  if (!blob || blob.type !== 'image/webp') throw new Error('无法导出 WebP，请更换浏览器重试')
  if (blob.size > MAX_IMAGE_BYTES) throw new Error('裁剪结果超过 5MB，请更换图片或重新取景')
  return blob
}
