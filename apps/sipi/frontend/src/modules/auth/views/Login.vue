<!-- Login.vue — acceso real (JWT). Usuario + contraseña. -->
<template>
  <div class="min-h-screen bg-zinc-100 flex items-center justify-center p-4">
    <div class="card p-6 w-full max-w-sm">
      <div class="flex flex-col items-center mb-6">
        <div class="w-11 h-11 rounded-lg bg-primary-600 flex items-center justify-center mb-3">
          <UiIcon name="config" class="w-6 h-6 text-white" />
        </div>
        <h1 class="text-lg font-semibold text-zinc-900">SIPI</h1>
        <p class="text-xs text-zinc-400">Sistema de Información del Patrimonio Inmatriculado</p>
      </div>

      <!-- autocomplete=off: el navegador no memoriza usuario/contraseña -->
      <form class="space-y-3" autocomplete="off" @submit.prevent="onSubmit">
        <div>
          <label class="label">Usuario</label>
          <input v-model="form.nombreUsuario" type="text" autocomplete="off" required
                 class="input font-mono" autofocus />
        </div>
        <div>
          <label class="label">Contraseña</label>
          <input v-model="form.contrasena" type="password" autocomplete="new-password" required class="input" />
        </div>

        <label class="flex items-center gap-2 text-sm text-zinc-600 select-none">
          <input v-model="form.remember" type="checkbox"
                 class="rounded border-zinc-300 text-primary-600 focus:ring-primary-500" />
          Recuérdame
        </label>

        <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

        <UiButton type="submit" variant="primary" icon="check" class="w-full justify-center"
                  :loading="loading" :disabled="!form.nombreUsuario || !form.contrasena">
          Iniciar sesión
        </UiButton>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { useAuth } from '../composables/useAuth'

const { login, loading, error } = useAuth()
const form = reactive({ nombreUsuario: '', contrasena: '', remember: false })

const onSubmit = () => login({ nombreUsuario: form.nombreUsuario, contrasena: form.contrasena, remember: form.remember })
</script>
