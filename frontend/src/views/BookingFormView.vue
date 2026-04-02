<template>
    <section class="page">
      <div class="availability-layout" v-if="selectedDress">
        <div class="dress-panel">
          <h3>Booking Details</h3>
          <img :src="selectedDress.img" alt="" class="dress-img" />
          <h2>{{ selectedDress.name }}</h2>
          <p class="meta">{{ selectedDress.size }} • {{ selectedDress.color }}</p>
          <p class="meta">Fitting Date: {{ rentForm.startDate }}</p>
        </div>
  
        <div class="calendar-panel">
          <h3>Customer Details</h3>
          <div class="form-group">
        <label>
          Customer Name
          <input required />
        </label>
      </div>

      <div class="form-group">
        <label>
          Phone Number
          <input required />
        </label>
      </div>

      <div class="form-group">
        <label>
          Email
        <input required />
        </label>
      </div>

      <button type="submit" @click="goToPayment">Proceed to payment</button>
        </div>
      </div>
    </section>
  </template>
  
  <script setup>

import { reactive, ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const activeTab = ref('rent')

const selectedDress = ref(null)

onMounted(async () => {
  const dressId = route.params.dressId
  rentForm.startDate = route.query.startDate || ''
  rentForm.endDate = route.query.endDate || ''
  
  if (dressId) {
    // Fetch dress details from backend
    const res = await fetch(`http://localhost:5001/inventory/${dressId}`)
    const data = await res.json()
    
    if (data.code === 200) {
      selectedDress.value = data.data
      // Auto-fill form
      rentForm.dress = `${selectedDress.value.dress_id} - ${selectedDress.value.name}`
      rentForm.size = `${selectedDress.value.size}`
      rentForm.price = `$${selectedDress.value.price}`
      rentForm.img = `${selectedDress.value.img}`
    }
  }
})

const rentForm = reactive({
  name: '',
  dress: '',
  startDate: '',
  endDate: ''
})


const rentSubmitted = ref(false)
const returnSubmitted = ref(false)

const handleRent = () => {
  rentSubmitted.value = true
  // later: POST to backend
}

  
  function goToPayment() {
    router.push({
      path: `/payment/${selectedDress.value.dress_id}`,
      query: {
        startDate: selectedStart.value,
        endDate: selectedEnd.value
      }
    })
  }
  </script>
  
  <style scoped>
  .page {
    max-width: 1100px;
    margin: 3rem auto;
    padding: 0 1rem;
  }
  
  .availability-layout {
    display: grid;
    grid-template-columns: 320px 1fr;
    gap: 2rem;
    align-items: start;
  }
  
  .dress-panel,
  .calendar-panel {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(20px);
    padding: 2rem;
    border-radius: 24px;
    border: 1px solid rgba(255, 154, 198, 0.2);
    box-shadow:
      0 20px 40px rgba(255, 154, 198, 0.15),
      0 0 0 1px rgba(255, 255, 255, 0.9);
    position: relative;
    overflow: hidden;
  }
  
  .dress-panel::before,
  .calendar-panel::before {
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
    max-height: 360px;
    object-fit: cover;
    border-radius: 18px;
    margin-bottom: 1.25rem;
  }
  
  h2 {
    font-size: 1.8rem;
    background: var(--gradient-bg);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.75rem;
    font-weight: 800;
  }
  
  h3 {
    color: var(--dark-blue);
    font-size: 1.2rem;
    font-weight: 700;
    margin: 0 0 1.25rem 0;
    text-align: center;
  }
  
  h4 {
    color: var(--dark-blue);
    font-size: 1rem;
    font-weight: 700;
  }
  
  .meta,
  .price {
    color: var(--dark-blue);
    margin-bottom: 0.5rem;
  }
  
  .price {
    font-weight: 700;
  }
  
  .calendar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  
  .nav-btn {
    width: 42px;
    height: 42px;
    border: none;
    border-radius: 12px;
    background: var(--gradient-bg);
    color: white;
    font-size: 1.2rem;
    font-weight: 700;
    cursor: pointer;
  }
  
  .weekday-row,
  .calendar-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 0.45rem;
  }
  
  .weekday-row {
    margin-bottom: 0.5rem;
  }
  
  .weekday-row span {
    text-align: center;
    font-size: 0.85rem;
    font-weight: 700;
    color: #64748b;
  }
  
  .calendar-day {
    aspect-ratio: 1 / 1;
    border: none;
    border-radius: 12px;
    background: #fff;
    color: var(--dark-blue);
    font-weight: 600;
    cursor: pointer;
    box-shadow: inset 0 0 0 1px #e8eaf6;
  }
  
  .calendar-day.other-month {
    opacity: 0.35;
  }
  
  .calendar-day.unavailable {
    background: #e5e7eb;
    color: #94a3b8;
    cursor: not-allowed;
    box-shadow: inset 0 0 0 1px #d1d5db;
  }
  
  .calendar-day.selected {
    background: var(--gradient-bg);
    color: white;
    box-shadow: none;
  }
  
  .calendar-day.in-range {
    background: rgba(255, 154, 198, 0.18);
    color: var(--dark-blue);
  }
  
  .selection-box {
    margin-top: 1.25rem;
    padding: 1rem;
    border-radius: 14px;
    background: rgba(255, 154, 198, 0.1);
    border: 1px solid rgba(255, 154, 198, 0.2);
  }
  
  .next-btn {
    width: 100%;
    padding: 1rem;
    margin-top: 1rem;
    background: var(--gradient-bg);
    color: white;
    border: none;
    border-radius: 16px;
    font-size: 1rem;
    font-weight: 700;
    cursor: pointer;
    box-shadow: 0 10px 30px rgba(255, 154, 198, 0.4);
  }
  
  @media (max-width: 900px) {
    .availability-layout {
      grid-template-columns: 1fr;
    }
  }

  .form-group {
  margin-bottom: 1.8rem;
  position: relative;
  justify-content: center;
}

input,
textarea,
select {
  width: 100%;
  padding: 1rem 1.2rem;
  border: 2px solid #e8eaf6;
  border-radius: 16px;
  font-size: 1rem;
  background: rgba(255, 255, 255, 0.8);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-sizing: border-box;
}

button[type="submit"] {
  width: 100%;
  padding: 1.2rem;
  background: var(--gradient-bg);
  color: white;
  border: none;
  border-radius: 16px;
  font-size: 1.1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  margin-top: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 10px 30px rgba(255, 154, 198, 0.4);
}

button[type="submit"]:hover {
  transform: translateY(-3px);
  box-shadow: 0 20px 40px rgba(255, 154, 198, 0.5);
}

button[type="submit"]:active {
  transform: translateY(-1px);
}

label {
  display: block;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--dark-blue);
  margin-bottom: 0.5rem;
}
  </style>
  