<template>
  <div class="home-container">
    <div class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">
          <span class="gradient-text">智能相册</span> 管理与检索
        </h1>
        <p class="hero-subtitle">
          基于 AI 的本地照片知识库，用自然语言描述或图片相似度搜索你的珍贵回忆
        </p>
        <div class="hero-actions">
          <el-button type="primary" size="large" @click="$router.push('/text-search')" class="hero-btn-primary">
            <el-icon><Search /></el-icon>
            文搜图
          </el-button>
          <el-button size="large" @click="$router.push('/image-search')" class="hero-btn-secondary">
            <el-icon><Picture /></el-icon>
            图搜图
          </el-button>
        </div>
      </div>
      <div class="hero-decoration">
        <div class="floating-card card-1">
          <el-icon><Picture /></el-icon>
        </div>
        <div class="floating-card card-2">
          <el-icon><Search /></el-icon>
        </div>
        <div class="floating-card card-3">
          <el-icon><Star /></el-icon>
        </div>
      </div>
    </div>

    <div class="stats-section">
      <el-row :gutter="20">
        <el-col :span="6" v-for="item in statsCards" :key="item.label">
          <div class="stat-card">
            <div class="stat-icon" :style="{ background: item.gradient }">
              <el-icon><component :is="item.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ item.value }}</div>
              <div class="stat-label">{{ item.label }}</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <div class="features-section">
      <h2 class="section-title">快速开始</h2>
      <el-row :gutter="24">
        <el-col :span="12">
          <div class="feature-card" @click="$router.push('/text-search')">
            <div class="feature-icon text-search">
              <el-icon><Search /></el-icon>
            </div>
            <div class="feature-content">
              <h3>文搜图</h3>
              <p>输入自然语言描述，AI 智能理解并找到匹配的图片</p>
            </div>
            <el-icon class="feature-arrow"><ArrowRight /></el-icon>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="feature-card" @click="$router.push('/image-search')">
            <div class="feature-icon image-search">
              <el-icon><Picture /></el-icon>
            </div>
            <div class="feature-content">
              <h3>图搜图</h3>
              <p>上传参考图片，基于视觉特征找到相似的照片</p>
            </div>
            <el-icon class="feature-arrow"><ArrowRight /></el-icon>
          </div>
        </el-col>
      </el-row>
    </div>

    <div class="recent-section">
      <div class="section-header">
        <h2 class="section-title">最近入库</h2>
        <el-button text @click="$router.push('/album')" class="view-all-btn">
          查看全部 <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
      <el-empty v-if="recentPhotos.length === 0" description="暂无图片，请先入库" />
      <div v-else class="recent-grid">
        <div 
          v-for="photo in recentPhotos" 
          :key="photo.image_id"
          class="recent-item"
          @click="$router.push('/album')"
        >
          <el-image
            :src="photo.thumb_url || getThumbUrl(photo.thumb_path)"
            class="recent-image"
            fit="cover"
            :preview-src-list="[photo.processed_url || getOriginalUrl(photo.original_path)]"
          />
          <div class="recent-overlay">
            <el-icon><ZoomIn /></el-icon>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, shallowRef } from 'vue'
import { getStats, getPhotos } from '../api/index.js'
import { Search, Picture, Star, ArrowRight, ZoomIn, Files, Clock, DataLine, Folder } from '@element-plus/icons-vue'

const statsCards = ref([
  { label: '图片总数', value: 0, icon: shallowRef(Files), gradient: 'linear-gradient(135deg, #6366f1, #818cf8)' },
  { label: '分类数量', value: 0, icon: shallowRef(Folder), gradient: 'linear-gradient(135deg, #8b5cf6, #a78bfa)' },
  { label: '近7天入库', value: 0, icon: shallowRef(Clock), gradient: 'linear-gradient(135deg, #06b6d4, #22d3ee)' },
  { label: '存储占用', value: 'N/A', icon: shallowRef(DataLine), gradient: 'linear-gradient(135deg, #f59e0b, #fbbf24)' }
])
const recentPhotos = ref([])

onMounted(async () => {
  try {
    const res = await getStats()
    if (res.data.success) {
      statsCards.value[0].value = res.data.data.total_photos
      statsCards.value[1].value = res.data.data.category_count
      statsCards.value[2].value = res.data.data.recent_count
    }
  } catch (e) {
    console.error('Failed to load stats:', e)
  }

  try {
    const res = await getPhotos({ page_size: 5 })
    if (res.data.success) {
      recentPhotos.value = res.data.data.results
    }
  } catch (e) {
    console.error('Failed to load recent photos:', e)
  }
})

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
.home-container {
  max-width: 1200px;
  margin: 0 auto;
}

