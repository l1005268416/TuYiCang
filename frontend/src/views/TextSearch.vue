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
        <span>找到 <strong>{{ results.length }}</strong> 张相似图片</span>
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
    </div>

    <el-dialog v-model="dialogVisible" title="图片详情" width="700px" class="detail-dialog">
      <div v-if="selectedPhoto">
        <el-image
          :src="getOriginalUrl(selectedPhoto)"
          style="width: 100%; max-height: 450px; border-radius: 12px;"
          fit="contain"
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

const searchTips = [
  '海边日落',
  '户外露营',
  '美食照片',
  '宠物猫狗',
  '城市夜景'
]

async function handleSearch() {
  if (!query.value.trim()) return
  searching.value = true
  searched.value = true
  try {
    const res = await searchByText({ query: query.value.trim() })
    if (res.data.success) {
      results.value = res.data.data.results
    } else {
      ElMessage.error(res.data.message || '搜索失败')
    }
  } catch (e) {
    ElMessage.error('搜索请求失败')
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
}

.search-btn {
  background: transparent !important;
  border: none !important;
  color: white !important;
  padding: 8px 20px;
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
  color: #f8fafc;
  font-size: 14px;
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
</style>
