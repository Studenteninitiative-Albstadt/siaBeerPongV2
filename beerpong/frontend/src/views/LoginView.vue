<template>
  <div class="min-vh-100 d-flex align-items-center justify-content-center"
       style="background:radial-gradient(circle at top,#1f1f1f 0%,#0d0d0d 55%,#000 100%)">
    <div class="card bg-black border-secondary text-light" style="width:360px">
      <div class="card-body p-4">
        <h3 class="text-center mb-1">🍺 BeerPong</h3>
        <p class="text-center text-secondary small mb-4">Tournament Manager</p>

        <form @submit.prevent="handleLogin">
          <div class="mb-3">
            <label class="form-label text-secondary small">Benutzername</label>
            <input v-model="username" type="text"
                   class="form-control bg-dark text-light border-secondary"
                   :disabled="loading" required autocomplete="username" />
          </div>
          <div class="mb-4">
            <label class="form-label text-secondary small">Passwort</label>
            <input v-model="password" type="password"
                   class="form-control bg-dark text-light border-secondary"
                   :disabled="loading" required autocomplete="current-password" />
          </div>

          <div v-if="error" class="alert alert-danger py-2 small mb-3">{{ error }}</div>

          <button type="submit" class="btn btn-primary w-100" :disabled="loading">
            {{ loading ? 'Anmelden…' : 'Anmelden' }}
          </button>
        </form>

        <hr class="border-secondary mt-4 mb-3" />
        <p class="text-secondary small text-center mb-0">
          Standard-Zugänge (erste Inbetriebnahme):<br>
          <code>admin / admin</code> · <code>live / live</code>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const auth   = useAuthStore()
const router = useRouter()

const username = ref('')
const password = ref('')
const loading  = ref(false)
const error    = ref('')

async function handleLogin() {
  error.value   = ''
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    router.push(auth.isOrga ? '/admin' : '/live')
  } catch {
    error.value = 'Ungültige Anmeldedaten.'
  } finally {
    loading.value = false
  }
}
</script>
