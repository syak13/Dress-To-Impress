<template>
  <section class="page">
    <div class="payment-layout" v-if="selectedDress">
      <!-- Dress Summary -->
      <div class="summary-panel">
        <h3>Fitting Details</h3>
        <img :src="selectedDress.img" alt="" class="dress-img" />
        <h2>{{ selectedDress.name }}</h2>
        <p class="meta">{{ selectedDress.size }} • {{ selectedDress.color }}</p>
        <div class="summary-row">
          <span>Fitting Date</span>
          <span>{{ formatDate(rentForm.startDate) }}</span>
        </div>
        <!-- <div class="summary-row">
          <span>Price per day</span>
          <span>${{ selectedDress.price }}</span>
        </div>
        <div class="summary-row total">
          <span>Total ({{ rentalDays }} days)</span>
          <span>${{ totalPrice }}</span>
        </div> -->
      </div>

      <!-- Customer + Payment Form -->
      <div class="payment-panel">
        <h3>Complete Your Booking</h3>

        <!-- Customer Details Section -->
        <div class="section-divider">
          <h4>Customer Information</h4>
        </div>

        <div class="form-group">
          <label>Name *</label>
          <input v-model="customerDetails.name" placeholder="Jane Smith" required />
        </div>

        <div class="form-group">
          <label>Email *</label>
          <input v-model="customerDetails.email" type="email" placeholder="jane@example.com" required />
        </div>

        <div class="form-group">
          <label>Phone *</label>
          <input v-model="customerDetails.phone" placeholder="+65 9123 4567" required />
        </div>

        <!-- Payment Section -->
        <!-- <div class="section-divider">
          <h4>Payment Method</h4>
        </div> -->

        <!-- <div class="form-group">
          <label>Name on card</label>
          <input v-model="cardName" placeholder="Jane Smith" required />
        </div> -->

        <!-- <div class="form-group">
          <label>Card details</label>
          <div id="card-element" class="stripe-input"></div>
          <p v-if="cardError" class="error-msg">{{ cardError }}</p>
        </div> -->

        <!-- <p v-if="apiError" class="error-msg">{{ apiError }}</p> -->

        <button 
          type="submit" 
          class="pay-btn" 
          :disabled="loading || !isFormValid"
          @click.prevent="handlePayment"
        >
          {{ loading ? 'Processing...' : `Click to Confirm Fitting Appointment` }}
        </button>

        <!-- Success State -->
        <!-- <div v-if="paymentSuccess" class="success-box">
          <h4>🎉 Rental Confirmed!</h4>
          <p>Your dress is reserved. You'll receive a confirmation email shortly.</p>
          <p><strong>Rental ID:</strong> {{ confirmedRentalId }}</p>
          <RouterLink to="/" class="back-home-btn">
            Back to Dresses
          </RouterLink>
        </div> -->
      </div>
    </div>

    <div v-else class="loading">
      Loading your booking...
    </div>
  </section>
</template>

