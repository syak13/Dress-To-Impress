<template>
  <section class="page">
    <h2>Return a dress</h2>

    <!-- <div class="tabs">
      <button :class="{ active: activeTab === 'rent' }" @click="activeTab = 'rent'">
        Rent a dress
      </button>
      <button :class="{ active: activeTab === 'return' }" @click="activeTab = 'return'">
        Return a dress
      </button>
    </div> -->

    <!-- <form v-if="activeTab === 'rent'" class="form" @submit.prevent="handleRent">
      <h3>Rental details</h3>

      <div v-if="selectedDress" class="dress-preview">
        <h4>Selected: {{ selectedDress.name }} ({{ selectedDress.size }})</h4>
        <p>Price: ${{ selectedDress.price }}/day</p>
        <p>Available: {{ selectedDress.is_available ? 'Yes' : 'No' }}</p>
      </div>

      <div class="form-group">
        <label>
          Dress ID / Name
          <input v-model="rentForm.dress" type="text" readonly />
        </label>
      </div>

      <div class="form-group">
        <label>
          Customer name
          <input v-model="rentForm.name" type="text" required />
        </label>
      </div>
      
      <div class="form-group">
        <label>
          Rental start date
          <input v-model="rentForm.startDate" type="date" required />
        </label>
      </div>

      <div class="form-group">
        <label>
          Return date
          <input v-model="rentForm.endDate" type="date" required />
        </label>
      </div>

      <button type="submit">Place rental</button>

      <p v-if="rentSubmitted" class="success">
        Rental placed. We will email your confirmation.
      </p>
    </form> -->

    <form class="form" @submit.prevent="handleReturn">
      <h3>Return details</h3>

      <label>
        Rental reference
        <input v-model="returnForm.reference" type="text" required />
      </label>

      <label>
        Return date
        <input v-model="returnForm.returnDate" type="date" required />
      </label>

      <label>
        Condition notes (optional)
        <textarea v-model="returnForm.notes" rows="3" />
      </label>

      <button type="submit">Submit return</button>

      <p v-if="returnSubmitted" class="success">
        Return submitted. Thank you!
      </p>
    </form>
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
  
  if (dressId) {
    // Fetch dress details from backend
    const res = await fetch(`http://localhost:5001/inventory/${dressId}`)
    const data = await res.json()
    
    if (data.code === 200) {
      selectedDress.value = data.data
      // Auto-fill form
      rentForm.dress = `${selectedDress.value.dress_id} - ${selectedDress.value.name}`
    }
  }
})

const rentForm = reactive({
  name: '',
  dress: '',
  startDate: '',
  endDate: ''
})

const returnForm = reactive({
  reference: '',
  returnDate: '',
  notes: ''
})

const rentSubmitted = ref(false)
const returnSubmitted = ref(false)

const handleRent = () => {
  rentSubmitted.value = true
  // later: POST to backend
}

const handleReturn = () => {
  returnSubmitted.value = true
  // later: POST to backend
}
</script>

<style scoped>
.page {
  max-width: 500px;
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

.form {
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

.form::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--gradient-bg);
}

.form-group {
  margin-bottom: 1.8rem;
  position: relative;
}

label {
  display: block;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--dark-blue);
  margin-bottom: 0.5rem;
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

input:focus,
textarea:focus,
select:focus {
  outline: none;
  border-color: var(--primary-pink);
  background: white;
  box-shadow:
    0 0 0 4px rgba(255, 154, 198, 0.15),
    0 8px 25px rgba(255, 154, 198, 0.1);
  transform: translateY(-1px);
}

textarea {
  resize: vertical;
  min-height: 100px;
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

.success {
  background: rgba(34, 197, 94, 0.15);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 12px;
  padding: 1rem;
  color: #166534;
  font-weight: 500;
  text-align: center;
  margin-top: 1.5rem;
}

/* Tabs for Rental page */
.tabs {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 16px;
  padding: 0.25rem;
  backdrop-filter: blur(10px);
}

.tabs button {
  flex: 1;
  padding: 1rem;
  border: none;
  border-radius: 14px;
  background: transparent;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tabs button.active {
  background: var(--gradient-bg);
  color: white;
  box-shadow: 0 8px 25px rgba(255, 154, 198, 0.3);
}

h3 {
  color: var(--dark-blue);
  font-size: 1.3rem;
  font-weight: 700;
  margin: 0 0 1.5rem 0;
  text-align: center;
}

.dress-preview {
  background: #f0f8ff;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  border-left: 4px solid var(--pastel-blue);
}

input[readonly] {
  background: #f8f9fa;
  color: #666;
}

</style>