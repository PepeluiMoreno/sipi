<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl">
      <!-- Header -->
      <div class="px-6 py-4 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">
          {{ isEditing ? 'Editar Usuario' : 'Crear Nuevo Usuario' }}
        </h2>
      </div>

      <!-- Formulario -->
      <form @submit.prevent="saveUser">
        <!-- Contenido del formulario -->
        <div class="p-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Columna Izquierda - Información Personal -->
            <div class="space-y-4">
              <h3 class="text-md font-semibold text-gray-900 border-b pb-2">Información Personal</h3>
              
              <!-- Foto de perfil -->
              <div class="flex items-center space-x-4 mb-2">
                <div class="relative">
                  <div 
                    class="w-20 h-20 bg-indigo-100 rounded-full flex items-center justify-center overflow-hidden border-2 border-gray-300"
                    :class="{ 'border-indigo-500': formData.avatar }"
                  >
                    <img 
                      v-if="formData.avatar" 
                      :src="formData.avatar" 
                      alt="Foto de perfil"
                      class="w-full h-full object-cover"
                    >
                    <UserIcon v-else class="w-8 h-8 text-indigo-600" />
                  </div>
                  <button
                    type="button"
                    @click="openPhotoUpload"
                    class="absolute -bottom-1 -right-1 bg-indigo-600 text-white p-1.5 rounded-full hover:bg-indigo-700 transition-colors shadow-lg"
                    title="Cambiar foto"
                  >
                    <CameraIcon class="w-3 h-3" />
                  </button>
                </div>
                <div>
                  <p class="text-sm font-medium text-gray-900">Foto de perfil</p>
                  <p class="text-xs text-gray-500 mt-1">Haz clic para cambiar la imagen</p>
                  <button
                    v-if="formData.avatar"
                    type="button"
                    @click="removePhoto"
                    class="text-xs text-red-600 hover:text-red-700 mt-1"
                  >
                    Eliminar foto
                  </button>
                </div>
              </div>

              <!-- Nombre y Apellidos en misma línea -->
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Nombre *
                  </label>
                  <input
                    v-model="formData.nombre"
                    type="text"
                    required
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                    placeholder="Nombre"
                  >
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Apellidos *
                  </label>
                  <input
                    v-model="formData.apellidos"
                    type="text"
                    required
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                    placeholder="Apellidos"
                  >
                </div>
              </div>

              <!-- Email -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Email *
                </label>
                <input
                  v-model="formData.email"
                  type="email"
                  required
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                  placeholder="usuario@empresa.com"
                >
              </div>

              <!-- Nombre de Usuario -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Nombre de Usuario *
                </label>
                <input
                  v-model="formData.nombre_usuario"
                  type="text"
                  required
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                  placeholder="nombre.usuario"
                >
              </div>

              <!-- Teléfono y Organización -->
              <div class="grid grid-cols-1 gap-3">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Teléfono
                  </label>
                  <input
                    v-model="formData.telefono"
                    type="tel"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                    placeholder="+34 600 000 000"
                  >
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Organización *
                  </label>
                  <select
                    v-model="formData.organizacion"
                    required
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 text-sm bg-white"
                  >
                    <option value="">Seleccione una organización</option>
                    <option 
                      v-for="org in organizaciones" 
                      :key="org.id" 
                      :value="org.id"
                    >
                      {{ org.nombre }}
                    </option>
                  </select>
                </div>
              </div>
            </div>

            <!-- Columna Derecha - Credenciales y Roles -->
            <div class="space-y-4">
              <h3 class="text-md font-semibold text-gray-900 border-b pb-2">Credenciales y Permisos</h3>
              
              <!-- Contraseñas (solo para nuevo usuario) -->
              <div v-if="!isEditing" class="space-y-3">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Contraseña *
                  </label>
                  <input
                    v-model="formData.contrasena"
                    type="password"
                    required
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                    placeholder="Mínimo 6 caracteres"
                  >
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Confirmar Contraseña *
                  </label>
                  <input
                    v-model="formData.confirmar_contrasena"
                    type="password"
                    required
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                    placeholder="Repite la contraseña"
                  >
                </div>
              </div>

              <!-- Selección de Rol -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-3">
                  Rol del Usuario *
                </label>
                <div class="space-y-2">
                  <div
                    v-for="role in availableRoles"
                    :key="role.id"
                    class="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                    :class="{ 'bg-indigo-50 border-indigo-200': formData.rolSeleccionado === role.id }"
                    @click="formData.rolSeleccionado = role.id"
                  >
                    <input
                      :id="`role-${role.id}`"
                      v-model="formData.rolSeleccionado"
                      :value="role.id"
                      type="radio"
                      class="w-4 h-4 text-indigo-600 border-gray-300 focus:ring-indigo-500"
                    >
                    <label :for="`role-${role.id}`" class="ml-3 flex-1 cursor-pointer">
                      <span class="block text-sm font-medium text-gray-900">{{ role.nombre }}</span>
                      <span class="block text-xs text-gray-500 mt-1">{{ role.descripcion }}</span>
                      <span class="inline-block mt-1 px-2 py-1 text-xs rounded-full" 
                            :class="getRoleBadgeClass(role.nombre)">
                        {{ getRoleLevel(role.nivel) }}
                      </span>
                    </label>
                  </div>
                </div>
              </div>

              <!-- Estado de verificación (solo edición) -->
              <div v-if="isEditing" class="bg-gray-50 rounded-lg p-3">
                <div class="flex items-center justify-between">
                  <div class="flex items-center">
                    <CheckCircleIcon 
                      v-if="formData.email_verificado" 
                      class="w-5 h-5 text-green-500 mr-2" 
                    />
                    <ExclamationCircleIcon 
                      v-else 
                      class="w-5 h-5 text-yellow-500 mr-2" 
                    />
                    <span class="text-sm font-medium" 
                          :class="formData.email_verificado ? 'text-green-700' : 'text-yellow-700'">
                      {{ formData.email_verificado ? 'Email verificado' : 'Email pendiente de verificación' }}
                    </span>
                  </div>
                  <button
                    v-if="!formData.email_verificado"
                    type="button"
                    @click="reenviarVerificacion"
                    class="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded hover:bg-yellow-200 transition-colors"
                  >
                    Reenviar
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Área reservada para errores -->
        <div class="border-t border-gray-200">
          <!-- Errores de validación -->
          <div 
            v-if="validationErrors.length > 0" 
            class="bg-red-50 border-b border-red-200 p-4"
          >
            <h4 class="text-sm font-medium text-red-800 mb-2">Errores de validación:</h4>
            <ul class="text-sm text-red-700 space-y-1">
              <li v-for="error in validationErrors" :key="error" class="flex items-start">
                <span class="w-1.5 h-1.5 bg-red-500 rounded-full mt-1.5 mr-2 flex-shrink-0"></span>
                <span>{{ error }}</span>
              </li>
            </ul>
          </div>

          <!-- Botones (siempre visibles) -->
          <div class="bg-gray-50 px-6 py-4">
            <div class="flex justify-end space-x-3">
              <button
                type="button"
                @click="closeForm"
                class="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm"
              >
                Cancelar
              </button>
              <button
                type="submit"
                class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm"
              >
                {{ isEditing ? 'Actualizar Usuario' : 'Crear Usuario' }}
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  </div>

  <!-- Modal de carga de foto -->
  <PhotoUploadModal
    v-if="showPhotoUpload"
    :user="formData"
    @photo-updated="onPhotoUpdated"
    @close="showPhotoUpload = false"
  />