<script setup>
import { reactive, ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { loadStripe } from '@stripe/stripe-js'

const route = useRoute()

const selectedDress = ref(null)
const customerDetails = reactive({ name: '', phone: '', email: '' })
const rentForm = reactive({ startDate: '', endDate: '' })
const cardName = ref('')

const cardError = ref('')
const apiError = ref('')
const loading = ref(false)
const paymentSuccess = ref(false)
const confirmedRentalId = ref(null)

let stripe = null
let cardElement = null

onMounted(async () => {
  // Pre-fill dates from availability selection
  rentForm.startDate = route.query.startDate || ''
  rentForm.endDate = route.query.endDate || ''

  // Auto-fill customer info from localStorage (login session)
  const stored = localStorage.getItem('dti_user')
  if (stored) {
    const user = JSON.parse(stored)
    customerDetails.name = user.name || ''
    customerDetails.email = user.email || ''
  }

  // Load dress details
  const dressId = route.params.dressId
  if (dressId) {
    const res = await fetch(`http://localhost:5001/inventory/${dressId}`)
    const data = await res.json()
    if (data.code === 200) {
      selectedDress.value = data.data
    }
  }

  // Initialize Stripe
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

const rentalDays = computed(() => {
  if (!rentForm.startDate || !rentForm.endDate) return 0
  const start = new Date(rentForm.startDate)
  const end = new Date(rentForm.endDate)
  return Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1
})

const totalPrice = computed(() => {
  if (!selectedDress.value || !rentalDays.value) return 0
  return (parseFloat(selectedDress.value.price) * rentalDays.value).toFixed(2)
})

const isFormValid = computed(() => {
  return customerDetails.name && 
         customerDetails.email && 
         customerDetails.phone && 
         rentForm.startDate && 
         rentForm.endDate && 
         cardName.value
})

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-SG', {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

async function handlePayment() {
  loading.value = true
  apiError.value = ''
  cardError.value = ''

  const stored = localStorage.getItem('dti_user')
  const user = stored ? JSON.parse(stored) : null

  if (!user) {
    apiError.value = 'Please log in to complete your rental.'
    loading.value = false
    return
  }

  try {
    const orderRes = await fetch('http://localhost:5011/rental-order', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customer_id: user.customer_id,
        dress_id: selectedDress.value.dress_id,
        start_date: rentForm.startDate,
        end_date: rentForm.endDate,
        customer_name: customerDetails.name,
        customer_email: customerDetails.email,
        customer_phone: customerDetails.phone,
        total_amount: parseFloat(totalPrice.value)
      })
    })

    const orderJson = await orderRes.json()

    if (orderJson.code !== 201) {
      apiError.value = orderJson.message || 'Failed to create rental order.'
      loading.value = false
      return
    }

    const { client_secret, invoice_id, rental_id } = orderJson.data

    const { error, paymentIntent } = await stripe.confirmCardPayment(client_secret, {
      payment_method: {
        card: cardElement,
        billing_details: {
          name: cardName.value,
          email: customerDetails.email,
          phone: customerDetails.phone
        }
      }
    })

    if (error) {
      cardError.value = error.message
      loading.value = false
      return
    }

    if (paymentIntent.status === 'succeeded') {
      await fetch(`http://localhost:5005/invoice/${invoice_id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: 'PAID',
          stripe_id: paymentIntent.id
        })
      })

      confirmedRentalId.value = rental_id
      paymentSuccess.value = true
    }
  } catch (e) {
    apiError.value = 'Payment failed. Please try again.'
    console.error(e)
  } finally {
    loading.value = false
  }
}


</script>

<style scoped>
.page {
  max-width: 1100px;
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
  padding: 2.5rem;
  border-radius: 24px;
  border: 1px solid rgba(255, 154, 198, 0.2);
  box-shadow: 
    0 20px 40px rgba(255, 154, 198, 0.15),
    0 0 0 1px rgba(255, 255, 255, 0.9);
  position: relative;
  overflow: hidden;
}

.summary-panel::before,
.payment-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--gradient-bg);
}

.dress-img {
  width: 100%;
  max-height: 300px;
  object-fit: cover;
  border-radius: 16px;
  margin-bottom: 1.25rem;
}

h2 {
  font-size: 1.5rem;
  background: var(--gradient-bg);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 800;
  margin-bottom: 0.75rem;
}

h3 {
  color: var(--dark-blue);
  font-size: 1.2rem;
  font-weight: 700;
  margin: 0 0 1.5rem 0;
  text-align: center;
}

h4 {
  color: var(--dark-blue);
  font-size: 1rem;
  font-weight: 700;
  margin: 0 0 1.25rem 0;
}

.meta {
  color: var(--dark-blue);
  margin-bottom: 1rem;
  font-size: 0.95rem;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  color: var(--dark-blue);
  padding: 0.75rem 0;
  border-bottom: 1px solid rgba(255, 154, 198, 0.15);
  font-size: 0.95rem;
}

.summary-row.total {
  font-weight: 800;
  font-size: 1.1rem;
  border-bottom: none;
  margin-top: 0.75rem;
  padding-top: 1rem;
  border-top: 2px solid rgba(255, 154, 198, 0.3);
}

.section-divider {
  border-bottom: 1px solid rgba(255, 154, 198, 0.2);
  padding-bottom: 1rem;
  margin-bottom: 1.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--dark-blue);
  margin-bottom: 0.5rem;
}

input {
  width: 100%;
  padding: 1rem 1.2rem;
  border: 2px solid #e8eaf6;
  border-radius: 16px;
  font-size: 1rem;
  background: rgba(255, 255, 255, 0.8);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-sizing: border-box;
}

input:focus {
  outline: none;
  border-color: var(--primary-pink);
  background: white;
  box-shadow: 0 0 0 4px rgba(255, 154, 198, 0.15);
  transform: translateY(-1px);
}

.stripe-input {
  padding: 1rem 1.2rem;
  border: 2px solid #e8eaf6;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.8);
}

.pay-btn {
  width: 100%;
  padding: 1.25rem;
  background: var(--gradient-bg);
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 1.1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  margin-top: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 12px 35px rgba(255, 154, 198, 0.4);
}

.pay-btn:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 25px 50px rgba(255, 154, 198, 0.5);
}

.pay-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.error-msg {
  color: #e53e3e;
  font-size: 0.875rem;
  margin-top: 0.5rem;
  background: rgba(229, 62, 62, 0.1);
  padding: 0.75rem;
  border-radius: 10px;
  border-left: 3px solid #e53e3e;
}

.success-box {
  text-align: center;
  padding: 2.5rem;
  background: rgba(72, 187, 120, 0.15);
  border: 2px solid rgba(72, 187, 120, 0.3);
  border-radius: 20px;
  margin-top: 1rem;
  color: var(--dark-blue);
}

.success-box h4 {
  color: #22c55e;
  font-size: 1.3rem;
  margin-bottom: 0.75rem;
}

.back-home-btn {
  display: inline-block;
  margin-top: 1.5rem;
  padding: 0.75rem 2rem;
  background: var(--gradient-bg);
  color: white;
  text-decoration: none;
  border-radius: 16px;
  font-weight: 600;
}

.loading {
  text-align: center;
  padding: 6rem 2rem;
  color: var(--dark-blue);
  font-size: 1.1rem;
}

@media (max-width: 900px) {
  .payment-layout {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
}
</style>
 