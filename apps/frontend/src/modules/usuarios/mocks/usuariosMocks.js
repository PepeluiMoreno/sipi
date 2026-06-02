// src/modules/usuarios/mocks/usuariosMocks.js

// Mock de roles del sistema
export const mockRoles = [
  {
    id: 'admin',
    nombre: 'Administrador',
    descripcion: 'Acceso completo al sistema, gestión de usuarios y configuración',
    nivel: 4,
    usuarios_count: 2,
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z'
  },
  {
    id: 'configurador',
    nombre: 'Configurador',
    descripcion: 'Puede modificar configuraciones del sistema pero no gestionar usuarios',
    nivel: 3,
    usuarios_count: 5,
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z'
  },
  {
    id: 'grabador',
    nombre: 'Grabador',
    descripcion: 'Puede crear y editar contenido pero no modificar configuraciones',
    nivel: 2,
    usuarios_count: 12,
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z'
  },
  {
    id: 'lector',
    nombre: 'Lector',
    descripcion: 'Solo puede visualizar contenido, sin permisos de edición',
    nivel: 1,
    usuarios_count: 25,
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z'
  }
]

// Mock de organizaciones
export const mockOrganizaciones = [
  { id: 'particular', nombre: 'Particular' },
  { id: 'apudepa', nombre: 'Apudepa' },
  { id: 'mhel', nombre: 'MHEL' },
  { id: 'europa-laica', nombre: 'Europa Laica' },
  { id: 'laicistas-jerez', nombre: 'Laicistas de Jerez' }
]

// Mock de usuarios de ejemplo
export const mockUsers = [
  {
    id: '1',
    nombre: 'Ana',
    apellidos: 'García López',
    nombre_usuario: 'ana.garcia',
    email: 'ana.garcia@empresa.com',
    email_verificado: true,
    telefono: '+34 600 111 222',
    organizacion: 'apudepa',
    localidad: 'Madrid',
    avatar: '',
    roles: [mockRoles[0]], // Administrador
    created_at: '2024-01-10T09:00:00Z',
    updated_at: '2024-01-10T09:00:00Z'
  },
  {
    id: '2',
    nombre: 'Carlos',
    apellidos: 'Martínez Ruiz',
    nombre_usuario: 'carlos.martinez',
    email: 'carlos.martinez@empresa.com',
    email_verificado: true,
    telefono: '+34 600 333 444',
    organizacion: 'mhel',
    localidad: 'Barcelona',
    avatar: '',
    roles: [mockRoles[1]], // Configurador
    created_at: '2024-01-11T10:00:00Z',
    updated_at: '2024-01-11T10:00:00Z'
  },
  {
    id: '3',
    nombre: 'María',
    apellidos: 'Rodríguez Sánchez',
    nombre_usuario: 'maria.rodriguez',
    email: 'maria.rodriguez@empresa.com',
    email_verificado: false,
    telefono: '+34 600 555 666',
    organizacion: 'europa-laica',
    localidad: 'Valencia',
    avatar: '',
    roles: [mockRoles[2]], // Grabador
    created_at: '2024-01-12T11:00:00Z',
    updated_at: '2024-01-12T11:00:00Z'
  },
  {
    id: '4',
    nombre: 'David',
    apellidos: 'Fernández Gómez',
    nombre_usuario: 'david.fernandez',
    email: 'david.fernandez@empresa.com',
    email_verificado: true,
    telefono: '+34 600 777 888',
    organizacion: 'laicistas-jerez',
    localidad: 'Jerez de la Frontera',
    avatar: '',
    roles: [mockRoles[3]], // Lector
    created_at: '2024-01-13T12:00:00Z',
    updated_at: '2024-01-13T12:00:00Z'
  },
  {
    id: '5',
    nombre: 'Laura',
    apellidos: 'Hernández Castro',
    nombre_usuario: 'laura.hernandez',
    email: 'laura.hernandez@empresa.com',
    email_verificado: true,
    telefono: '+34 600 999 000',
    organizacion: 'particular',
    localidad: 'Sevilla',
    avatar: '',
    roles: [mockRoles[3]], // Lector
    created_at: '2024-01-14T13:00:00Z',
    updated_at: '2024-01-14T13:00:00Z'
  },
  {
    id: '6',
    nombre: 'Pedro',
    apellidos: 'Jiménez Torres',
    nombre_usuario: 'pedro.jimenez',
    email: 'pedro.jimenez@empresa.com',
    email_verificado: false,
    telefono: '+34 600 123 456',
    organizacion: 'particular',
    localidad: 'Málaga',
    avatar: '',
    roles: [mockRoles[2]], // Grabador
    created_at: '2024-01-15T14:00:00Z',
    updated_at: '2024-01-15T14:00:00Z'
  }
]

// Simulador de delay de red
export const simulateNetworkDelay = () => {
  return new Promise(resolve => setTimeout(resolve, 500 + Math.random() * 500))
}

// Generar ID único
export const generateId = () => {
  return Date.now().toString() + Math.random().toString(36).substr(2, 9)
}