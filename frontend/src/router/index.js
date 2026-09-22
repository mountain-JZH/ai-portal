import { createRouter, createWebHistory } from 'vue-router'

import AdminLayout from '../layouts/AdminLayout.vue'
import AdminDashboardView from '../views/AdminDashboardView.vue'
import HomeView from '../views/HomeView.vue'
import NewsAdminView from '../views/NewsAdminView.vue'
import NewsCreateView from '../views/NewsCreateView.vue'
import NewsDetailView from '../views/NewsDetailView.vue'
import NewsEditView from '../views/NewsEditView.vue'
import NewsView from '../views/NewsView.vue'
import ToolsView from '../views/ToolsView.vue'
import KnowledgeView from '../views/KnowledgeView.vue'

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
      path: '/knowledge',
      name: 'knowledge',
      component: KnowledgeView,
    },
    {
      path: '/admin',
      component: AdminLayout,
      meta: {
        layout: 'admin',
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
      ],
    },
  ],
})

export default router
