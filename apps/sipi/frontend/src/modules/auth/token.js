// Almacenamiento del token de acceso, con soporte de "Recuérdame":
//  - remember = true  → localStorage (persiste tras cerrar el navegador)
//  - remember = false → sessionStorage (se borra al cerrar la pestaña/navegador)
const KEY = 'auth_token'
const REMEMBER = 'auth_remember'

export function getToken() {
  return localStorage.getItem(KEY) || sessionStorage.getItem(KEY) || null
}

export function setToken(token, remember = true) {
  if (!token) { clearToken(); return }
  if (remember) {
    localStorage.setItem(KEY, token)
    localStorage.setItem(REMEMBER, '1')
    sessionStorage.removeItem(KEY)
  } else {
    sessionStorage.setItem(KEY, token)
    localStorage.removeItem(KEY)
    localStorage.removeItem(REMEMBER)
  }
}

export function clearToken() {
  localStorage.removeItem(KEY)
  localStorage.removeItem(REMEMBER)
  sessionStorage.removeItem(KEY)
}

export function isRemembered() {
  return localStorage.getItem(REMEMBER) === '1'
}
