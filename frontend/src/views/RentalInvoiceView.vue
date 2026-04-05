<template>
  <section class="page">
    <h2>Booking Confirmed</h2>

    <div v-if="order" class="card">
      <!-- Header -->
      <div class="check-icon">✓</div>
      <p class="confirmed-text">Your rental is confirmed!</p>

      <hr class="divider" />

      <!-- Details grid -->
      <div class="details-grid">
        <div class="detail-item">
          <span class="detail-label">Customer ID</span>
          <span class="detail-value">#{{ order.customer_id }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Rental ID</span>
          <span class="detail-value">#{{ order.rental_id }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Dress Rented</span>
          <span class="detail-value">{{ order.dress_name }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Rental Period</span>
          <span class="detail-value">{{ formatDate(order.start_date) }} → {{ formatDate(order.end_date) }}</span>
        </div>
      </div>

      <hr class="divider" />

      <!-- Total -->
      <div class="total-row">
        <span>Total Paid</span>
        <span class="total-amount">${{ Number(order.total).toFixed(2) }}</span>
      </div>

      <hr class="divider" />

      <!-- Warning message -->
      <div class="warning-box">
        <p class="warning-icon">⚠</p>
        <p class="warning-text">
          Please return on time, without any damage or stains.
          Otherwise there will be subsequent charges.
        </p>
      </div>

      <RouterLink to="/dresses" class="btn-home">Back to Dresses</RouterLink>
    </div>

    <div v-else class="card no-data">
      <p>No order data found.</p>
      <RouterLink to="/dresses" class="btn-home">Back to Dresses</RouterLink>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'

const order = ref(null)

onMounted(() => {
  const state = window.history.state?.order
  if (state) order.value = state
})

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-SG', {
    day: 'numeric', month: 'short', year: 'numeric'
  })
}
</script>

<style scoped>
.page {
  max-width: 480px;
  margin: 3rem auto;
  padding: 0 1rem;
}

h2 {
  font-size: 2.2rem;
  background: var(--gradient-bg);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-align: center;
  margin-bottom: 1.5rem;
  font-weight: 800;
}

.card {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  padding: 2.5rem;
  border-radius: 24px;
  border: 1px solid rgba(255, 154, 198, 0.2);
  box-shadow:
    0 20px 40px rgba(255, 154, 198, 0.15),
    0 0 0 1px rgba(255, 255, 255, 0.9);
  position: relative;
  overflow: hidden;
  text-align: center;
}

.card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 4px;
  background: var(--gradient-bg);
}

.check-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(34, 197, 94, 0.15);
  border: 2px solid rgba(34, 197, 94, 0.4);
  color: #16a34a;
  font-size: 1.8rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
}

.confirmed-text {
  font-size: 1.1rem;
  font-weight: 700;
  color: #16a34a;
  margin: 0;
}

.divider {
  border: none;
  border-top: 1px solid rgba(255, 154, 198, 0.2);
  margin: 1.25rem 0;
}

.details-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  text-align: left;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.detail-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-value {
  font-size: 1rem;
  font-weight: 700;
  color: var(--dark-blue);
}

.total-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--dark-blue);
}

.total-amount {
  font-size: 1.4rem;
  background: var(--gradient-bg);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.warning-box {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.3);
  border-radius: 12px;
  padding: 1rem 1.2rem;
  text-align: left;
  margin-bottom: 1.5rem;
}

.warning-icon {
  font-size: 1.1rem;
  margin: 0;
  flex-shrink: 0;
  color: #d97706;
}

.warning-text {
  font-size: 0.9rem;
  color: #92400e;
  line-height: 1.5;
  margin: 0;
  font-weight: 500;
}

.btn-home {
  display: block;
  width: 100%;
  padding: 1.1rem;
  background: var(--gradient-bg);
  color: white;
  border-radius: 16px;
  font-size: 1rem;
  font-weight: 700;
  text-align: center;
  text-decoration: none;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 10px 30px rgba(255, 154, 198, 0.4);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-home:hover {
  transform: translateY(-3px);
  box-shadow: 0 20px 40px rgba(255, 154, 198, 0.5);
}

.no-data {
  color: #64748b;
}
</style>
