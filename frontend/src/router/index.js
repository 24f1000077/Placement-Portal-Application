import { createRouter, createWebHistory } from 'vue-router'
import { auth, homeForRole } from '@/utils/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/login' },
    { path: '/login', name: 'login', component: () => import('@/views/public/Login.vue'), meta: { public: true } },
    { path: '/register/student', name: 'register-student', component: () => import('@/views/public/RegisterStudent.vue'), meta: { public: true } },
    { path: '/register/company', name: 'register-company', component: () => import('@/views/public/RegisterCompany.vue'), meta: { public: true } },

    { path: '/overview', name: 'admin-overview', component: () => import('@/views/admin/AdminOverview.vue'), meta: { role: 'ADMIN' } },
    { path: '/admin/companies', name: 'admin-companies', component: () => import('@/views/admin/AdminCompanies.vue'), meta: { role: 'ADMIN' } },
    { path: '/admin/drives', name: 'admin-drives', component: () => import('@/views/admin/AdminDrives.vue'), meta: { role: 'ADMIN' } },
    { path: '/admin/applications', name: 'admin-applications', component: () => import('@/views/admin/AdminApplications.vue'), meta: { role: 'ADMIN' } },
    { path: '/admin/students', name: 'admin-students', component: () => import('@/views/admin/AdminStudents.vue'), meta: { role: 'ADMIN' } },
    { path: '/admin/interviews', name: 'admin-interviews', component: () => import('@/views/admin/AdminInterviews.vue'), meta: { role: 'ADMIN' } },

    { path: '/company/overview', name: 'company-overview', component: () => import('@/views/company/CompanyOverview.vue'), meta: { role: 'COMPANY' } },
    { path: '/company/drives', name: 'company-drives', component: () => import('@/views/company/CompanyDrives.vue'), meta: { role: 'COMPANY' } },
    { path: '/company/applications', name: 'company-applications', component: () => import('@/views/company/CompanyApplications.vue'), meta: { role: 'COMPANY' } },
    { path: '/company/interviews', name: 'company-interviews', component: () => import('@/views/company/CompanyInterviews.vue'), meta: { role: 'COMPANY' } },
    { path: '/company/profile', name: 'company-profile', component: () => import('@/views/company/CompanyProfile.vue'), meta: { role: 'COMPANY' } },

    { path: '/student/drives', name: 'student-drives', component: () => import('@/views/student/StudentDrives.vue'), meta: { role: 'STUDENT' } },
    { path: '/student/applications', name: 'student-applications', component: () => import('@/views/student/StudentApplications.vue'), meta: { role: 'STUDENT' } },
    { path: '/student/profile', name: 'student-profile', component: () => import('@/views/student/StudentProfile.vue'), meta: { role: 'STUDENT' } },
  ],
})

// Guards every route against the required auth/role state.
router.beforeEach((to) => {
  if (to.meta.public) {
    if (auth.token && to.name === 'login') return homeForRole(auth.role)
    return true
  }
  if (!auth.token) return '/login'
  if (to.meta.role && to.meta.role !== auth.role) return homeForRole(auth.role)
  return true
})

export default router