.hero-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 48px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%);
  border-radius: 24px;
  border: 1px solid rgba(99, 102, 241, 0.2);
  margin-bottom: 32px;
  position: relative;
  overflow: hidden;
}

.hero-content {
  flex: 1;
  z-index: 1;
}

.hero-title {
  font-size: 36px;
  font-weight: 700;
  color: #f8fafc;
  margin: 0 0 16px 0;
  line-height: 1.3;
}

.gradient-text {
  background: linear-gradient(135deg, #818cf8, #c084fc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 16px;
  color: #94a3b8;
  margin: 0 0 32px 0;
  max-width: 480px;
  line-height: 1.6;
}

.hero-actions {
  display: flex;
  gap: 16px;
}

.hero-btn-primary {
  background: linear-gradient(135deg, #6366f1, #818cf8) !important;
  border: none !important;
  padding: 12px 28px !important;
  font-weight: 500;
}

.hero-btn-primary:hover {
  background: linear-gradient(135deg, #4f46e5, #6366f1) !important;
  transform: translateY(-2px);
}

.hero-btn-secondary {
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  color: #f8fafc !important;
  padding: 12px 28px !important;
}

.hero-btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1) !important;
  border-color: rgba(255, 255, 255, 0.2) !important;
}

.hero-decoration {
  position: absolute;
  right: 48px;
  top: 50%;
  transform: translateY(-50%);
}

.floating-card {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: absolute;
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.floating-card .el-icon {
  font-size: 24px;
  color: #f8fafc;
}

.card-1 {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.6), rgba(139, 92, 246, 0.4));
  top: -60px;
  right: 20px;
  animation: float 6s ease-in-out infinite;
}

.card-2 {
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.6), rgba(34, 211, 238, 0.4));
  top: 0;
  right: -30px;
  animation: float 6s ease-in-out infinite 1s;
}

.card-3 {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.6), rgba(251, 191, 36, 0.4));
  top: 60px;
  right: 40px;
  animation: float 6s ease-in-out infinite 2s;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-20px); }
}

.stats-section {
  margin-bottom: 40px;
}

.stat-card {
  background: rgba(30, 41, 59, 0.6);
  border-radius: 16px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: 1px solid rgba(99, 102, 241, 0.15);
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
  border-color: rgba(99, 102, 241, 0.3);
  box-shadow: 0 8px 32px rgba(99, 102, 241, 0.15);
}

.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon .el-icon {
  font-size: 24px;
  color: white;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #f8fafc;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
  margin-top: 4px;
}

.features-section {
  margin-bottom: 40px;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: #f8fafc;
  margin: 0 0 20px 0;
}

.feature-card {
  background: rgba(30, 41, 59, 0.6);
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  border: 1px solid rgba(99, 102, 241, 0.15);
  cursor: pointer;
  transition: all 0.3s;
}

.feature-card:hover {
  transform: translateY(-4px);
  border-color: rgba(99, 102, 241, 0.4);
  box-shadow: 0 8px 32px rgba(99, 102, 241, 0.2);
}

.feature-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.feature-icon .el-icon {
  font-size: 28px;
  color: white;
}

.feature-icon.text-search {
  background: linear-gradient(135deg, #6366f1, #818cf8);
}

.feature-icon.image-search {
  background: linear-gradient(135deg, #10b981, #34d399);
}

.feature-content {
  flex: 1;
}

.feature-content h3 {
  font-size: 18px;
  font-weight: 600;
  color: #f8fafc;
  margin: 0 0 8px 0;
}

.feature-content p {
  font-size: 14px;
  color: #64748b;
  margin: 0;
  line-height: 1.5;
}

.feature-arrow {
  font-size: 20px;
  color: #64748b;
  transition: all 0.3s;
}

.feature-card:hover .feature-arrow {
  color: #818cf8;
  transform: translateX(4px);
}

.recent-section {
  background: rgba(30, 41, 59, 0.4);
  border-radius: 20px;
  padding: 24px;
  border: 1px solid rgba(99, 102, 241, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.view-all-btn {
  color: #818cf8 !important;
  display: flex;
  align-items: center;
  gap: 4px;
}

.recent-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}

.recent-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s;
}

.recent-item:hover {
  transform: scale(1.05);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.recent-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.recent-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
}

.recent-item:hover .recent-overlay {
  opacity: 1;
}

.recent-overlay .el-icon {
  font-size: 24px;
  color: white;
}

@media (max-width: 768px) {
  .hero-section {
    padding: 32px 20px;
  }

  .hero-title {
    font-size: 24px;
  }

  .hero-decoration {
    display: none;
  }

  .hero-actions {
    flex-direction: column;
  }

  .recent-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
