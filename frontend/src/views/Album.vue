<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">
        <el-icon class="title-icon"><FolderOpened /></el-icon>
        相册管理
      </h2>
      <p class="page-desc">浏览和管理你的照片库</p>
    </div>

    <div class="album-layout">
      <aside class="sidebar">
        <div class="sidebar-card">
          <h3 class="sidebar-title">文件夹分类</h3>
          <el-tree
            :data="categories"
            :props="{ label: 'name', children: 'children' }"
            class="category-tree"
            @node-click="handleCategoryClick"
          />
        </div>
      </aside>

      <main class="main-content">
        <div class="filter-card">
          <el-row :gutter="16" align="middle">
            <el-col :span="6">
              <el-input 
                v-model="searchTag" 
                placeholder="搜索标签" 
                clearable 
                class="filter-input"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </el-col>
            <el-col :span="10">
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                class="filter-date"
              />
            </el-col>
            <el-col :span="4">
              <el-button type="primary" @click="loadPhotos" class="filter-btn">
                <el-icon><Search /></el-icon>
                查询
              </el-button>
            </el-col>
            <el-col :span="4" style="text-align: right;">
              <span class="total-count">共 <strong>{{ total }}</strong> 张图片</span>
            </el-col>
          </el-row>
        </div>

        <div class="photos-grid">
          <div 
            v-for="photo in photos" 
            :key="photo.image_id" 
            class="photo-card"
            @click="showDetail(photo)"
          >
            <el-image
              :src="photo.thumb_url || getThumbUrl(photo.thumb_path)"
              class="photo-image"
              fit="cover"
            />
            <div class="photo-overlay">
              <el-icon><ZoomIn /></el-icon>
            </div>
            <div class="photo-info">
              <span class="photo-folder">{{ photo.folder_tag || '根目录' }}</span>
              <span class="photo-date">{{ formatDate(photo.shoot_time || photo.create_time) }}</span>
            </div>
          </div>
        </div>

        <div class="pagination-wrapper" v-if="total > pageSize">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="total"
            layout="prev, pager, next"
            background
            @current-change="handlePageChange"
          />
        </div>
      </main>
    </div>

    <el-dialog v-model="dialogVisible" title="图片详情" width="750px" class="detail-dialog" destroy-on-close>
      <div v-if="selectedPhoto">
        <div class="detail-image-wrapper">
          <el-image
            :src="getOriginalUrl(selectedPhoto.original_url)||selectedPhoto.processed_url "
            style="width: 100%; max-height: 70vh; border-radius: 12px;"
            fit="contain"
            :preview-src-list="[getOriginalUrl(selectedPhoto.original_url)||selectedPhoto.processed_url ]"
          />
        </div>
        <div class="detail-meta">
          <div class="meta-row">
            <div class="meta-item">
              <span class="meta-label">描述</span>
              <span class="meta-value">{{ selectedPhoto.description || '-' }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">标签</span>
              <div class="meta-tags">
                <el-tag v-for="tag in (selectedPhoto.tags || '').split(',')" :key="tag" size="small" v-if="selectedPhoto.tags">
                  {{ tag }}
                </el-tag>
                <el-button text size="small" @click="editTags" class="edit-tag-btn">编辑</el-button>
              </div>
            </div>
          </div>
          <div class="meta-row">
            <div class="meta-item" v-if="selectedPhoto.shoot_time">
              <span class="meta-label">拍摄时间</span>
              <span class="meta-value">{{ selectedPhoto.shoot_time }}</span>
            </div>
            <div class="meta-item" v-if="selectedPhoto.camera_model">
              <span class="meta-label">相机型号</span>
              <span class="meta-value">{{ selectedPhoto.camera_model }}</span>
            </div>
          </div>
          <div class="meta-row">
            <div class="meta-item" v-if="selectedPhoto.gps">
              <span class="meta-label">GPS位置</span>
              <span class="meta-value">{{ selectedPhoto.gps }}</span>
            </div>
            <div class="meta-item" v-if="selectedPhoto.resolution">
              <span class="meta-label">分辨率</span>
              <span class="meta-value">{{ selectedPhoto.resolution }}</span>
            </div>
          </div>
          <div class="meta-item full-width">
            <span class="meta-label">路径</span>
            <span class="meta-value path">{{ selectedPhoto.original_path }}</span>
          </div>
          <div class="meta-item full-width">
            <span class="meta-label">入库时间</span>
            <span class="meta-value">{{ selectedPhoto.create_time }}</span>
          </div>
        </div>
        <div class="detail-actions">
          <el-button type="danger" @click="handleDelete(selectedPhoto.image_id)">
            <el-icon><Delete /></el-icon>
            删除图片
          </el-button>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="tagDialogVisible" title="编辑标签" width="400px" class="tag-dialog">
      <el-input v-model="tagInput" placeholder="用逗号分隔多个标签" />
      <template #footer>
        <el-button @click="tagDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveTags">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getPhotos, getCategories, updateTags, deletePhoto } from '../api/index.js'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, ZoomIn, FolderOpened, Delete } from '@element-plus/icons-vue'

