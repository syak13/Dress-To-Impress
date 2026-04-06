<template>
  <section>
    <h2>Browse dresses</h2>

    <div class="filters">
      <label>
        Size
        <select v-model="filters.size">
          <option value="">Any</option>
          <option v-for="size in sizes" :key="size" :value="size">
            {{ size }}
          </option>
        </select>
      </label>

      <label>
        Color
        <select v-model="filters.color">
          <option value="">Any</option>
          <option v-for="color in colors" :key="color" :value="color">
            {{ color }}
          </option>
        </select>
      </label>
    </div>

    <div class="grid">
      <DressCard v-for="dress in filteredDresses" :key="dress.dress_id" :dress="dress" />
      <!-- <DressCard v-for="dress in filteredDresses" :key="dress.id" :dress="dress" /> -->
    </div>
  </section>
</template>

<script setup>
import { computed, reactive, ref, onMounted } from 'vue'
import DressCard from '../components/DressCard.vue'

const dresses = ref([])
// [
//   { id: 1, name: 'Blush Satin Gown', size: 'S', color: 'Pink', pricePerDay: '$45', gradient: '135deg, #ff9ac6, #ffd4e6' },
//   { id: 2, name: 'Royal Blue Gown', size: 'M', color: 'Blue', pricePerDay: '$60', gradient: '135deg, #a2c8f0, #d4e6ff' },
//   { id: 3, name: 'Emerald Chiffon', size: 'L', color: 'Green', pricePerDay: '$55', gradient: '135deg, #a8e6cf, #dcedc1' },
//   { id: 4, name: 'Ivory Lace Maxi', size: 'S', color: 'Ivory', pricePerDay: '$50', gradient: '135deg, #f8f1e9, #e8e2d4' },
//   { id: 5, name: 'Navy Velvet', size: 'M', color: 'Navy', pricePerDay: '$65', gradient: '135deg, #1e3a8a, #3b82f6' },
//   { id: 6, name: 'Lavender Tulle', size: 'L', color: 'Lavender', pricePerDay: '$48', gradient: '135deg, #c7ceea, #f3e5f5' },
//   { id: 7, name: 'Ruby Red Mermaid', size: 'S', color: 'Red', pricePerDay: '$70', gradient: '135deg, #ff6b6b, #ff8e8e' },
//   { id: 8, name: 'Champagne Silk', size: 'M', color: 'Gold', pricePerDay: '$52', gradient: '135deg, #f4c430, #ffeaa7' },
//   { id: 9, name: 'Sapphire Off-Shoulder', size: 'L', color: 'Sapphire', pricePerDay: '$58', gradient: '135deg, #4dabf7, #a2c8f0' }
// ]

const sizes = ['XS', 'S', 'M', 'L', 'XL']
const colors = ['Pink', 'Navy', 'Black', 'Red', 'Green']

const filters = reactive({
  size: '',
  color: ''
})

const fetchDresses = async () => {
  try {
    const res = await fetch('http://localhost:8000/fitting/dresses')
    const data = await res.json()

    if (data.code === 200) {
      dresses.value = data.data.dresses
    } else {
      console.error(data.message)
    }
  } catch (err) {
    console.error('Error fetching dresses:', err)
  }
}

onMounted(() => {
  fetchDresses()
})

const filteredDresses = computed(() => {
  return dresses.value.filter(d => {
    const sizeOk = !filters.size || d.size === filters.size
    const colorOk = !filters.color || d.color === filters.color
    return sizeOk && colorOk // remove color filter unless backend supports it
  })
})

// const filteredDresses = computed(() => {
//   return dresses.filter(d => {
//     const sizeOk = !filters.size || d.size === filters.size
//     const colorOk = !filters.color || d.color === filters.color
//     return sizeOk && colorOk
//   })
// })
</script>

<style scoped>
section {
  max-width: 1200px;
  margin: 0 auto;
}

h2 {
  font-size: 2.5rem;
  background: var(--gradient-bg);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-align: center;
  margin-bottom: 3rem;
}

.filters {
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin-bottom: 3rem;
  flex-wrap: wrap;
}

select {
  padding: 0.75rem 1rem;
  border: 2px solid var(--pastel-blue);
  border-radius: 12px;
  background: white;
  font-size: 1rem;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 2rem;
}
</style>