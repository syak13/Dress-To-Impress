import { reactive } from 'vue'

// Module-level state — shared across ALL components (like PHP $_SESSION)
const state = reactive({
  user: JSON.parse(localStorage.getItem('dti_user') || 'null')
})

export function useAuth() {
  function login(userData) {
    state.user = userData
    localStorage.setItem('dti_user', JSON.stringify(userData))
  }

  function logout() {
    state.user = null
    localStorage.removeItem('dti_user')
  }

  return { state, login, logout }
}