</template>

<script setup>
import { ref, watch } from 'vue'
import { CheckCircleIcon, ExclamationCircleIcon, CameraIcon, UserIcon } from '@heroicons/vue/24/outline'
import { mockRoles, mockOrganizaciones } from '../mocks/usuariosMocks'
import PhotoUploadModal from './PhotoUploadModal.vue'

const props = defineProps({
  user: Object,
  isEditing: Boolean,
  availableRoles: {
    type: Array,
    default: () => mockRoles
  }
})

const emit = defineEmits(['save', 'close', 'resend-verification'])

const formData = ref({
  nombre: '',
  apellidos: '',
  nombre_usuario: '',
  email: '',
  contrasena: '',
  confirmar_contrasena: '',
  telefono: '',
  organizacion: '',
  email_verificado: false,
  rolSeleccionado: 'lector',
  avatar: ''
})

const validationErrors = ref([])
const showPhotoUpload = ref(false)
const organizaciones = ref(mockOrganizaciones)

// Cargar datos del usuario si estamos editando
watch(() => props.user, (user) => {
  if (user && props.isEditing) {
    formData.value = {
      nombre: user.nombre || '',
      apellidos: user.apellidos || '',
      nombre_usuario: user.nombre_usuario || '',
      email: user.email || '',
      contrasena: '',
      confirmar_contrasena: '',
      telefono: user.telefono || '',
      organizacion: user.organizacion || '',
      email_verificado: user.email_verificado || false,
      rolSeleccionado: user.roles && user.roles.length > 0 ? user.roles[0].id : 'lector',
      avatar: user.avatar || ''
    }
  }
}, { immediate: true })

