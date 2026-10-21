import { createRouter, createWebHistory } from 'vue-router'

import AdminLayout from '../layouts/AdminLayout.vue'
import AdminDashboardView from '../views/AdminDashboardView.vue'
import AnnouncementAdminView from '../views/AnnouncementAdminView.vue'
import AnnouncementFormView from '../views/AnnouncementFormView.vue'
import BannerAdminView from '../views/BannerAdminView.vue'
import BannerFormView from '../views/BannerFormView.vue'
import SectionVisualsAdminView from '../views/SectionVisualsAdminView.vue'
import DifyAssistantView from '../views/DifyAssistantView.vue'
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
import { resolveAccess } from '../utils/routeAccess'

const router = createRouter({
  history: createWebHistory(),

  routes: [
    {
      path: '/projects/new',
      name: 'project-new',
      component: () => import('../views/ProjectEditView.vue'),
      meta: { requiresProjectEditor: true },
    },
    {
      path: '/projects/:id/edit',
      name: 'project-edit',
      component: () => import('../views/ProjectEditView.vue'),
      meta: { requiresProjectEditor: true },
    },
    {
      path: '/projects',
      name: 'projects',
      component: () => import('../views/ProjectsView.vue'),
    },
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
      path: '/exchange',
      name: 'exchange',
      component: () => import('../views/ExchangeView.vue'),
    },
    {
      path: '/tools',
      name: 'tools',
      component: ToolsView,
    },
    {
      path: '/assistant',
      name: 'dify-assistant',
      component: DifyAssistantView,
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
          path: 'employees',
          name: 'employees-admin',
          component: () => import('../views/EmployeesAdminView.vue'),
        },
        {
          path: 'projects',
          name: 'projects-admin',
          component: () => import('../views/ProjectsAdminView.vue'),
        },
        {
          path: 'exchange',
          name: 'exchange-admin',
          component: () => import('../views/ExchangeAdminView.vue'),
        },
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
          path: 'content/banners/sections',
          name: 'section-visuals-admin',
          component: SectionVisualsAdminView,
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

router.addRoute({
  path: '/admin/login',
  name: 'admin-login',
  redirect: (to) => ({ name: 'login', query: { ...to.query, redirect: to.query.redirect || '/admin' } }),
})
router.addRoute({
  path: '/change-password',
  name: 'change-password',
  component: () => import('../views/ChangePasswordView.vue'),
  meta: { layout: 'auth' },
})

router.beforeEach((to) => resolveAccess(to))

export default router
