<template>
  <!-- Renders the single global header bar shared by every role. -->
  <nav class="navbar navbar-expand-md pp-header sticky-top">
    <div class="container-fluid px-3 px-md-4 pp-header-row">
      <span class="navbar-brand pp-brand">PlacementPro</span>
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#ppNav">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="ppNav">
        <ul class="navbar-nav mx-md-auto pp-tabs pp-tabs-centered">
          <li class="nav-item" v-for="tab in tabs" :key="tab.path">
            <router-link class="nav-link" :class="{ active: isActive(tab.path) }" :to="tab.path">
              {{ tab.label }}
            </router-link>
          </li>
        </ul>
        <div class="d-flex align-items-center pp-user">
          <span class="pp-user-name">{{ auth.name }}</span>
          <button class="btn btn-sm btn-outline-light ms-3" @click="onLogout">Logout</button>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { auth, clearSession } from '@/utils/auth'

// Defines each role's header tabs in display order.
const TAB_CONFIG = {
  ADMIN: [
    { label: 'Overview', path: '/overview' },
    { label: 'Companies', path: '/admin/companies' },
    { label: 'Placement Drives', path: '/admin/drives' },
    { label: 'Applications', path: '/admin/applications' },
    { label: 'Students', path: '/admin/students' },
    { label: 'Interviews', path: '/admin/interviews' },
  ],
  COMPANY: [
    { label: 'Overview', path: '/company/overview' },
    { label: 'Placement Drives', path: '/company/drives' },
    { label: 'Applications', path: '/company/applications' },
    { label: 'Interviews', path: '/company/interviews' },
    { label: 'Profile', path: '/company/profile' },
  ],
  STUDENT: [
    { label: 'Placement Drives', path: '/student/drives' },
    { label: 'Applications', path: '/student/applications' },
    { label: 'Profile', path: '/student/profile' },
  ],
}

const route = useRoute()
const router = useRouter()

// Resolves the current role's tab list.
const tabs = computed(() => TAB_CONFIG[auth.role] || [])

// Determines whether a given tab path matches the active route.
function isActive(path) {
  return route.path === path
}

// Clears the session and returns the user to the login screen.
function onLogout() {
  clearSession()
  router.push('/login')
}
</script>

<style scoped>
.pp-header {
  background: var(--pp-primary);
  padding: 0.65rem 0;
}
.pp-brand {
  color: #fff;
  font-weight: 700;
  letter-spacing: 0.02em;
  margin-right: 2rem;
}
.pp-header-row {
  position: relative;
}
.pp-tabs .nav-item {
  margin: 0 0.15rem;
}
.pp-tabs .nav-link {
  color: rgba(255, 255, 255, 0.78);
  font-weight: 500;
  padding: 0.6rem 1.1rem;
  border-radius: 6px;
  transition: background-color 0.15s ease, color 0.15s ease;
}
@media (min-width: 768px) {
  .pp-tabs-centered {
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
  }
}
.pp-tabs .nav-link:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
}
.pp-tabs .nav-link.active {
  color: #fff;
  background: rgba(255, 255, 255, 0.18);
}
.pp-user-name {
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}
</style>
