<template>
  <section class="page">
    <h2>Return a Dress</h2>

    <!-- ── Phase 1: Rental lookup ─────────────────────────────────────────── -->
    <div v-if="phase === 1" class="card">
      <h3>Return Details</h3>

      <div class="form-group">
        <label>Rental ID</label>
        <input v-model="rentalId" type="text" placeholder="e.g. 2" />
      </div>

      <div class="form-group">
        <label>Return Date</label>
        <input v-model="returnDate" type="date" :max="today" />
      </div>

      <p v-if="lookupError" class="error-msg">{{ lookupError }}</p>

      <button class="btn-primary" @click="proceedToReturn" :disabled="lookupLoading">
        {{ lookupLoading ? 'Checking...' : 'Proceed to Return' }}
      </button>
    </div>

    <!-- ── Phase 2: Image comparison + upload ─────────────────────────────── -->
    <div v-else-if="phase === 2" class="card wide">
      <h3>Submit Return — Rental #{{ rentalId }}</h3>

      <div class="image-row">
        <!-- Left: actual dress from DB -->
        <div class="image-box">
          <p class="image-label">Actual Dress</p>
          <img :src="dressImage" alt="Dress" class="dress-img" />
        </div>

        <!-- Right: customer upload -->
        <div class="image-box">
          <p class="image-label">Upload Return Image</p>
          <div class="upload-area" :class="{ 'upload-error': notDressError }" @click="triggerUpload">
            <img v-if="uploadPreview && !notDressError" :src="uploadPreview" class="dress-img" alt="Uploaded" />
            <div v-else class="upload-placeholder">
              <span class="upload-icon" :style="notDressError ? 'background: #e53e3e' : ''">{{ notDressError ? '✕' : '+' }}</span>
              <span v-if="notDressError" style="color: #c53030; font-weight: 700; text-align: center;">
                That doesn't look like a dress.<br/>Click to upload again.
              </span>
              <span v-else>Click to upload image</span>
            </div>
          </div>
          <input
            id="upload-input"
            type="file"
            accept="image/*"
            class="hidden-input"
            @change="handleImageUpload"
          />
          <p v-if="uploadedFile && !notDressError" class="file-info">{{ uploadedFile.name }}</p>
        </div>
      </div>

      <p v-if="submitError" class="error-msg">{{ submitError }}</p>

      <button
        class="btn-primary"
        @click="submitReturn"
        :disabled="!uploadedFile || submitLoading"
      >
        {{ submitLoading ? 'Processing...' : 'Submit Return' }}
      </button>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const phase      = ref(1)
const today      = new Date().toISOString().slice(0, 10)
const rentalId   = ref('')
const returnDate = ref(today)

const lookupError   = ref('')
const lookupLoading = ref(false)

const dressImage  = ref('')
const rentalData  = ref(null)

const uploadedFile   = ref(null)
const uploadPreview  = ref('')
const submitError    = ref('')
const submitLoading  = ref(false)
const notDressError  = ref(false)

function triggerUpload() {
  document.getElementById('upload-input').click()
}

function handleImageUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return
  uploadedFile.value  = file
  uploadPreview.value = URL.createObjectURL(file)
  notDressError.value = false
  submitError.value   = ''
}

async function proceedToReturn() {
  if (!rentalId.value || !returnDate.value) {
    lookupError.value = 'Please fill in both Rental ID and Return Date.'
    return
  }

  lookupLoading.value = true
  lookupError.value   = ''

  try {
    const res  = await fetch(`http://localhost:8000/rental/${rentalId.value}`)
    const data = await res.json()

    if (res.status === 404 || data.code === 404) {
      lookupError.value = 'No such Rental ID found.'
      return
    }

    const rental = data.data

    if (rental.status === 'COMPLETED' || rental.status === 'CANCELLED') {
      lookupError.value = `This order has been closed. Its status is "${rental.status}".`
      return
    }

    if (rental.status !== 'ACTIVE') {
      lookupError.value = `Rental is not active (status: ${rental.status}).`
      return
    }

    rentalData.value = rental

    // Fetch dress image from inventory
    const invRes  = await fetch(`http://localhost:8000/inventory/${rental.dress_id}`)
    const invData = await invRes.json()
    if (invData.code === 200) {
      dressImage.value = invData.data.img
    }

    phase.value = 2
  } catch {
    lookupError.value = 'Failed to connect to server. Please try again.'
  } finally {
    lookupLoading.value = false
  }
}

