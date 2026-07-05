import { ref, readonly } from 'vue'

// ========================
// Breakpoints (matching responsive.scss)
// ========================
const BP_MOBILE_MAX = 767
const BP_DESKTOP_MIN = 768
const BP_TABLET_MIN = 768
const BP_TABLET_MAX = 1023

// ========================
// Shared reactive state (singleton)
// ========================
const windowWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 375)
const windowHeight = ref(typeof window !== 'undefined' ? window.innerHeight : 667)

const isDesktop = ref(false)
const isMobile = ref(true)
const isTablet = ref(false)
const deviceCategory = ref('mobile') // 'mobile' | 'tablet' | 'desktop'
const hasTouch = ref(false)
const platform = ref('unknown') // 'windows' | 'mac' | 'linux' | 'android' | 'ios' | 'unknown'

let _initialized = false
let _resizeTimer = null
const RESIZE_DEBOUNCE_MS = 150

// ========================
// Platform detection via user-agent
// ========================
function detectPlatform() {
  if (typeof navigator === 'undefined') return 'unknown'
  const ua = navigator.userAgent || ''
  if (/iPhone|iPad|iPod/i.test(ua)) return 'ios'
  if (/Android/i.test(ua)) return 'android'
  if (/Windows/i.test(ua)) return 'windows'
  if (/Mac/i.test(ua)) return 'mac'
  if (/Linux/i.test(ua)) return 'linux'
  return 'unknown'
}

// ========================
// Touch capability detection
// ========================
function detectTouch() {
  if (typeof window === 'undefined') return false
  return (
    'ontouchstart' in window ||
    navigator.maxTouchPoints > 0 ||
    (typeof navigator.msMaxTouchPoints !== 'undefined' && navigator.msMaxTouchPoints > 0)
  )
}

// ========================
// Determine device category from width + touch + platform
// ========================
function classify(width) {
  if (width <= BP_MOBILE_MAX) return 'mobile'
  if (width <= BP_TABLET_MAX) return 'tablet'
  return 'desktop'
}

// ========================
// Debounced update on resize
// ========================
function handleResize() {
  if (typeof window === 'undefined') return
  windowWidth.value = window.innerWidth
  windowHeight.value = window.innerHeight

  const w = windowWidth.value
  isDesktop.value = w >= BP_DESKTOP_MIN
  isMobile.value = w <= BP_MOBILE_MAX
  isTablet.value = w >= BP_TABLET_MIN && w <= BP_TABLET_MAX
  deviceCategory.value = classify(w)
}

// ========================
// Initialize (call once globally)
// ========================
export function initBreakpoint() {
  if (_initialized || typeof window === 'undefined') return
  _initialized = true

  // One-time platform/touch detection
  platform.value = detectPlatform()
  hasTouch.value = detectTouch()

  // Initial measurement
  handleResize()

  // Debounced resize listener
  window.addEventListener('resize', () => {
    clearTimeout(_resizeTimer)
    _resizeTimer = setTimeout(handleResize, RESIZE_DEBOUNCE_MS)
  })
}

// ========================
// Composable for components
// ========================
export function useBreakpoint() {
  if (!_initialized) {
    initBreakpoint()
  }

  return {
    windowWidth: readonly(windowWidth),
    windowHeight: readonly(windowHeight),
    isDesktop: readonly(isDesktop),
    isMobile: readonly(isMobile),
    isTablet: readonly(isTablet),
    deviceCategory: readonly(deviceCategory),
    hasTouch: readonly(hasTouch),
    platform: readonly(platform),
  }
}
