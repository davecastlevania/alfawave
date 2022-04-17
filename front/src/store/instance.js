import axios from 'axios'
import logger from '@/logging'
import { merge } from 'lodash-es'

function getDefaultUrl () {
  return (
    window.location.protocol + '//' + window.location.hostname +
    (window.location.port ? ':' + window.location.port : '') + '/'
  )
}

function notifyServiceWorker (registration, message) {
  if (registration && registration.active) {
    registration.active.postMessage(message)
  }
}

export default {
  namespaced: true,
  state: {
    maxEvents: 200,
    frontSettings: {},
    instanceUrl: import.meta.env.VUE_APP_INSTANCE_URL,
    events: [],
    knownInstances: [],
    nodeinfo: null,
    settings: {
      instance: {
        name: {
          value: ''
        },
        short_description: {
          value: ''
        },
        long_description: {
          value: ''
        },
        funkwhale_support_message_enabled: {
          value: true
        },
        support_message: {
          value: ''
        }
      },
      users: {
        registration_enabled: {
          value: true
        },
        upload_quota: {
          value: 0
        }
      },
      moderation: {
        signup_approval_enabled: {
          value: false
        },
        signup_form_customization: { value: null }
      },
      subsonic: {
        enabled: {
          value: true
        }
      }
    }
  },
  mutations: {
    settings: (state, value) => {
      merge(state.settings, value)
    },
    event: (state, value) => {
      state.events.unshift(value)
      if (state.events.length > state.maxEvents) {
        state.events = state.events.slice(0, state.maxEvents)
      }
    },
    events: (state, value) => {
      state.events = value
    },
    nodeinfo: (state, value) => {
      state.nodeinfo = value
    },
    frontSettings: (state, value) => {
      state.frontSettings = value
    },
    instanceUrl: (state, value) => {
      if (value && !value.endsWith('/')) {
        value = value + '/'
      }
      state.instanceUrl = value
      notifyServiceWorker(state.registration, { command: 'serverChosen', serverUrl: state.instanceUrl })
      // append the URL to the list (and remove existing one if needed)
      if (value) {
        const index = state.knownInstances.indexOf(value)
        if (index > -1) {
          state.knownInstances.splice(index, 1)
        }
        state.knownInstances.splice(0, 0, value)
      }
      if (!value) {
        axios.defaults.baseURL = null
        return
      }
      const suffix = 'api/v1/'
      axios.defaults.baseURL = state.instanceUrl + suffix
    }
  },
  getters: {
    defaultUrl: (state) => () => {
      return getDefaultUrl()
    },
    absoluteUrl: (state) => (relativeUrl) => {
      if (relativeUrl.startsWith('http')) {
        return relativeUrl
      }
      if (state.instanceUrl?.endsWith('/') && relativeUrl.startsWith('/')) {
        relativeUrl = relativeUrl.slice(1)
      }

      const instanceUrl = state.instanceUrl ?? getDefaultUrl()
      return instanceUrl + relativeUrl
    },
    domain: (state) => {
      const url = state.instanceUrl
      const parser = document.createElement('a')
      parser.href = url
      return parser.hostname
    },
    appDomain: (state) => {
      return location.hostname
    }
  },
  actions: {
    setUrl ({ commit, dispatch }, url) {
      commit('instanceUrl', url)
      const modules = [
        'auth',
        'favorites',
        'moderation',
        'player',
        'playlists',
        'queue',
        'radios'
      ]
      modules.forEach(m => {
        commit(`${m}/reset`, null, { root: true })
      })
    },
    // Send a request to the login URL and save the returned JWT
    fetchSettings ({ commit }, payload) {
      return axios.get('instance/settings/').then(response => {
        logger.default.info('Successfully fetched instance settings')

        const sections = response.data.reduce((map, entry) => {
          map[entry.section] ??= {}
          map[entry.section][entry.name] = entry
          return map
        }, {})

        commit('settings', sections)
        payload?.callback?.()
      }, response => {
        logger.default.error('Error while fetching settings', response.data)
      })
    },
    fetchFrontSettings ({ commit }) {
      return axios.get('/settings.json').then(response => {
        commit('frontSettings', response.data)
      }, response => {
        logger.default.error('Error when fetching front-end configuration (or no customization available)')
      })
    }
  }
}
