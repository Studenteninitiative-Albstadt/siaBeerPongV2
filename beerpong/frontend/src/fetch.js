/**
 * Global fetch interceptor — attaches the JWT Bearer token to every request.
 * Imported once in main.js so all components (GroupsView, KnockoutView, etc.)
 * get auth headers without needing individual changes.
 */
const _originalFetch = window.fetch.bind(window)

window.fetch = function authedFetch(input, init = {}) {
  const token = localStorage.getItem('access_token')
  if (token) {
    init.headers = {
      ...init.headers,
      Authorization: `Bearer ${token}`,
    }
  }
  return _originalFetch(input, init)
}
