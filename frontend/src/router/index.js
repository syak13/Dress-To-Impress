import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import BrowseDressesView from '../views/BrowseDressesView.vue'
import ScheduleFittingView from '../views/ScheduleFittingView.vue'
import RentalView from '../views/RentalView.vue'

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/dresses', name: 'browse-dresses', component: BrowseDressesView },
  { path: '/fitting', name: 'schedule-fitting', component: ScheduleFittingView },
  { path: '/rental', name: 'rental', component: RentalView }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router