const categories = ref([])
const photos = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchTag = ref('')
const folderTag = ref('')
const dateRange = ref([])
const dialogVisible = ref(false)
const tagDialogVisible = ref(false)
const selectedPhoto = ref(null)
const tagInput = ref('')
const editingImageId = ref('')

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return dateStr.substring(0, 10)
}

onMounted(() => {
  loadCategories()
  loadPhotos()
})

async function loadCategories() {
  try {
    const res = await getCategories()
    if (res.data.success) {
      categories.value = res.data.data.categories
    }
  } catch (e) {
    console.error('Failed to load categories:', e)
  }
}

async function loadPhotos() {
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (searchTag.value) params.tag = searchTag.value
    if (folderTag.value) params.folder_tag = folderTag.value
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_time = dateRange.value[0].toISOString()
      params.end_time = dateRange.value[1].toISOString()
    }

    const res = await getPhotos(params)
    if (res.data.success) {
      photos.value = res.data.data.results
      total.value = res.data.data.total
    }
  } catch (e) {
    ElMessage.error('加载图片失败')
  }
}

function handlePageChange(page) {
  currentPage.value = page
  loadPhotos()
}

function handleCategoryClick(node) {
  folderTag.value = node.path || node.name
  currentPage.value = 1
  loadPhotos()
}

function showDetail(photo) {
  selectedPhoto.value = photo
  dialogVisible.value = true
}

function editTags() {
  editingImageId.value = selectedPhoto.value.image_id
  tagInput.value = selectedPhoto.value.tags || ''
  tagDialogVisible.value = true
}

async function saveTags() {
  try {
    const res = await updateTags(editingImageId.value, tagInput.value)
    if (res.data.success) {
      ElMessage.success('标签更新成功')
      tagDialogVisible.value = false
      if (selectedPhoto.value) {
        selectedPhoto.value.tags = tagInput.value
      }
    }
  } catch (e) {
    ElMessage.error('标签更新失败')
  }
}

async function handleDelete(imageId) {
  try {
    await ElMessageBox.confirm('确定删除该图片及其关联数据吗？', '确认删除', {
      type: 'warning'
    })
    const res = await deletePhoto(imageId)
    if (res.data.success) {
      ElMessage.success('删除成功')
      dialogVisible.value = false
      loadPhotos()
    }
  } catch {
    // cancelled or failed
  }
}

function getThumbUrl(path) {
  if (!path) return ''
  return path
}

function getOriginalUrl(path) {
  if (!path) return ''
  return path
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
  color: #fbbf24;
}

.page-desc {
  color: #64748b;
  margin: 0;
}

.album-layout {
  display: flex;
  gap: 24px;
}

.sidebar {
  width: 260px;
  flex-shrink: 0;
}

.sidebar-card {
  background: rgba(30, 41, 59, 0.6);
  border-radius: 16px;
  padding: 20px;
  border: 1px solid rgba(99, 102, 241, 0.15);
  position: sticky;
  top: 88px;
}