const reenviarVerificacion = () => {
  emit('resend-verification', formData.value)
}

const openPhotoUpload = () => {
  showPhotoUpload.value = true
}

const onPhotoUpdated = (userWithPhoto) => {
  formData.value.avatar = userWithPhoto.avatar
  showPhotoUpload.value = false
}

const removePhoto = () => {
  formData.value.avatar = ''
}

const validateForm = () => {
  validationErrors.value = []

  if (!props.isEditing) {
    if (formData.value.contrasena.length < 6) {
      validationErrors.value.push('La contraseña debe tener al menos 6 caracteres')
    }
    
    if (formData.value.contrasena !== formData.value.confirmar_contrasena) {
      validationErrors.value.push('Las contraseñas no coinciden')
    }
  }

  if (!formData.value.nombre.trim()) {
    validationErrors.value.push('El nombre es obligatorio')
  }

  if (!formData.value.apellidos.trim()) {
    validationErrors.value.push('Los apellidos son obligatorios')
  }

  if (!formData.value.nombre_usuario.trim()) {
    validationErrors.value.push('El nombre de usuario es obligatorio')
  }

  if (!formData.value.email.trim()) {
    validationErrors.value.push('El email es obligatorio')
  } else if (!isValidEmail(formData.value.email)) {
    validationErrors.value.push('El formato del email no es válido')
  }

  if (!formData.value.organizacion) {
    validationErrors.value.push('Debe seleccionar una organización')
  }

  if (!formData.value.rolSeleccionado) {
    validationErrors.value.push('Debe seleccionar un rol para el usuario')
  }

  return validationErrors.value.length === 0
}

const isValidEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

const getRoleBadgeClass = (roleName) => {
  const classes = {
    'Administrador': 'bg-red-100 text-red-800',
    'Configurador': 'bg-blue-100 text-blue-800',
    'Grabador': 'bg-green-100 text-green-800',
    'Lector': 'bg-gray-100 text-gray-800'
  }
  return classes[roleName] || 'bg-gray-100 text-gray-800'
}

const getRoleLevel = (nivel) => {
  const levels = {
    1: 'Básico',
    2: 'Intermedio', 
    3: 'Avanzado',
    4: 'Completo'
  }
  return levels[nivel] || 'Básico'
}

const saveUser = () => {
  if (!validateForm()) {
    return
  }

  // Preparar datos para enviar
  const userData = { 
    ...formData.value,
    roles: [props.availableRoles.find(r => r.id === formData.value.rolSeleccionado)]
  }
  
  // No enviar campos de confirmación si estamos editando
  if (props.isEditing) {
    delete userData.contrasena
    delete userData.confirmar_contrasena
  }

  emit('save', userData)
}

const closeForm = () => {
  emit('close')
}
</script>