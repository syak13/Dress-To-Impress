<template>
  <header class="header">
    <div class="logo">
      <span class="logo-icon">✨</span>
      Dress To Impress
    </div>
    <nav class="nav">
      <RouterLink to="/">Home</RouterLink>
      <RouterLink to="/dresses">Browse Dresses</RouterLink>
      <RouterLink to="/fitting">Book Fitting</RouterLink>
      <RouterLink to="/rental">Rentals</RouterLink>
    </nav>
  </header>
</template>

<script setup>
import { RouterLink } from 'vue-router'
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
</style>