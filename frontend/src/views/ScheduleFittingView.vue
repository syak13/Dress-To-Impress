<template>
  <section class="page">
    <h2>Schedule a fitting</h2>
    <form class="form" @submit.prevent="handleSubmit">
      <div class="form-group">
        <label>
          Full name
          <input v-model="form.name" type="text" required />
        </label>
      </div>

      <div class="form-group">
        <label>
          Email
          <input v-model="form.email" type="email" required />
        </label>
      </div>

      <div class="form-group">
        <label>
          Preferred date
          <input v-model="form.date" type="date" required />
        </label>
      </div>

      <div class="form-group">
        <label>
          Preferred time
          <input v-model="form.time" type="time" required />
        </label>
      </div>

      <div class="form-group">
        <label>
          Notes (optional)
          <textarea v-model="form.notes" rows="3" />
        </label>
      </div>
      <button type="submit">Request fitting</button>

      <p v-if="submitted" class="success">
        We received your request. We will confirm via email.
      </p>
    </form>
  </section>
</template>

<script setup>
import { reactive, ref } from 'vue'

const form = reactive({
  name: '',
  email: '',
  date: '',
  time: '',
  notes: ''
})

const submitted = ref(false)

const handleSubmit = () => {
  // later: send to backend via fetch/axios
  submitted.value = true
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
</style>