<script setup>
import { onMounted, onUnmounted } from 'vue'

const DIFY_TOKEN = 'vifzPa2WJoioiZsz'
const DIFY_BASE_URL = 'https://dify-app.crc.com.cn'
const DIFY_SCRIPT_URL = `${DIFY_BASE_URL}/embed.min.js`

let difyScript = null
let isMounted = false

function removeDifyElements() {
  document
    .getElementById('dify-chatbot-bubble-button')
    ?.remove()

  document
    .getElementById('dify-chatbot-bubble-window')
    ?.remove()
}

onMounted(() => {
  isMounted = true

  window.difyChatbotConfig = {
    token: DIFY_TOKEN,
    baseUrl: DIFY_BASE_URL,
    inputs: {},
    systemVariables: {},
    userVariables: {},
  }

  const existingScript =
    document.getElementById(DIFY_TOKEN) ||
    Array.from(document.scripts).find(
      (script) => script.src === DIFY_SCRIPT_URL,
    )

  const existingBubble = document.getElementById(
    'dify-chatbot-bubble-button',
  )

  if (existingScript || existingBubble) {
    return
  }

  difyScript = document.createElement('script')

  difyScript.src = DIFY_SCRIPT_URL
  difyScript.id = DIFY_TOKEN
  difyScript.defer = true

  difyScript.addEventListener('load', () => {
    if (!isMounted) {
      removeDifyElements()
    }
  })

  document.body.appendChild(difyScript)
})

onUnmounted(() => {
  isMounted = false

  difyScript?.remove()
  difyScript = null

  removeDifyElements()
  delete window.difyChatbotConfig
})
</script>

<template>
  <div></div>
</template>

<style>
#dify-chatbot-bubble-button {
  background: linear-gradient(145deg, #4f7cff, #655ce7) !important;
  box-shadow:
    0 10px 26px rgba(76, 85, 170, 0.24),
    inset 0 1px 0 rgba(255, 255, 255, 0.28) !important;
}

#dify-chatbot-bubble-window {
  width: 24rem !important;
  height: 40rem !important;
  max-width: calc(100vw - 2rem) !important;
  max-height: calc(100vh - 6rem) !important;
}
</style>


