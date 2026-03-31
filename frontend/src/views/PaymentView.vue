<template>
  <section class="page">
    <div class="payment-layout" v-if="dress">
      <!-- Order Summary -->
      <div class="summary-panel">
        <h3>Order Summary</h3>
        <img :src="dress.img" alt="" class="dress-img" />
        <h2>{{ dress.name }}</h2>
        <p class="meta">{{ dress.size }} &bull; {{ dress.color }}</p>
        <div class="summary-row"><span>Rental period</span><span>{{ startDate }} → {{ endDate }}</span></div>
        <div class="summary-row"><span>Price</span><span>${{ dress.price }}</span></div>
        <div class="summary-row total"><span>Total</span><span>${{ dress.price }}</span></div>
      </div>

      <!-- Payment Form -->
      <div class="payment-panel">
        <h3>Payment Details</h3>

        <div v-if="paymentSuccess" class="success-box">
          <p>Payment successful! Your rental is confirmed.</p>
          <p>Rental ID: <strong>{{ confirmedRentalId }}</strong></p>
          <button class="pay-btn" @click="router.push('/')">Back to Home</button>
        </div>

        <form v-else @submit.prevent="handlePayment">
          <div class="form-group">
            <label>Name on card</label>
            <input v-model="cardName" placeholder="Jane Smith" required />
          </div>

          <div class="form-group">
            <label>Card details</label>
            <div id="card-element" class="stripe-input"></div>
            <p v-if="cardError" class="error-msg">{{ cardError }}</p>
          </div>

          <p v-if="apiError" class="error-msg">{{ apiError }}</p>

          <button type="submit" class="pay-btn" :disabled="loading">
            {{ loading ? 'Processing...' : `Pay $${dress.price}` }}
          </button>
        </form>
      </div>
    </div>

    <div v-else class="loading">Loading order details...</div>
  </section>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { loadStripe } from '@stripe/stripe-js'

const route = useRoute()
const router = useRouter()

const dress = ref(null)
const startDate = route.query.startDate
const endDate = route.query.endDate

const cardName = ref('')
const cardError = ref('')
const apiError = ref('')
const loading = ref(false)
const paymentSuccess = ref(false)
const confirmedRentalId = ref(null)

let stripe = null
let cardElement = null

onMounted(async () => {
  // Load dress details
  const dressId = route.params.dressId
  const res = await fetch(`http://localhost:5001/inventory/${dressId}`)
  const data = await res.json()
  if (data.code === 200) dress.value = data.data

  // Mount Stripe card element
  stripe = await loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY)
  const elements = stripe.elements()
  cardElement = elements.create('card', {
    style: {
      base: {
        fontSize: '16px',
        color: '#1e3a5f',
        fontFamily: 'inherit',
        '::placeholder': { color: '#94a3b8' }
      }
    }
  })
  cardElement.mount('#card-element')
  cardElement.on('change', (e) => {
    cardError.value = e.error ? e.error.message : ''
  })
})

onBeforeUnmount(() => {
  if (cardElement) cardElement.destroy()
})

