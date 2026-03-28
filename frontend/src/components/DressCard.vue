<template>
  <article class="card">
    <div class="image-placeholder" :style="{ background: `linear-gradient(${dress.gradient})` }">
      <!-- <div class="dress-icon">
        <img src="../../pub" alt="">
      </div> -->
      <img :src="dress.img" alt="">
    </div>
    <div class="body">
      <h3>{{ dress.name }}</h3>
      <p class="meta">{{ dress.size }} • {{ dress.color }}</p>
      <p class="price">From ${{ dress.price }} / day</p>
      <RouterLink :to="`/rental/${dress.dress_id}`" class="rent-link">Rent this dress</RouterLink>
      <RouterLink :to="`/fitting/${dress.dress_id}`" class="rent-link">Book fitting for this dress</RouterLink>
    </div>
  </article>
</template>

<script setup>
import { RouterLink } from 'vue-router'

const props = defineProps({
  dress: { type: Object, required: true }
})
</script>

<style scoped>
.card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 24px;
  box-shadow: var(--shadow-card);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 154, 198, 0.2);
}

.card:hover {
  transform: translateY(-8px);
  box-shadow: 0 25px 50px rgba(255, 154, 198, 0.25);
}

.image-placeholder {
  width: auto;
  height: 300px;
  border-radius: 20px 20px 0 0;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.image-placeholder::before {
  /* content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 80px;
  background: rgba(255, 255, 255, 0.4);
  border-radius: 20px 20px 0 0; */
}

.dress-icon {
  font-size: 2.8rem;
  z-index: 1;
}

.card:hover .image-placeholder {
  transform: scale(1.05);
}

.body {
  padding: 1.5rem;
  flex: 1;
  display: flex;
  flex-direction: column;
}

h3 {
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--dark-blue);
  margin: 0 0 0.5rem 0;
}

.meta {
  font-size: 0.9rem;
  color: #64748b;
  margin: 0 0 0.75rem 0;
}

.price {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--primary-pink);
  margin: 0.75rem 0 1.25rem 0;
}

/* MATCHES HERO BUTTONS EXACTLY */
.rent-link {
  align-self: stretch;
  padding: 1rem 0;
  background: var(--gradient-bg);
  color: white;
  text-decoration: none;
  text-align: center;
  font-weight: 600;
  font-size: 1rem;
  border-radius: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: var(--shadow-soft);
  margin-top: 10px;
}

.rent-link:hover {
  transform: translateY(-3px);
  box-shadow: 0 20px 40px rgba(255, 154, 198, 0.4);
}

.rent-link:active {
  transform: translateY(-1px);
}
</style>