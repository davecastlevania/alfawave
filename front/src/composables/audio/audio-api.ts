import type { IAudioContext, IAudioNode } from 'standardized-audio-context'

import { AudioContext } from 'standardized-audio-context'
import { useEventListener } from '@vueuse/core'

// Audio nodes
export const AUDIO_CONTEXT = new AudioContext()
export const GAIN_NODE = AUDIO_CONTEXT.createGain()

// Unlock AudioContext automatically
const UNLOCK_EVENTS = ['touchstart', 'touchend', 'mousedown', 'keydown']
for (const event of UNLOCK_EVENTS) {
  const stop = useEventListener(window, event, () => {
    AUDIO_CONTEXT.resume()
    stop()
  }, { passive: true })
}

// Connect Gain Node
GAIN_NODE.connect(AUDIO_CONTEXT.destination)

export const setGain = (value: number) => {
  GAIN_NODE.gain.value = Math.max(0, Math.min(value, 1))
}

// TODO (wvffle): Create equalizer filters
const equalizerFilters = [
  GAIN_NODE
]

export const connectAudioSource = (sourceNode: IAudioNode<IAudioContext>) => {
  for (const filter of equalizerFilters) {
    sourceNode.connect(filter)
  }
}

export const createAudioSource = (sourceElement: HTMLAudioElement) => {
  return AUDIO_CONTEXT.createMediaElementSource(sourceElement)
}
