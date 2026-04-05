<template>
  <section class="page">
    <div class="login-card">
      <div class="card-header">
        <h2>Welcome Back</h2>
        <p class="subtitle">Sign in to your account or create a new one</p>
      </div>

      <div class="tab-row">
        <button :class="['tab-btn', { active: activeTab === 'login' }]" @click="activeTab = 'login'">
          Login
        </button>
        <button :class="['tab-btn', { active: activeTab === 'register' }]" @click="activeTab = 'register'">
          Register
        </button>
      </div>

      <!-- Login Form -->
      <form v-if="activeTab === 'login'" @submit.prevent="handleLogin" class="form">
        <div class="form-group">
          <label>Email</label>
          <input v-model="loginForm.email" type="email" placeholder="Fill in your email" required />
        </div>
        <div class="form-group">
          <label>Password</label>
          <input v-model="loginForm.password" type="password" placeholder="Enter your password" required />
        </div>
        <p v-if="loginError" class="error-msg">{{ loginError }}</p>
        <button type="submit" :disabled="loginLoading">
          {{ loginLoading ? 'Signing in...' : 'Sign In' }}
        </button>
        <p class="switch-text">
          Don't have an account?
          <span class="link" @click="activeTab = 'register'">Register here</span>
        </p>
      </form>

      <!-- Register Form -->
      <form v-if="activeTab === 'register'" @submit.prevent="handleRegister" class="form">
        <div class="form-group">
          <label>Full Name</label>
          <input v-model="registerForm.name" type="text" placeholder="Fill in your name" required />
        </div>
        <div class="form-group">
          <label>Email</label>
          <input v-model="registerForm.email" type="email" placeholder="Fill in your email" required />
        </div>
        <div class="form-group">
          <label>Password</label>
          <input v-model="registerForm.password" type="password" placeholder="Create a password" required />
        </div>
        <p v-if="registerError" class="error-msg">{{ registerError }}</p>
        <p v-if="registerSuccess" class="success-msg">{{ registerSuccess }}</p>
        <button type="submit" :disabled="registerLoading">
          {{ registerLoading ? 'Creating account...' : 'Create Account' }}
        </button>
        <p class="switch-text">
          Already have an account?
          <span class="link" @click="activeTab = 'login'">Sign in here</span>
        </p>
      </form>
    </div>
  </section>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const route = useRoute()
const { login } = useAuth()

const activeTab = ref('login')

const loginForm = reactive({ email: '', password: '' })
const registerForm = reactive({ name: '', email: '', password: '' })

const loginError = ref('')
const loginLoading = ref(false)
const registerError = ref('')
const registerSuccess = ref('')
const registerLoading = ref(false)

async function handleLogin() {
  loginError.value = ''
  loginLoading.value = true
  try {
    const res = await fetch('http://localhost:8000/customer/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: loginForm.email, password: loginForm.password })
    })
    const data = await res.json()
    if (data.code === 200) {
      login(data.data)
      const redirect = route.query.redirect || (data.data.role === 'employee' ? '/return' : '/dresses')
      router.push(redirect)
    } else {
      loginError.value = data.message || 'Login failed.'
    }
  } catch (e) {
    loginError.value = 'Could not connect to server.'
  } finally {
    loginLoading.value = false
  }
}

async function handleRegister() {
  registerError.value = ''
  registerSuccess.value = ''
  registerLoading.value = true
  try {
    const res = await fetch('http://localhost:8000/customer/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: registerForm.name,
        email: registerForm.email,
        password: registerForm.password
      })
    })
    const data = await res.json()
    if (data.code === 201) {
      registerSuccess.value = 'Account created! You can now sign in.'
      registerForm.name = ''
      registerForm.email = ''
      registerForm.password = ''
      setTimeout(() => { activeTab.value = 'login' }, 1500)
    } else {
      registerError.value = data.message || 'Registration failed.'
    }
  } catch (e) {
    registerError.value = 'Could not connect to server.'
  } finally {
    registerLoading.value = false
  }
}
</script>

<style scoped>
.page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 70vh;
  padding: 2rem 1rem;
}

.login-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 28px;
  border: 1px solid rgba(255, 154, 198, 0.2);
  box-shadow: 0 20px 60px rgba(255, 154, 198, 0.2), 0 0 0 1px rgba(255, 255, 255, 0.9);
  padding: 2.5rem;
  width: 100%;
  max-width: 440px;
  position: relative;
  overflow: hidden;
}

.login-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--gradient-bg);
}

.card-header {
  text-align: center;
  margin-bottom: 1.75rem;
}

.card-header h2 {
  font-size: 1.9rem;
  font-weight: 800;
  background: var(--gradient-bg);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 0.4rem 0;
}

.subtitle {
  color: #64748b;
  font-size: 0.95rem;
  margin: 0;
}

.tab-row {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.75rem;
  background: #f1f5f9;
  border-radius: 14px;
  padding: 4px;
}

.tab-btn {
  flex: 1;
  padding: 0.6rem;
  border: none;
  border-radius: 11px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  background: transparent;
  color: #64748b;
  transition: all 0.2s ease;
}

.tab-btn.active {
  background: white;
  color: var(--dark-blue);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.form {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.form-group {
  margin-bottom: 1.4rem;
}

label {
  display: block;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--dark-blue);
  margin-bottom: 0.45rem;
}

input {
  width: 100%;
  padding: 0.85rem 1rem;
  border: 2px solid #e8eaf6;
  border-radius: 14px;
  font-size: 0.95rem;
  background: rgba(255, 255, 255, 0.8);
  transition: border-color 0.2s ease;
  box-sizing: border-box;
}

input:focus {
  outline: none;
  border-color: var(--primary-pink);
}

button[type='submit'] {
  width: 100%;
  padding: 1rem;
  background: var(--gradient-bg);
  color: white;
  border: none;
  border-radius: 16px;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 0.5rem;
  box-shadow: 0 10px 30px rgba(255, 154, 198, 0.4);
}

button[type='submit']:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 15px 35px rgba(255, 154, 198, 0.5);
}

button[type='submit']:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.error-msg {
  color: #e11d48;
  font-size: 0.88rem;
  margin: 0 0 0.75rem 0;
  padding: 0.6rem 0.9rem;
  background: #fff1f2;
  border-radius: 10px;
  border: 1px solid #fecdd3;
}

.success-msg {
  color: #059669;
  font-size: 0.88rem;
  margin: 0 0 0.75rem 0;
  padding: 0.6rem 0.9rem;
  background: #f0fdf4;
  border-radius: 10px;
  border: 1px solid #bbf7d0;
}

.switch-text {
  text-align: center;
  color: #64748b;
  font-size: 0.9rem;
  margin: 1rem 0 0 0;
}

.link {
  color: var(--primary-pink);
  font-weight: 600;
  cursor: pointer;
  text-decoration: underline;
}
</style>
