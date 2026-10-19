import assert from 'node:assert/strict'
import { test } from 'node:test'
import { cropGeometry, exportSectionCrop, MAX_IMAGE_BYTES } from '../src/utils/sectionImageCrop.js'

for (const [frameWidth, frameHeight] of [[823, 128], [1200, 128], [288, 144]]) {
  for (const [width, height] of [[4000, 500], [1600, 900], [1000, 1000], [600, 2000], [200, 60]]) {
    test(`crop covers frame without distortion: ${width}×${height}, frame ${frameWidth}×${frameHeight}`, () => {
      for (const zoom of [1, 2, 4]) {
        for (const [x, y] of [[0, 0], [-100000, -100000], [100000, 100000]]) {
          const result = cropGeometry(width, height, frameWidth, frameHeight, zoom, x, y)
          const tolerance = 1e-8
          assert.ok(result.left <= tolerance && result.top <= tolerance)
          assert.ok(result.left + result.width >= frameWidth - tolerance)
          assert.ok(result.top + result.height >= frameHeight - tolerance)
          assert.ok(result.sourceX >= -tolerance && result.sourceY >= -tolerance)
          assert.ok(result.sourceX + result.sourceWidth <= width + tolerance)
          assert.ok(result.sourceY + result.sourceHeight <= height + tolerance)
          assert.ok(Math.abs(result.sourceWidth / result.sourceHeight - frameWidth / frameHeight) < tolerance)
          assert.ok(Math.abs(result.width / result.height - width / height) < tolerance)
          assert.ok(Math.abs(-result.left / result.scale - result.sourceX) < tolerance)
          assert.ok(Math.abs(-result.top / result.scale - result.sourceY) < tolerance)
        }
      }
      const reset = cropGeometry(width, height, frameWidth, frameHeight)
      assert.equal(reset.x, 0)
      assert.equal(reset.y, 0)
      assert.deepEqual(reset, cropGeometry(width, height, frameWidth, frameHeight, 0))
      assert.deepEqual(cropGeometry(width, height, frameWidth, frameHeight, 10),
        cropGeometry(width, height, frameWidth, frameHeight, 4))
    })
  }
}

test('Canvas export uses exactly the preview source rectangle and no overlay', async () => {
  let drawArguments
  const canvas = {
    width: 0, height: 0,
    getContext: () => ({ drawImage: (...args) => { drawArguments = args } }),
    toBlob: (callback, type, quality) => {
      assert.equal(type, 'image/webp')
      assert.equal(quality, 0.82)
      callback(new Blob(['test'], { type }))
    },
  }
  const previousDocument = globalThis.document
  globalThis.document = { createElement: () => canvas }
  try {
    const image = { width: 1600, height: 900 }
    const geometry = cropGeometry(1600, 900, 823, 128, 1.4, 20, -50)
    await exportSectionCrop(image, geometry, 1646, 256)
    assert.equal(canvas.width, 1646)
    assert.equal(canvas.height, 256)
    assert.deepEqual(drawArguments, [image, geometry.sourceX, geometry.sourceY,
      geometry.sourceWidth, geometry.sourceHeight, 0, 0, 1646, 256])
    canvas.toBlob = (callback) => callback(null)
    await assert.rejects(exportSectionCrop(image, geometry, 1646, 256), /WebP/)
    canvas.toBlob = (callback) => callback(new Blob(['wrong type'], { type: 'image/png' }))
    await assert.rejects(exportSectionCrop(image, geometry, 1646, 256), /WebP/)
    canvas.toBlob = (callback) => callback(new Blob([new Uint8Array(MAX_IMAGE_BYTES + 1)], { type: 'image/webp' }))
    await assert.rejects(exportSectionCrop(image, geometry, 1646, 256), /5MB/)
    canvas.getContext = () => null
    await assert.rejects(exportSectionCrop(image, geometry, 1646, 256), /浏览器/)
  } finally {
    if (previousDocument === undefined) delete globalThis.document
    else globalThis.document = previousDocument
  }
})