async function handlePayment() {
  loading.value = true
  apiError.value = ''

  const stored = localStorage.getItem('dti_user')
  const user = stored ? JSON.parse(stored) : null
  if (!user) {
    apiError.value = 'You must be logged in to complete a rental.'
    loading.value = false
    return
  }

  // Step 1: Create rental order → gets Stripe client_secret from backend
  let orderData
  try {
    const orderRes = await fetch('http://localhost:5011/rental-order', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customer_id: user.customer_id,
        dress_id: dress.value.dress_id,
        start_date: startDate,
        end_date: endDate
      })
    })
    const orderJson = await orderRes.json()
    if (orderJson.code !== 201) {
      apiError.value = orderJson.message || 'Failed to create rental order.'
      loading.value = false
      return
    }
    orderData = orderJson.data
  } catch (e) {
    apiError.value = 'Could not reach the server. Please try again.'
    loading.value = false
    return
  }

  const { client_secret, invoice_id, rental_id } = orderData

  if (!client_secret) {
    apiError.value = 'Payment setup failed. Please contact support.'
    loading.value = false
    return
  }

  // Step 2: Confirm card payment with Stripe
  const { error, paymentIntent } = await stripe.confirmCardPayment(client_secret, {
    payment_method: {
      card: cardElement,
      billing_details: { name: cardName.value }
    }
  })

  if (error) {
    cardError.value = error.message
    loading.value = false
    return
  }

  // Step 3: Mark invoice as PAID
  if (paymentIntent.status === 'succeeded') {
    await fetch(`http://localhost:5005/invoice/${invoice_id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'PAID', stripe_id: paymentIntent.id })
    })
    confirmedRentalId.value = rental_id
    paymentSuccess.value = true
  }

  loading.value = false
}
</script>

<style scoped>
.page {
  max-width: 1000px;
  margin: 3rem auto;
  padding: 0 1rem;
}

.payment-layout {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 2rem;
  align-items: start;
}

.summary-panel,
.payment-panel {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  padding: 2rem;
  border-radius: 24px;
  border: 1px solid rgba(255, 154, 198, 0.2);
  box-shadow: 0 20px 40px rgba(255, 154, 198, 0.15), 0 0 0 1px rgba(255, 255, 255, 0.9);
  position: relative;
  overflow: hidden;
}

.summary-panel::before,
.payment-panel::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 4px;
  background: var(--gradient-bg);
}

.dress-img {
  width: 100%;
  max-height: 300px;
  object-fit: cover;
  border-radius: 14px;
  margin-bottom: 1rem;
}

h2 {
  font-size: 1.5rem;
  background: var(--gradient-bg);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 800;
  margin-bottom: 0.5rem;
}

h3 {
  color: var(--dark-blue);
  font-size: 1.1rem;
  font-weight: 700;
  margin: 0 0 1.25rem 0;
  text-align: center;
}

.meta {
  color: var(--dark-blue);
  margin-bottom: 0.75rem;
  font-size: 0.9rem;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  color: var(--dark-blue);
  padding: 0.5rem 0;
  border-bottom: 1px solid rgba(255, 154, 198, 0.15);
  font-size: 0.95rem;
}

.summary-row.total {
  font-weight: 800;
  font-size: 1.05rem;
  border-bottom: none;
  margin-top: 0.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--dark-blue);
  margin-bottom: 0.5rem;
}

input {
  width: 100%;
  padding: 0.9rem 1rem;
  border: 2px solid #e8eaf6;
  border-radius: 12px;
  font-size: 1rem;
  background: rgba(255, 255, 255, 0.8);
  box-sizing: border-box;
}

.stripe-input {
  padding: 0.9rem 1rem;
  border: 2px solid #e8eaf6;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.8);
}

.pay-btn {
  width: 100%;
  padding: 1.1rem;
  background: var(--gradient-bg);
  color: white;
  border: none;
  border-radius: 16px;
  font-size: 1.05rem;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 10px 30px rgba(255, 154, 198, 0.4);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  transition: all 0.3s ease;
}

.pay-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 20px 40px rgba(255, 154, 198, 0.5);
}

.pay-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.error-msg {
  color: #e53e3e;
  font-size: 0.875rem;
  margin-top: 0.4rem;
}

.success-box {
  text-align: center;
  padding: 1.5rem;
  background: rgba(72, 187, 120, 0.1);
  border: 1px solid rgba(72, 187, 120, 0.3);
  border-radius: 14px;
  margin-bottom: 1.5rem;
  color: var(--dark-blue);
}

.success-box p {
  margin-bottom: 0.5rem;
}

.loading {
  text-align: center;
  padding: 4rem;
  color: var(--dark-blue);
}

@media (max-width: 800px) {
  .payment-layout {
    grid-template-columns: 1fr;
  }
}
</style>
