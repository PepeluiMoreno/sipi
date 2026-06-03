<!-- UiIcon: envoltorio sobre Heroicons (outline) con nombres curados.
     Uso: <UiIcon name="search" /> · clase de tamaño por prop o class. -->
<template>
  <component :is="cmp" v-if="cmp" :class="['shrink-0', sizeClass]" aria-hidden="true" />
</template>

<script setup>
import { computed } from 'vue'
import {
  HomeModernIcon, BuildingOffice2Icon, MapPinIcon, MapIcon, MagnifyingGlassIcon,
  PlusIcon, PencilSquareIcon, TrashIcon, XMarkIcon, CheckIcon, CheckCircleIcon,
  ChevronRightIcon, ChevronLeftIcon, ChevronDownIcon, ChevronUpIcon,
  DocumentTextIcon, AdjustmentsHorizontalIcon, ArrowPathIcon, BellIcon,
  Squares2X2Icon, ListBulletIcon, FunnelIcon, ExclamationTriangleIcon,
  InformationCircleIcon, UserGroupIcon, Cog6ToothIcon, EyeIcon, ArrowLeftIcon,
} from '@heroicons/vue/24/outline'

const MAP = {
  inmueble: HomeModernIcon, edificio: BuildingOffice2Icon, 'map-pin': MapPinIcon,
  mapa: MapIcon, search: MagnifyingGlassIcon, plus: PlusIcon, editar: PencilSquareIcon,
  borrar: TrashIcon, cerrar: XMarkIcon, check: CheckIcon, 'check-circle': CheckCircleIcon,
  'chevron-right': ChevronRightIcon, 'chevron-left': ChevronLeftIcon,
  'chevron-down': ChevronDownIcon, 'chevron-up': ChevronUpIcon,
  documento: DocumentTextIcon, ajustes: AdjustmentsHorizontalIcon, refrescar: ArrowPathIcon,
  campana: BellIcon, cards: Squares2X2Icon, lista: ListBulletIcon, filtro: FunnelIcon,
  alerta: ExclamationTriangleIcon, info: InformationCircleIcon, usuarios: UserGroupIcon,
  config: Cog6ToothIcon, ver: EyeIcon, atras: ArrowLeftIcon,
}

const props = defineProps({
  name: { type: String, required: true },
  size: { type: String, default: 'md' }, // sm | md | lg
})
const cmp = computed(() => MAP[props.name] || null)
const sizeClass = computed(() => ({ sm: 'w-4 h-4', md: 'w-5 h-5', lg: 'w-6 h-6' }[props.size] || 'w-5 h-5'))
</script>
