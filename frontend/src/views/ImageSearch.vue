<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">
        <el-icon class="title-icon"><Picture /></el-icon>
        图搜图
      </h2>
      <p class="page-desc">上传参考图片，找到视觉相似的照片</p>
    </div>

    <div class="upload-section">
      <el-upload
        ref="uploadRef"
        drag
        action=""
        :auto-upload="false"
        :on-change="handleUpload"
        :limit="1"
        accept="image/*"
        class="upload-zone"
      >
        <div class="upload-content">
          <el-icon class="upload-icon"><Upload /></el-icon>
          <p class="upload-text">拖拽参考图片到此处</p>
          <p class="upload-hint">或 <span>点击选择文件</span></p>
        </div>
      </el-upload>

      <div v-if="previewUrl" class="preview-section">
        <el-image
          :src="previewUrl"
          class="preview-image"
          fit="contain"
          :preview-src-list="[previewUrl]"
        />
        <div class="preview-actions">
          <el-button type="primary" @click="handleSearch" :loading="searching" class="action-btn">
            <el-icon><Search /></el-icon>
            开始检索
          </el-button>
          <el-button @click="resetUpload" class="action-btn secondary">
            <el-icon><RefreshRight /></el-icon>
            重新上传
          </el-button>
        </div>
      </div>
    </div>

    <div v-if="searching" class="loading-state">
      <div class="loading-spinner"></div>
      <p>正在以图搜图中...</p>
    </div>

    <div v-else-if="results.length === 0 && searched" class="empty-state">
      <el-empty description="未找到相似的图片，请尝试其他参考图片" />
    </div>

    <div v-else-if="results.length > 0">
      <div class="results-header">
        <span>找到 <strong>{{ total }}</strong> 张相似图片</span>
      </div>
      <div class="results-grid">
        <div 
          v-for="photo in results" 
          :key="photo.image_id" 
          class="result-card"
          @click="showDetail(photo)"
        >
          <el-image
            :src="getThumbUrl(photo)"
            class="result-image"
            fit="cover"
          />
          <div class="result-overlay">
            <div class="score-badge">{{ (photo.score * 100).toFixed(0) }}%</div>
          </div>
        </div>
      </div>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <el-dialog v-model="dialogVisible" title="图片详情" width="700px" class="detail-dialog">
      <div v-if="selectedPhoto">
        <el-image
          :src="getOriginalUrl(selectedPhoto)"
          style="width: 100%; max-height: 70vh; border-radius: 12px;"
          fit="contain"
          :preview-src-list="[getOriginalUrl(selectedPhoto)]"
        />
        <div class="detail-meta">
          <div class="meta-item">
            <span class="meta-label">描述</span>
            <span class="meta-value">{{ selectedPhoto.description || '-' }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">标签</span>
            <div class="meta-tags">
              <el-tag v-for="tag in (selectedPhoto.tags || '').split(',')" :key="tag" size="small">
                {{ tag }}
              </el-tag>
            </div>
          </div>
          <div class="meta-item" v-if="selectedPhoto.shoot_time">
            <span class="meta-label">拍摄时间</span>
            <span class="meta-value">{{ selectedPhoto.shoot_time }}</span>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { searchByImage } from '../api/index.js'
import { ElMessage } from 'element-plus'
import { Upload, Search, RefreshRight, Picture, Loading } from '@element-plus/icons-vue'

const uploadRef = ref(null)
const previewUrl = ref('')
const selectedFile = ref(null)
const searching = ref(false)
const searched = ref(false)
const results = ref([])
const dialogVisible = ref(false)
const selectedPhoto = ref(null)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

function handleUpload(file) {
  selectedFile.value = file.raw
  previewUrl.value = URL.createObjectURL(file.raw)
  searched.value = false
  results.value = []
}

async function handleSearch() {
  if (!selectedFile.value) return
  currentPage.value = 1
  searching.value = true
  searched.value = true
  try {
    const res = await searchByImage(selectedFile.value, currentPage.value, pageSize.value)
    if (res.data.success) {
      results.value = res.data.data.results
      total.value = res.data.data.total
    } else {
      ElMessage.error(res.data.message || '搜索失败')
    }
  } catch (e) {
    ElMessage.error('搜索请求失败')
  } finally {
    searching.value = false
  }
}

async function handlePageChange(page) {
  currentPage.value = page
  searching.value = true
  try {
    const res = await searchByImage(selectedFile.value, currentPage.value, pageSize.value)
    if (res.data.success) {
      results.value = res.data.data.results
      total.value = res.data.data.total
    }
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    searching.value = false
  }
}

function resetUpload() {
  uploadRef.value?.clearFiles()
  previewUrl.value = ''
  selectedFile.value = null
  searched.value = false
  results.value = []
  currentPage.value = 1
  total.value = 0
}

function showDetail(photo) {
  selectedPhoto.value = photo
  dialogVisible.value = true
}

function getThumbUrl(photo) {
  if (!photo) return ''
  return photo.thumb_url || photo.thumb_path || ''
}

function getOriginalUrl(photo) {
  if (!photo) return ''
  return photo.original_url || photo.processed_url || ''
}
</script>

<style scoped>
.page-container {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 32px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #f8fafc;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  color: #34d399;
}

.page-desc {
  color: #64748b;
  margin: 0;
}

.upload-section {
  background: rgba(30, 41, 59, 0.6);
  border-radius: 16px;
  padding: 32px;
  border: 1px solid rgba(99, 102, 241, 0.15);
  margin-bottom: 32px;
}

.upload-zone :deep(.el-upload-dragger) {
  background: rgba(15, 23, 42, 0.6);
  border: 2px dashed rgba(99, 102, 241, 0.3);
  border-radius: 16px;
  padding: 48px;
  transition: all 0.3s;
}

.upload-zone :deep(.el-upload-dragger:hover) {
  border-color: #818cf8;
  background: rgba(99, 102, 241, 0.1);
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.upload-icon {
  font-size: 56px;
  color: #818cf8;
  margin-bottom: 16px;
}

.upload-text {
  color: #f8fafc;
  font-size: 16px;
  margin: 0 0 8px 0;
}

.upload-hint {
  color: #64748b;
  font-size: 14px;
  margin: 0;
}

.upload-hint span {
  color: #818cf8;
}

.preview-section {
  margin-top: 32px;
  text-align: center;
}

.preview-image {
  max-width: 320px;
  max-height: 240px;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.preview-actions {
  margin-top: 24px;
  display: flex;
  justify-content: center;
  gap: 16px;
}

.action-btn {
  padding: 12px 24px;
  border-radius: 10px;
}

.action-btn.primary {
  background: linear-gradient(135deg, #10b981, #34d399) !important;
  border: none !important;
}

.action-btn.secondary {
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  color: #f8fafc !important;
}

.loading-state {
  text-align: center;
  padding: 80px 20px;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 3px solid rgba(16, 185, 129, 0.2);
  border-top-color: #34d399;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-state p {
  color: #64748b;
}

.empty-state {
  padding: 60px 20px;
}

.results-header {
  color: #94a3b8;
  margin-bottom: 20px;
}

.results-header strong {
  color: #34d399;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}

.result-card {
  background: rgba(30, 41, 59, 0.6);
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(99, 102, 241, 0.15);
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.result-card:hover {
  transform: translateY(-4px);
  border-color: rgba(16, 185, 129, 0.4);
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.2);
}

.result-image {
  width: 100%;
  height: 140px;
  object-fit: cover;
}

.result-overlay {
  position: absolute;
  top: 8px;
  right: 8px;
}

.score-badge {
  background: rgba(16, 185, 129, 0.9);
  color: white;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.detail-meta {
  margin-top: 20px;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.meta-label {
  color: #64748b;
  font-size: 12px;
}

.meta-value {
  color: #f8fafc !important;
  font-size: 14px;
}

:deep(.el-dialog) {
  background: #1e293b !important;
}

:deep(.el-dialog__header) {
  background: #1e293b !important;
  border-bottom: 1px solid rgba(99, 102, 241, 0.2);
}

:deep(.el-dialog__title) {
  color: #f8fafc !important;
}

:deep(.el-dialog__body) {
  background: #1e293b !important;
  color: #f8fafc !important;
  padding: 20px 24px;
}

:deep(.el-dialog__headerbtn .el-dialog__close) {
  color: #94a3b8 !important;
}

.meta-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

@media (max-width: 1024px) {
  .results-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 768px) {
  .results-grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .detail-meta {
    grid-template-columns: 1fr;
  }
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 32px;
  padding-bottom: 32px;
}

.pagination-wrapper :deep(.el-pagination) {
  --el-pagination-bg-color: rgba(30, 41, 59, 0.6);
  --el-pagination-text-color: #94a3b8;
  --el-pagination-button-color: #94a3b8;
  --el-pagination-hover-color: #34d399;
  --el-pagination-button-disabled-color: #475569;
  --el-pagination-button-bg-color: transparent;
  --el-pagination-button-disabled-bg-color: transparent;
}

.pagination-wrapper :deep(.el-pager li) {
  background: transparent;
  color: #94a3b8;
}

.pagination-wrapper :deep(.el-pager li.is-active) {
  color: #34d399;
}

.pagination-wrapper :deep(.el-pager li:hover) {
  color: #34d399;
}
</style>
