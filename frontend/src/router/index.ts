import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/pages/HomePage.vue'),
    },
    {
      path: '/memories',
      name: 'memories',
      component: () => import('@/pages/MemoriesPage.vue'),
    },
    {
      path: '/memories/:id',
      name: 'memory-detail',
      component: () => import('@/pages/MemoryDetailPage.vue'),
    },
    {
      path: '/graph',
      name: 'graph',
      component: () => import('@/pages/GraphPage.vue'),
    },
    {
      path: '/analytics',
      name: 'analytics',
      component: () => import('@/pages/AnalyticsPage.vue'),
    },
    {
      path: '/compare',
      name: 'compare',
      component: () => import('@/pages/ComparePage.vue'),
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/pages/SettingsPage.vue'),
    },
    {
      path: '/insight/weekly',
      name: 'insight-weekly',
      component: () => import('@/pages/InsightWeeklyPage.vue'),
    },
    {
      path: '/insight/monthly',
      name: 'insight-monthly',
      component: () => import('@/pages/InsightMonthlyPage.vue'),
    },
    {
      path: '/insight/archive',
      name: 'insight-archive',
      component: () => import('@/pages/InsightArchivePage.vue'),
    },
    {
      path: '/insight/archive/:id',
      name: 'insight-detail',
      component: () => import('@/pages/InsightDetailPage.vue'),
    },
  ],
})

export default router
