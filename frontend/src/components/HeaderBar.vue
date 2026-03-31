<template>
  <header class="header">
    <div class="logo">
      <span class="logo-icon">✨</span>
      Dress To Impress
    </div>
    <nav class="nav">
      <!-- Customer nav -->
      <template v-if="!user || user.role === 'customer'">
        <RouterLink to="/">Home</RouterLink>
        <RouterLink to="/dresses">Browse Dresses</RouterLink>
      </template>
      <!-- Employee nav -->
      <template v-if="user?.role === 'employee'">
        <RouterLink to="/return">Return Dress</RouterLink>
      </template>
    </nav>
    <div class="auth-section">
      <template v-if="user">
        <span class="user-greeting">Hi, {{ user.name.split(' ')[0] }}</span>
        <button class="logout-btn" @click="logout">Logout</button>
      </template>
      <template v-else>
        <RouterLink to="/login" class="login-btn">Login</RouterLink>
      </template>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const { state, logout: authLogout } = useAuth()
const user = computed(() => state.user)

function logout() {
  authLogout()
  router.push('/login')
}
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 2rem;  /* Reduced from 1.5rem */
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 154, 198, 0.2);
  box-shadow: 0 4px 20px rgba(255, 154, 198, 0.1);
}

.logo {
  font-size: 1.5rem;
  font-weight: 800;
  background: var(--gradient-bg);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.logo-icon {
  font-size: 1.3em;
}

.nav {
  display: flex;
  gap: 2rem;
}

.nav a {
  color: var(--dark-blue);
  text-decoration: none;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 25px;
  transition: all 0.3s ease;
  position: relative;
}

.nav a:hover {
  background: var(--pastel-pink);
  transform: translateY(-2px);
  box-shadow: var(--shadow-soft);
}

.nav a.router-link-active {
  background: var(--gradient-bg);
  color: white;
  box-shadow: var(--shadow-soft);
}

.auth-section {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.user-greeting {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--dark-blue);
}

.login-btn {
  color: var(--dark-blue);
  text-decoration: none;
  font-weight: 600;
  padding: 0.5rem 1.2rem;
  border-radius: 25px;
  background: var(--gradient-bg);
  color: white;
  transition: all 0.3s ease;
  box-shadow: var(--shadow-soft);
}

.login-btn:hover {
  transform: translateY(-2px);
}

.logout-btn {
  padding: 0.45rem 1rem;
  border: 2px solid rgba(255, 154, 198, 0.5);
  border-radius: 25px;
  background: transparent;
  color: var(--dark-blue);
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.logout-btn:hover {
  background: var(--pastel-pink);
}
</style>