.sidebar-title {
  font-size: 14px;
  font-weight: 600;
  color: #94a3b8;
  margin: 0 0 16px 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.category-tree {
  background: transparent !important;
}

.category-tree :deep(.el-tree-node__content) {
  background: transparent !important;
  color: #94a3b8;
  border-radius: 8px;
  height: 36px;
}

.category-tree :deep(.el-tree-node__content:hover) {
  background: rgba(99, 102, 241, 0.15) !important;
  color: #f8fafc;
}

.category-tree :deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: rgba(99, 102, 241, 0.2) !important;
  color: #818cf8;
}

.main-content {
  flex: 1;
  min-width: 0;
}

.filter-card {
  background: rgba(30, 41, 59, 0.6);
  border-radius: 16px;
  padding: 20px;
  border: 1px solid rgba(99, 102, 241, 0.15);
  margin-bottom: 24px;
}

.filter-input :deep(.el-input__wrapper) {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(99, 102, 241, 0.2);
  box-shadow: none;
  border-radius: 10px;
}

.filter-input :deep(.el-input__inner) {
  color: #f8fafc;
}

.filter-date {
  width: 100% !important;
}

.filter-date :deep(.el-input__wrapper) {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(99, 102, 241, 0.2);
  box-shadow: none;
}

.filter-btn {
  background: linear-gradient(135deg, #6366f1, #818cf8) !important;
  border: none !important;
  border-radius: 10px;
}

.total-count {
  color: #64748b;
  font-size: 13px;
}

.total-count strong {
  color: #818cf8;
}

.photos-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}

.photo-card {
  background: rgba(30, 41, 59, 0.6);
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(99, 102, 241, 0.15);
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.photo-card:hover {
  transform: translateY(-4px);
  border-color: rgba(99, 102, 241, 0.4);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.2);
}

.photo-image {
  width: 100%;
  height: 160px;
  object-fit: cover;
}

.photo-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
}

.photo-card:hover .photo-overlay {
  opacity: 1;
}

.photo-overlay .el-icon {
  font-size: 28px;
  color: white;
}

.photo-info {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.photo-folder {
  color: #94a3b8;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.photo-date {
  color: #64748b;
  font-size: 11px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 32px;
}

.pagination-wrapper :deep(.el-pagination) {
  --el-pagination-bg-color: rgba(30, 41, 59, 0.6);
  --el-pagination-text-color: #94a3b8;
  --el-pagination-button-bg-color: rgba(30, 41, 59, 0.8);
}

.pagination-wrapper :deep(.el-pager li) {
  background: rgba(30, 41, 59, 0.8);
  color: #94a3b8;
  border-radius: 8px;
  margin: 0 4px;
}

.pagination-wrapper :deep(.el-pager li.is-active) {
  background: #6366f1;
  color: white;
}

.detail-meta {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.meta-row {
  display: flex;
  gap: 24px;
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

:deep(.el-dialog__body .meta-label) {
  color: #94a3b8 !important;
}

:deep(.el-dialog__body .meta-value) {
  color: #f8fafc !important;
}

.meta-item {
  flex: 1;
}

.meta-item.full-width {
  width: 100%;
}

.meta-label {
  color: #94a3b8 !important;
  font-size: 12px;
  display: block;
  margin-bottom: 4px;
}

.meta-value {
  color: #f8fafc !important;
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
  align-items: center;
}

.edit-tag-btn {
  color: #818cf8 !important;
}

.detail-image-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
  max-height: 70vh;
  overflow: auto;
}

.detail-image-wrapper :deep(.el-image__wrapper) {
  max-height: 100%;
  object-fit: contain;
}

.detail-actions {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid rgba(99, 102, 241, 0.15);
  text-align: right;
}

@media (max-width: 1200px) {
  .photos-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 1024px) {
  .album-layout {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
  }

  .sidebar-card {
    position: static;
  }

  .photos-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 768px) {
  .photos-grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .meta-row {
    flex-direction: column;
    gap: 12px;
  }
}
</style>
