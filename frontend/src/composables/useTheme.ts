import { ref, watch } from 'vue'

export type Theme = 'dark' | 'light'

function detectInitialTheme(): Theme {
  try {
    const stored = localStorage.getItem('theme')
    if (stored === 'dark' || stored === 'light') return stored
  } catch {
    // localStorage can be unavailable (private mode).
  }
  if (typeof window !== 'undefined' && window.matchMedia?.('(prefers-color-scheme: light)').matches) {
    return 'light'
  }
  return 'dark'
}

const theme = ref<Theme>(detectInitialTheme())

let initialized = false

function applyTheme(value: Theme) {
  document.documentElement.setAttribute('data-theme', value)
}

function ensureInitialized() {
  if (initialized) return
  initialized = true
  applyTheme(theme.value)
}

function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
}

export function useTheme() {
  ensureInitialized()
  watch(theme, (value) => {
    applyTheme(value)
    try {
      localStorage.setItem('theme', value)
    } catch {
      // Ignore storage failures.
    }
  })

  return {
    theme,
    toggleTheme,
  }
}
