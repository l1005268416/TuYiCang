<template>
  <div style="padding: 20px; max-width: 1200px; margin: 0 auto;">
    <h1 style="margin-bottom: 20px;">欢迎使用图忆仓</h1>

    <el-row :gutter="20" style="margin-bottom: 30px;">
      <el-col :span="6" v-for="item in statsCards" :key="item.label">
        <el-card shadow="hover" style="text-align: center;">
          <div style="font-size: 32px; font-weight: bold; color: #409eff;">{{ item.value }}</div>
          <div style="color: #999; margin-top: 8px;">{{ item.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-bottom: 30px;">
      <el-col :span="12">
        <el-card shadow="hover" style="text-align: center; cursor: pointer;" @click="$router.push('/text-search')">
          <el-icon style="font-size: 48px; color: #409eff; margin-bottom: 16px;"><Search /></el-icon>
          <h3>文搜图</h3>
          <p style="color: #999;">输入自然语言描述，找到匹配的图片</p>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover" style="text-align: center; cursor: pointer;" @click="$router.push('/image-search')">
          <el-icon style="font-size: 48px; color: #67c23a; margin-bottom: 16px;"><Picture /></el-icon>
          <h3>图搜图</h3>
          <p style="color: #999;">上传参考图片，找到视觉相似的图片</p>
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-weight: bold;">最近入库</span>
          <el-button text @click="$router.push('/album')">查看全部</el-button>
        </div>
      </template>
      <el-empty v-if="recentPhotos.length === 0" description="暂无图片，请先入库" />
      <div v-else style="display: flex; gap: 10px; flex-wrap: wrap;">
        <div v-for="photo in recentPhotos" :key="photo.image_id"
             style="width: 80px; cursor: pointer;"
             @click="$router.push('/album')">
          <el-image
            :src="getThumbUrl(photo.thumb_path)"
            style="width: 80px; height: 80px; border-radius: 4px;"
            fit="cover"
            :preview-src-list="[getOriginalUrl(photo.original_path)]"
          />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getStats, getPhotos } from '../api/index.js'

const statsCards = ref([
  { label: '图片总数', value: 0 },
  { label: '分类数量', value: 0 },
  { label: '近7天入库', value: 0 },
  { label: '存储占用', value: 'N/A' }
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
