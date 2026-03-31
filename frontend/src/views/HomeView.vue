<template>
  <section class="hero-section">
    <div class="hero-content">
      <div class="hero-text">
        <h1 class="hero-title">
          Find Your <span class="gradient-text">Perfect</span>
          Prom Dress
        </h1>
        <p class="hero-subtitle">
          Rent stunning dresses for your special night.
          Curated collection, perfect fit, unforgettable memories.
        </p>
        <div class="hero-actions">
          <RouterLink to="/dresses" class="btn btn-primary">
            ✨ Browse Collection ✨
          </RouterLink>
          <!-- <RouterLink to="/fitting" class="btn btn-secondary">
            Book Fitting
          </RouterLink> -->
        </div>
      </div>
      <!-- <div class="hero-image">
        <div class="dress-preview">
          <div class="dress-card floating">
            <div class="dress-image-placeholder">
              <div class="dress-icon">👗</div>
               <div><img src="../../public/images/dress_pink.jpeg" alt=""></img></div>
              <span>Blush Satin Gown</span>
            </div>
          </div>
        </div>
      </div> -->
    </div>
  </section>
</template>

<script setup>
import { RouterLink } from 'vue-router'
</script>

<style scoped>
.hero-section {
  min-height: 80vh;
  display: flex;
  align-items: center;
  position: relative;
  overflow: hidden;
  padding: 0 2rem;
}

.hero-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--gradient-bg);
  opacity: 0.07;
  z-index: 0;
}

.hero-content {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  align-items: center;
  position: relative;
  z-index: 1;
}

.hero-text {
  animation: slideInLeft 0.8s ease-out;
}

.hero-title {
  font-size: clamp(2.5rem, 5vw, 4rem);
  font-weight: 800;
  line-height: 1.1;
  margin-bottom: 1.5rem;
  color: var(--dark-blue);
}

.gradient-text {
  background: var(--gradient-bg);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 1.3rem;
  color: #64748b;
  line-height: 1.6;
  margin-bottom: 2.5rem;
  max-width: 500px;
}

.hero-actions {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.btn {
  padding: 1rem 2rem;
  border-radius: 50px;
  font-weight: 600;
  font-size: 1rem;
  text-decoration: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  position: relative;
  overflow: hidden;
}

.btn-primary {
  background: var(--gradient-bg);
  color: white;
  box-shadow: var(--shadow-soft);
}

.btn-primary:hover {
  transform: translateY(-4px) scale(1.05);
  box-shadow: 0 20px 40px rgba(255, 154, 198, 0.4);
}

.btn-secondary {
  background: transparent;
  color: var(--dark-blue);
  border: 2px solid var(--pastel-blue);
}

.btn-secondary:hover {
  background: var(--pastel-blue);
  transform: translateY(-2px);
}

.dress-image-placeholder {
  width: 100%;
  height: 280px;
  background: linear-gradient(135deg, #ff9ac6 0%, #ffd4e6 50%, #f8c8dc 100%);
  border-radius: 24px 24px 0 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  position: relative;
  overflow: hidden;
}

.dress-image-placeholder::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 100px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 24px 24px 0 0;
}

.dress-icon {
  font-size: 3.5rem;
  z-index: 1;
}

.dress-image-placeholder span {
  font-size: 1.1rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  z-index: 1;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.hero-image {
  animation: slideInRight 0.8s ease-out 0.2s both;
  display: flex;
  justify-content: flex-end;
}

.dress-preview {
  perspective: 1000px;
}

.dress-card {
  width: 280px;
  height: 380px;
  background: white;
  border-radius: 24px;
  box-shadow: var(--shadow-card);
  position: relative;
  transform-style: preserve-3d;
  animation: float 6s ease-in-out infinite;
}

.dress-card.floating {
  animation-delay: -2s;
}

.dress-image {
  width: 100%;
  height: 280px;
  object-fit: cover;
  border-radius: 24px 24px 0 0;
}

.dress-image::before {
  content: '👗';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 4rem;
  opacity: 0.1;
}

.dress-label {
  padding: 1rem 1.5rem;
  font-weight: 600;
  color: var(--dark-blue);
  text-align: center;
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-50px);
  }

  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(50px);
  }

  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes float {

  0%,
  100% {
    transform: translateY(0px) rotateX(0deg);
  }

  50% {
    transform: translateY(-20px) rotateX(2deg);
  }
}

@media (max-width: 768px) {
  .hero-content {
    grid-template-columns: 1fr;
    gap: 2rem;
    text-align: center;
  }

  .hero-actions {
    justify-content: center;
  }
}
</style>