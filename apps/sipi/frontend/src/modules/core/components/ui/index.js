// Barrel + registro global de los widgets base del sistema de diseño SIPI.
import UiIcon from './UiIcon.vue'
import UiButton from './UiButton.vue'
import UiSpinner from './UiSpinner.vue'
import UiEmptyState from './UiEmptyState.vue'
import UiPanel from './UiPanel.vue'
import PageShell from './PageShell.vue'

export { UiIcon, UiButton, UiSpinner, UiEmptyState, UiPanel, PageShell }

/** Registra los componentes UI globalmente (disponibles en cualquier vista sin import). */
export function registerUi(app) {
  app.component('UiIcon', UiIcon)
  app.component('UiButton', UiButton)
  app.component('UiSpinner', UiSpinner)
  app.component('UiEmptyState', UiEmptyState)
  app.component('UiPanel', UiPanel)
  app.component('PageShell', PageShell)
}
