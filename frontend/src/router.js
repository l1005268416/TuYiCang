import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import TextSearch from './views/TextSearch.vue'
import ImageSearch from './views/ImageSearch.vue'
import Album from './views/Album.vue'
import Config from './views/Config.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/text-search', name: 'TextSearch', component: TextSearch },
  { path: '/image-search', name: 'ImageSearch', component: ImageSearch },
  { path: '/album', name: 'Album', component: Album },
  { path: '/config', name: 'Config', component: Config }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
