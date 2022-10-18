import type { IAudioContext, IAudioNode } from 'standardized-audio-context'

import { createAudioSource } from '~/composables/audio/audio-api'
import { reactive, ref, type Ref } from 'vue'
import { createEventHook, refDefault, type EventHookOn } from '@vueuse/shared'
import { useEventListener } from '@vueuse/core'

export interface SoundSource {
  uuid: string
  mimetype: string
  url: string
}

export interface Sound {
  preload(): void | Promise<void>
  dispose(): void

  readonly audioNode: IAudioNode<IAudioContext>
  readonly isLoaded: Ref<boolean>
  readonly currentTime: number
  readonly duration: number
  readonly buffered: number

  play(): void | Promise<void>
  pause(): void | Promise<void>

  seekTo(seconds: number): void | Promise<void>
  seekBy(seconds: number): void | Promise<void>

  onSoundEnd: EventHookOn<Sound>
}

export const soundImplementations = reactive(new Set<Constructor<Sound>>())

export const registerSoundImplementation = <T extends Constructor<Sound>>(implementation: T) => {
  soundImplementations.add(implementation)
  return implementation
}

// Default Sound implementation
@registerSoundImplementation
export class HTMLSound implements Sound {
  #audio = new Audio()
  #soundEndEventHook = createEventHook<HTMLSound>()

  readonly isLoaded = ref(false)

  audioNode = createAudioSource(this.#audio)
  onSoundEnd: EventHookOn<HTMLSound>

  constructor (sources: SoundSource[]) {
    // TODO: Quality picker
    this.#audio.src = sources[0].url
    this.#audio.preload = 'auto'

    useEventListener(this.#audio, 'ended', () => this.#soundEndEventHook.trigger(this))
    useEventListener(this.#audio, 'loadeddata', () => {
      // https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/readyState
      this.isLoaded.value = this.#audio.readyState >= 2
    })

    this.onSoundEnd = this.#soundEndEventHook.on
  }

  preload () {
    this.#audio.load()
  }

  dispose () {
    this.audioNode.disconnect()
  }

  async play () {
    this.#audio.play()
  }

  async pause () {
    this.#audio.pause()
  }

  async seekTo (seconds: number) {
    this.#audio.currentTime = seconds
  }

  async seekBy (seconds: number) {
    this.#audio.currentTime += seconds
  }

  get duration () {
    const { duration } = this.#audio
    return isNaN(duration) ? 0 : duration
  }

  get buffered () {
    // https://developer.mozilla.org/en-US/docs/Web/Guide/Audio_and_video_delivery/buffering_seeking_time_ranges#creating_our_own_buffering_feedback
    if (this.duration > 0) {
      const { length } = this.#audio.buffered
      for (let i = 0; i < length; i++) {
        if (this.#audio.buffered.start(length - 1 - i) < this.#audio.currentTime) {
          return this.#audio.buffered.end(length - 1 - i)
        }
      }
    }

    return 0
  }

  get currentTime () {
    return this.#audio.currentTime
  }
}

export const soundImplementation = refDefault(ref<Constructor<Sound>>(), HTMLSound)
