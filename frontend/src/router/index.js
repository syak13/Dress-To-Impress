import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import BrowseDressesView from '../views/BrowseDressesView.vue'
import ScheduleFittingView from '../views/ScheduleFittingView.vue'
// import RentalView from '../views/RentalView.vue'
import ReturnView from '../views/ReturnView.vue'
import RentalAvailabilityView from '../views/RentalAvailabilityView.vue'
import BookingFormView from '../views/BookingFormView.vue'
import RentalFormView from '../views/RentalFormView.vue'
import FittingAvailabilityView from '../views/FittingAvailabilityView.vue'

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/dresses', name: 'browse-dresses', component: BrowseDressesView },
  { path: '/fitting', name: 'schedule-fitting', component: ScheduleFittingView },
  { path: '/fitting/:dressId', name: 'schedule-fitting', component: ScheduleFittingView },
  // { path: '/rental/:dressId', component: RentalView },
  // { path: '/rental', name: 'rental', component: RentalView },
  { path: '/return', name: 'return', component: ReturnView },
  { path: '/rentalavailability/:dressId', name: 'rentalavailability', component: RentalAvailabilityView },
  { path: '/bookingform/:dressId', name: 'bookingform', component: BookingFormView},
  { path: '/rentalform/:dressId', name: 'rentalform', component: RentalFormView},
  { path: '/fittingavailability/:dressId', name: 'fittingavailability', component: FittingAvailabilityView }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router