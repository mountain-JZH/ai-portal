import { createRouter, createWebHistory } from 'vue-router'

import AdminLayout from '../layouts/AdminLayout.vue'
import AdminDashboardView from '../views/AdminDashboardView.vue'
import AnnouncementAdminView from '../views/AnnouncementAdminView.vue'
import AnnouncementFormView from '../views/AnnouncementFormView.vue'
import BannerAdminView from '../views/BannerAdminView.vue'
import BannerFormView from '../views/BannerFormView.vue'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import NewsAdminView from '../views/NewsAdminView.vue'
import NewsCreateView from '../views/NewsCreateView.vue'
import NewsDetailView from '../views/NewsDetailView.vue'
import NewsEditView from '../views/NewsEditView.vue'
import NewsView from '../views/NewsView.vue'
import ToolsView from '../views/ToolsView.vue'
import ToolAdminView from '../views/ToolAdminView.vue'
import ToolFormView from '../views/ToolFormView.vue'
import { fetchCurrentAdmin } from '../utils/adminAuth'

const router = createRouter({
  history: createWebHistory(),

  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/news',
      name: 'news',
      component: NewsView,
    },
    {
      path: '/news/:id',
      name: 'news-detail',
      component: NewsDetailView,
    },
    {
      path: '/tools',
      name: 'tools',
      component: ToolsView,
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: {
        layout: 'auth',
      },
    },
    {
      path: '/admin',
      component: AdminLayout,
      meta: {
        layout: 'admin',
        requiresAdmin: true,
      },
      children: [
        {
          path: '',
          name: 'admin-dashboard',
          component: AdminDashboardView,
        },
        {
          path: 'news',
          name: 'news-admin',
          component: NewsAdminView,
        },
        {
          path: 'news/new',
          name: 'news-create',
          component: NewsCreateView,
        },
        {
          path: 'news/:id/edit',
          name: 'news-edit',
          component: NewsEditView,
        },
        {
          path: 'content/banners',
          name: 'banner-admin',
          component: BannerAdminView,
        },
        {
          path: 'content/banners/new',
          name: 'banner-create',
          component: BannerFormView,
        },
        {
          path: 'content/banners/:id/edit',
          name: 'banner-edit',
          component: BannerFormView,
        },
        {
          path: 'content/announcements',
          name: 'announcement-admin',
          component: AnnouncementAdminView,
        },
        {
          path: 'content/announcements/new',
          name: 'announcement-create',
          component: AnnouncementFormView,
        },
        {
          path: 'content/announcements/:id/edit',
          name: 'announcement-edit',
          component: AnnouncementFormView,
        },
        {
          path: 'tools',
          name: 'tool-admin',
          component: ToolAdminView,
        },
        {
          path: 'tools/new',
          name: 'tool-create',
          component: ToolFormView,
        },
        {
          path: 'tools/:id/edit',
          name: 'tool-edit',
          component: ToolFormView,
        },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  if (!to.matched.some((record) => record.meta.requiresAdmin)) return true

  try {
    const admin = await fetchCurrentAdmin()

    if (admin) return true
  } catch {
    // The login page presents the user-facing service error if auth is unavailable.
  }

  return {
    name: 'login',
    query: { redirect: to.fullPath },
  }
})

export default router
