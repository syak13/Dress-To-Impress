import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import BrowseDressesView from '../views/BrowseDressesView.vue'
import ScheduleFittingView from '../views/ScheduleFittingView.vue'
import RentalView from '../views/RentalView.vue'
import ReturnView from '../views/ReturnView.vue'
import AvailabilityView from '../views/AvailabilityView.vue'

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/dresses', name: 'browse-dresses', component: BrowseDressesView },
  { path: '/fitting', name: 'schedule-fitting', component: ScheduleFittingView },
  { path: '/fitting/:dressId', name: 'schedule-fitting', component: ScheduleFittingView },
  { path: '/rental/:dressId', component: RentalView },
  { path: '/rental', name: 'rental', component: RentalView },
  { path: '/return', name: 'return', component: ReturnView },
  { path: '/availability/:dressId', name: 'availability', component: AvailabilityView }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router