import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

export function getStats() {
  return api.get('/stats')
}

export function getPhotoStatus() {
  return api.get('/photos/status')
}

export function ingestPhotos(filePaths, forceReprocess = false) {
  return api.post('/photos/ingest', { file_paths: filePaths, force_reprocess: forceReprocess })
}

export function getPhotos(params = {}) {
  return api.get('/photos', { params })
}

export function getCategories() {
  return api.get('/photos/categories')
}

export function updateTags(imageId, tags) {
  return api.put(`/photos/${imageId}/tags`, { tags })
}

export function deletePhoto(imageId) {
  return api.delete(`/photos/${imageId}`)
}

export function searchByText(data) {
  return api.post('/search/text', data)
}

export function searchByImage(file, page = 1, pageSize = 20) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('data', JSON.stringify({ page, page_size: pageSize }))
  return api.post('/search/image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function getConfigs(group = null) {
  const params = group ? { group } : {}
  return api.get('/configs', { params })
}

export function batchUpdateConfigs(updates) {
  return api.post('/configs/batch', { updates })
}

export function resetConfigs() {
  return api.post('/configs/reset')
}

export function exportConfigs() {
  return api.get('/configs/export', { responseType: 'blob' })
}

export function importConfigs(file) {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/configs/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export default api
