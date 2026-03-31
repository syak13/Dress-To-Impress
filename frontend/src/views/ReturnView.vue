<template>
  <section class="page">
    <h2>Return a Dress</h2>

    <form class="form" @submit.prevent="handleReturn">
      <h3>Return Details</h3>

      <label>
        Rental ID
        <input v-model="returnForm.reference" type="text" required />
      </label>

      <label>
        Return Date
        <input v-model="returnForm.returnDate" type="date" required />
      </label>

      <div class="upload-group">
        <span class="upload-label">Upload Image</span>

        <input id="uploadImage" type="file" accept="image/*" class="file-input" @change="handleImageUpload" />

        <label for="uploadImage" class="upload-btn">
          <span class="upload-icon">+</span>
          <span>{{ returnImageName || 'Choose image' }}</span>
        </label>

        <p v-if="returnImageName" class="file-name">
          Selected: {{ returnImageName }}
        </p>
      </div>

      <div v-if="showFees" class="fee-grid">
        <label>
          Late Fee
          <input v-model.number="returnForm.lateFee" type="number" min="0" step="0.01" />
        </label>

        <label>
          Damage Fee
          <input v-model.number="returnForm.damageFee" type="number" min="0" step="0.01" />
        </label>
      </div>

      <button type="submit">Submit return</button>

      <p v-if="returnSubmitted" class="success">
        Return submitted. Thank you!
      </p>
    </form>
  </section>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const activeTab = ref('rent')
const selectedDress = ref(null)
const showFees = ref(false)
const returnImage = ref(null)
const returnImageName = ref('')

const getTodayDate = () => {
  return new Date().toISOString().slice(0, 10)
}

onMounted(async () => {
  const dressId = route.params.dressId

  if (dressId) {
    const res = await fetch(`http://localhost:5001/inventory/${dressId}`)
    const data = await res.json()

    if (data.code === 200) {
      selectedDress.value = data.data
      rentForm.dress = `${selectedDress.value.dress_id} - ${selectedDress.value.name}`
    }
  }

  returnForm.returnDate = getTodayDate()
})

const rentForm = reactive({
  name: '',
  dress: '',
  startDate: '',
  endDate: ''
})

const returnForm = reactive({
  reference: '',
  returnDate: getTodayDate(),
  lateFee: 0,
  damageFee: 0
})

const rentSubmitted = ref(false)
const returnSubmitted = ref(false)

const handleImageUpload = (event) => {
  const file = event.target.files?.[0] || null
  returnImage.value = file
  returnImageName.value = file ? file.name : ''
  showFees.value = !!file
}

const handleRent = () => {
  rentSubmitted.value = true
}

const handleReturn = async () => {
  returnSubmitted.value = true
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

.upload-group {
  margin: 1rem 0 1.2rem;
}

.upload-label {
  display: block;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--dark-blue);
  margin-bottom: 0.5rem;
}

.file-input {
  display: none;
}

.upload-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  width: 100%;
  padding: 1rem 1.2rem;
  border-radius: 16px;
  border: 2px dashed rgba(255, 154, 198, 0.6);
  background: linear-gradient(135deg, rgba(255, 240, 248, 0.95), rgba(255, 255, 255, 0.95));
  color: var(--dark-blue);
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

.upload-btn:hover {
  transform: translateY(-2px);
  border-color: var(--primary-pink);
  box-shadow: 0 12px 30px rgba(255, 154, 198, 0.15);
}

.upload-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  background: var(--gradient-bg);
  color: white;
  font-size: 1.2rem;
  line-height: 1;
}

.file-name {
  margin-top: 0.7rem;
  font-size: 0.9rem;
  color: #64748b;
}

.fee-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

h3 {
  color: var(--dark-blue);
  font-size: 1.3rem;
  font-weight: 700;
  margin: 0 0 1.5rem 0;
  text-align: center;
}
</style>        