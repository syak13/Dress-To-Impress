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
import LoginView from '../views/LoginView.vue'
import PaymentView from '../views/PaymentView.vue'

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/login', name: 'login', component: LoginView },
  { path: '/dresses', name: 'browse-dresses', component: BrowseDressesView },
  { path: '/fitting', name: 'schedule-fitting', component: ScheduleFittingView },
  { path: '/fitting/:dressId', name: 'schedule-fitting-dress', component: ScheduleFittingView },
  // { path: '/rental/:dressId', component: RentalView },
  // { path: '/rental', name: 'rental', component: RentalView },
  { path: '/return', name: 'return', component: ReturnView, meta: { requiresAuth: true, role: 'employee' } },
  { path: '/rentalavailability/:dressId', name: 'rentalavailability', component: RentalAvailabilityView, meta: { requiresAuth: true, role: 'customer' } },
  { path: '/bookingform/:dressId', name: 'bookingform', component: BookingFormView, meta: { requiresAuth: true, role: 'customer' } },
  { path: '/rentalform/:dressId', name: 'rentalform', component: RentalFormView, meta: { requiresAuth: true, role: 'customer' } },
  { path: '/fittingavailability/:dressId', name: 'fittingavailability', component: FittingAvailabilityView, meta: { requiresAuth: true, role: 'customer' } },
  { path: '/payment/:dressId', name: 'payment', component: PaymentView, meta: { requiresAuth: true, role: 'customer' } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  const raw = localStorage.getItem('dti_user')
  const user = raw ? JSON.parse(raw) : null

  if (to.meta.requiresAuth && !user) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  // Employee tries to access a customer-only page → redirect to return
  if (to.meta.role === 'customer' && user?.role === 'employee') {
    return { name: 'return' }
  }

  // Customer tries to access employee-only page → redirect to home
  if (to.meta.role === 'employee' && user?.role === 'customer') {
    return { name: 'home' }
  }
})

export default router