async function submitReturn() {
  if (!uploadedFile.value) return

  submitLoading.value = true
  submitError.value   = ''

  const formData = new FormData()
  formData.append('rental_id',   rentalId.value)
  formData.append('return_date', returnDate.value)
  formData.append('image',       uploadedFile.value)

  try {
    const res  = await fetch('http://localhost:8000/return/image', {
      method: 'POST',
      body:   formData
    })
    const data = await res.json()

    if (data.code !== 200) {
      if (data.message === 'not_a_dress') {
        notDressError.value = true
        uploadedFile.value  = null
        uploadPreview.value = ''
      } else {
        submitError.value = data.message || 'Failed to process return.'
      }
      return
    }

    router.push({ name: 'invoice', state: { invoice: data.data } })
  } catch {
    submitError.value = 'Failed to submit return. Please try again.'
  } finally {
    submitLoading.value = false
  }
}
</script>

<style scoped>
.page {
  max-width: 900px;
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
  max-width: 500px;
  margin: 0 auto;
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

.card.wide {
  max-width: 820px;
}

.card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 4px;
  background: var(--gradient-bg);
}

h3 {
  color: var(--dark-blue);
  font-size: 1.3rem;
  font-weight: 700;
  margin: 0 0 1.5rem 0;
  text-align: center;
}

.form-group {
  margin-bottom: 1.2rem;
}

label {
  display: block;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--dark-blue);
  margin-bottom: 0.5rem;
}

input[type="text"],
input[type="date"] {
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

.btn-primary {
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

.btn-primary:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 20px 40px rgba(255, 154, 198, 0.5);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.error-msg {
  background: rgba(229, 62, 62, 0.1);
  border: 1px solid rgba(229, 62, 62, 0.3);
  border-radius: 12px;
  padding: 0.9rem 1rem;
  color: #c53030;
  font-size: 0.95rem;
  margin-top: 0.75rem;
}

/* ── Phase 2 styles ──────────────────────────────────────────── */
.image-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.image-box {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.image-label {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--dark-blue);
  text-align: center;
  margin: 0;
}

.dress-img {
  width: 100%;
  height: 320px;
  object-fit: cover;
  border-radius: 16px;
  border: 2px solid rgba(255, 154, 198, 0.2);
}

.upload-area {
  width: 100%;
  height: 320px;
  border-radius: 16px;
  border: 2px dashed rgba(255, 154, 198, 0.6);
  background: linear-gradient(135deg, rgba(255, 240, 248, 0.95), rgba(255, 255, 255, 0.95));
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  transition: all 0.3s ease;
}

.upload-area:hover {
  border-color: var(--primary-pink);
  box-shadow: 0 8px 24px rgba(255, 154, 198, 0.2);
}

.upload-area.upload-error {
  border-color: rgba(229, 62, 62, 0.6);
  background: rgba(254, 242, 242, 0.95);
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.6rem;
  color: var(--dark-blue);
  font-weight: 600;
  font-size: 0.95rem;
}

.upload-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 999px;
  background: var(--gradient-bg);
  color: white;
  font-size: 1.8rem;
  line-height: 1;
}

.hidden-input {
  display: none;
}

.file-info {
  text-align: center;
  font-size: 0.88rem;
  color: #64748b;
  margin: 0;
}

@media (max-width: 600px) {
  .image-row {
    grid-template-columns: 1fr;
  }
}
</style>
