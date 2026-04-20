<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">
        <el-icon class="title-icon"><Search /></el-icon>
        文搜图
      </h2>
      <p class="page-desc">用自然语言描述你想找的照片</p>
    </div>

    <div class="search-card">
      <el-input
        v-model="query"
        placeholder="输入自然语言描述，如：去年夏天在海边拍的日落照片"
        size="large"
        class="search-input"
        @keyup.enter="handleSearch"
      >
        <template #append>
          <el-button @click="handleSearch" :loading="searching" class="search-btn">
            <el-icon><Search /></el-icon>
          </el-button>
        </template>
      </el-input>
      <div class="search-tips">
        <span>试试：</span>
        <el-tag v-for="tip in searchTips" :key="tip" @click="query = tip" class="tip-tag">
          {{ tip }}
        </el-tag>
      </div>
    </div>

    <div v-if="searching" class="loading-state">
      <div class="loading-spinner"></div>
      <p>正在智能检索中...</p>
    </div>

    <div v-else-if="results.length === 0 && searched" class="empty-state">
      <el-empty description="未找到匹配的图片，请尝试其他描述" />
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
          <div class="result-info">
            <p class="result-desc">{{ photo.description || '无描述' }}</p>
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
          <div class="meta-item" v-if="selectedPhoto.camera_model">
            <span class="meta-label">相机型号</span>
            <span class="meta-value">{{ selectedPhoto.camera_model }}</span>
          </div>
          <div class="meta-item" v-if="selectedPhoto.resolution">
            <span class="meta-label">分辨率</span>
            <span class="meta-value">{{ selectedPhoto.resolution }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">路径</span>
            <span class="meta-value path">{{ selectedPhoto.original_path }}</span>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { searchByText } from '../api/index.js'
import { ElMessage } from 'element-plus'
import { Search, Loading } from '@element-plus/icons-vue'

const query = ref('')
const searching = ref(false)
const searched = ref(false)
const results = ref([])
const dialogVisible = ref(false)
const selectedPhoto = ref(null)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const searchTips = [
  '海边日落',
  '户外露营',
  '美食照片',
  '宠物猫狗',
  '城市夜景'
]

async function handleSearch() {
  if (!query.value.trim()) return
  currentPage.value = 1
  searching.value = true
  searched.value = true
  try {
    const res = await searchByText({
      query: query.value.trim(),
      page: currentPage.value,
      page_size: pageSize.value
    })
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
    const res = await searchByText({
      query: query.value.trim(),
      page: currentPage.value,
      page_size: pageSize.value
    })
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
  return photo.processed_url || photo.original_path || ''
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
  color: #818cf8;
}

.page-desc {
  color: #64748b;
  margin: 0;
}

.search-card {
  background: rgba(30, 41, 59, 0.6);
  border-radius: 16px;
  padding: 24px;
  border: 1px solid rgba(99, 102, 241, 0.15);
  margin-bottom: 32px;
}

.search-input :deep(.el-input__wrapper) {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(99, 102, 241, 0.2);
  box-shadow: none;
  border-radius: 12px;
  padding: 4px 16px;
}

.search-input :deep(.el-input__inner) {
  color: #f8fafc;
}

.search-input :deep(.el-input__inner::placeholder) {
  color: #64748b;
}

.search-input :deep(.el-input-group__append) {
  background: linear-gradient(135deg, #6366f1, #818cf8);
  border: none;
  border-radius: 0 12px 12px 0;
  padding: 0;
  min-width: 80px;
}

.search-btn {
  background: transparent !important;
  border: none !important;
  color: white !important;
  padding: 8px 20px;
  min-width: 80px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.search-tips {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.search-tips > span {
  color: #64748b;
  font-size: 13px;
}

.tip-tag {
  cursor: pointer;
  background: rgba(99, 102, 241, 0.15) !important;
  border-color: rgba(99, 102, 241, 0.3) !important;
  color: #818cf8 !important;
}

.tip-tag:hover {
  background: rgba(99, 102, 241, 0.25) !important;
}

.loading-state {
  text-align: center;
  padding: 80px 20px;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 3px solid rgba(99, 102, 241, 0.2);
  border-top-color: #818cf8;
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
  color: #818cf8;
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
}

.result-card:hover {
  transform: translateY(-4px);
  border-color: rgba(99, 102, 241, 0.4);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.2);
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

.result-card {
  position: relative;
}

.result-info {
  padding: 12px;
}

.result-desc {
  color: #94a3b8;
  font-size: 12px;
  margin: 0;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
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

.meta-value.path {
  font-size: 12px;
  word-break: break-all;
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
  --el-pagination-hover-color: #818cf8;
  --el-pagination-button-disabled-color: #475569;
  --el-pagination-button-bg-color: transparent;
  --el-pagination-button-disabled-bg-color: transparent;
}

.pagination-wrapper :deep(.el-pager li) {
  background: transparent;
  color: #94a3b8;
}

.pagination-wrapper :deep(.el-pager li.is-active) {
  color: #818cf8;
}

.pagination-wrapper :deep(.el-pager li:hover) {
  color: #818cf8;
}
</style>
