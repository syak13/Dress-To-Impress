<template>
  <section class="page">
    <h2>Return Invoice</h2>

    <div v-if="invoice" class="card">
      <!-- Header -->
      <div class="invoice-header">
        <div class="badge success">Return Submitted</div>
        <p class="rental-ref">Rental #{{ invoice.rental_id }}</p>
      </div>

      <hr class="divider" />

      <!-- Fee breakdown -->
      <div class="fee-table">
        <div class="fee-row">
          <span>Damage Fee</span>
          <span :class="invoice.damage_fee > 0 ? 'amount-bad' : 'amount-ok'">
            ${{ invoice.damage_fee.toFixed(2) }}
          </span>
        </div>

        <div class="fee-row">
          <span>
            Late Fee
            <span v-if="invoice.days_late > 0" class="days-tag">
              {{ invoice.days_late }} day{{ invoice.days_late > 1 ? 's' : '' }} late
            </span>
          </span>
          <span :class="invoice.late_fee > 0 ? 'amount-bad' : 'amount-ok'">
            ${{ invoice.late_fee.toFixed(2) }}
          </span>
        </div>

        <div class="fee-row total">
          <span>Total Due</span>
          <span :class="invoice.total_penalty > 0 ? 'amount-bad' : 'amount-ok'">
            ${{ invoice.total_penalty.toFixed(2) }}
          </span>
        </div>
      </div>

      <!-- No fees message -->
      <div v-if="invoice.total_penalty === 0" class="all-clear">
        No fees — dress returned in perfect condition and on time!
      </div>

      <!-- Damage explanation -->
      <div v-if="invoice.is_damaged" class="damage-note">
        <p class="damage-title">Damage Assessment</p>
        <p class="damage-desc">{{ invoice.damage_description }}</p>
      </div>

      <hr class="divider" />

      <RouterLink to="/" class="btn-home">Back to Home</RouterLink>
    </div>

    <div v-else class="card no-data">
      <p>No invoice data found.</p>
      <RouterLink to="/return" class="btn-home">Go to Returns</RouterLink>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'

const invoice = ref(null)

onMounted(() => {
  const state = window.history.state?.invoice
  if (state) {
    invoice.value = state
  }
})
</script>

<style scoped>
.page {
  max-width: 520px;
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
}

.card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 4px;
  background: var(--gradient-bg);
}

.invoice-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.25rem;
}

.badge {
  padding: 0.35rem 0.9rem;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 0.3px;
}

.badge.success {
  background: rgba(34, 197, 94, 0.12);
  color: #15803d;
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.rental-ref {
  font-size: 0.95rem;
  color: #64748b;
  font-weight: 600;
  margin: 0;
}

.divider {
  border: none;
  border-top: 1px solid rgba(255, 154, 198, 0.2);
  margin: 1.25rem 0;
}

.fee-table {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.fee-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1rem;
  color: var(--dark-blue);
  padding: 0.6rem 0;
  border-bottom: 1px solid rgba(255, 154, 198, 0.1);
}

.fee-row.total {
  border-bottom: none;
  border-top: 2px solid rgba(255, 154, 198, 0.3);
  padding-top: 1rem;
  margin-top: 0.25rem;
  font-size: 1.2rem;
  font-weight: 800;
}

.days-tag {
  display: inline-block;
  margin-left: 0.5rem;
  font-size: 0.8rem;
  background: rgba(255, 154, 198, 0.15);
  color: #be185d;
  border-radius: 999px;
  padding: 0.15rem 0.6rem;
  font-weight: 600;
}

.amount-ok {
  color: #15803d;
  font-weight: 700;
}

.amount-bad {
  color: #c53030;
  font-weight: 700;
}

.all-clear {
  text-align: center;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.25);
  border-radius: 12px;
  padding: 1rem;
  color: #15803d;
  font-size: 0.95rem;
  font-weight: 500;
  margin-top: 1rem;
}

.damage-note {
  margin-top: 1rem;
  background: rgba(255, 154, 198, 0.08);
  border: 1px solid rgba(255, 154, 198, 0.25);
  border-radius: 12px;
  padding: 1rem 1.2rem;
}

.damage-title {
  font-weight: 700;
  color: var(--dark-blue);
  font-size: 0.9rem;
  margin: 0 0 0.4rem 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.damage-desc {
  color: #475569;
  font-size: 0.95rem;
  line-height: 1.6;
  margin: 0;
}

.btn-home {
  display: block;
  width: 100%;
  padding: 1.1rem;
  background: var(--gradient-bg);
  color: white;
  border: none;
  border-radius: 16px;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
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
  text-align: center;
  color: #64748b;
}
</style>
