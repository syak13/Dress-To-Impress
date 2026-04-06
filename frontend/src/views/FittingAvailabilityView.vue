<template>
  <section class="page">
    <div class="availability-layout" v-if="selectedDress">
      <div class="dress-panel">
        <img :src="selectedDress.img" alt="" class="dress-img" />
        <h2>{{ selectedDress.name }}</h2>
        <p class="meta">{{ selectedDress.size }} • {{ selectedDress.color }}</p>
        <p class="price">${{ selectedDress.price }}/day</p>
      </div>

      <div class="calendar-panel">
        <h3>Select fitting date</h3>

        <div class="calendar-header">
          <button type="button" class="nav-btn" @click="prevMonth">‹</button>
          <h4>{{ currentMonthLabel }}</h4>
          <button type="button" class="nav-btn" @click="nextMonth">›</button>
        </div>

        <div class="weekday-row">
          <span v-for="day in weekdays" :key="day">{{ day }}</span>
        </div>

        <div class="calendar-grid">
          <button
            v-for="day in calendarDays"
            :key="day.date"
            type="button"
            class="calendar-day"
            :class="{
              'other-month': !day.inCurrentMonth,
              'unavailable': isUnavailable(day.date),
              'selected': isSelected(day.date)
            }"
            :disabled="isUnavailable(day.date)"
            @click="selectDate(day.date)"
          >
            {{ day.dayNumber }}
          </button>
        </div>

        <button
          v-if="selectedDate"
          type="button"
          class="next-btn"
          @click="goToFitting"
        >
          Next
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const selectedDress = ref(null)
const selectedDate = ref('')
const currentMonth = ref(new Date())

const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

onMounted(async () => {
  const dressId = route.params.dressId
  if (!dressId) return

  const res = await fetch(`http://localhost:8000/fitting/dresses/${dressId}`)
  const data = await res.json()

  if (data.code === 200) {
    selectedDress.value = data.data
  }
})

const currentMonthLabel = computed(() => {
  return currentMonth.value.toLocaleString('en-US', {
    month: 'long',
    year: 'numeric'
  })
})

const calendarDays = computed(() => {
  const year = currentMonth.value.getFullYear()
  const month = currentMonth.value.getMonth()

  const firstDayOfMonth = new Date(year, month, 1)
  const startDay = firstDayOfMonth.getDay()
  const gridStart = new Date(year, month, 1 - startDay)

  const days = []

  for (let i = 0; i < 42; i++) {
    const date = new Date(gridStart)
    date.setDate(gridStart.getDate() + i)

    days.push({
      date: formatDate(date),
      dayNumber: date.getDate(),
      inCurrentMonth: date.getMonth() === month
    })
  }

  return days
})

function formatDate(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function formatDisplayDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('en-SG', {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

function prevMonth() {
  const d = currentMonth.value
  currentMonth.value = new Date(d.getFullYear(), d.getMonth() - 1, 1)
}

function nextMonth() {
  const d = currentMonth.value
  currentMonth.value = new Date(d.getFullYear(), d.getMonth() + 1, 1)
}

function isUnavailable(dateStr) {
  // Check if date is in unavailable_dates (backend sends YYYY-MM-DD HH:MM:SS)
  // Frontend compares YYYY-MM-DD, so strip time from backend dates for comparison
  const unavailable = selectedDress.value?.unavailable_dates || []
  return unavailable.some(unavailDate => {
    const dateOnly = unavailDate.split(' ')[0]
    return dateOnly === dateStr
  })
}

function selectDate(dateStr) {
  if (isUnavailable(dateStr)) return
  selectedDate.value = dateStr
}

function isSelected(dateStr) {
  return dateStr === selectedDate.value
}

function goToFitting() {
  // Convert YYYY-MM-DD to YYYY-MM-DD 10:00:00 to match backend format
  const fittingDateTime = `${selectedDate.value} 10:00:00`
  
  router.push({
    path: `/bookingform/${selectedDress.value.dress_id}`,
    query: {
      fittingDate: fittingDateTime  // Now sends "2026-04-16 10:00:00"
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
</style>