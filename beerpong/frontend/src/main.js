// Inject JWT headers into every fetch() call globally
import './fetch.js'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router/index.js'
import App from './App.vue'

import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap'
import './style.css'

createApp(App)
  .use(createPinia())
  .use(router)
  .mount('#app')
