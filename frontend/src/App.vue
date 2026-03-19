<template>
  <div class="app">
    <HeaderBar />
    <main class="main-content">
      <router-view />
    </main>
    <FooterBar />
  </div>
</template>

<script setup>
import HeaderBar from './components/HeaderBar.vue'
import FooterBar from './components/FooterBar.vue'
</script>

<style>
:root {
  --primary-pink: #ff9ac6;
  --pastel-pink: #ffd4e6;
  --soft-blue: #a2c8f0;
  --pastel-blue: #d4e6ff;
  --dark-blue: #1e3a8a;
  --gradient-bg: linear-gradient(135deg, #ff9ac6 0%, #a2c8f0 100%);
  --shadow-soft: 0 10px 30px rgba(255, 154, 198, 0.2);
  --shadow-card: 0 8px 25px rgba(162, 200, 240, 0.15);
}

body {
  margin: 0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: linear-gradient(145deg, #fef7ff 0%, #f0f8ff 100%);
  min-height: 100vh;
}

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  padding: 2rem;
  position: relative;
}

.main-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: var(--gradient-bg);
  opacity: 0.3;
}
</style>