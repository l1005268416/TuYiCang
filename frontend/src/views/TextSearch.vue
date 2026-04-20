<template>
  <div style="padding: 20px; max-width: 1400px; margin: 0 auto;">
    <h2 style="margin-bottom: 20px;">文搜图</h2>

    <el-card style="margin-bottom: 20px;">
      <el-input
        v-model="query"
        placeholder="输入自然语言描述，如：去年夏天在海边拍的日落照片"
        size="large"
        @keyup.enter="handleSearch"
      >
        <template #append>
          <el-button @click="handleSearch" :loading="searching">
            <el-icon><Search /></el-icon> 搜索
          </el-button>
        </template>
      </el-input>
    </el-card>

    <div v-if="searching" style="text-align: center; padding: 40px;">
      <el-icon style="font-size: 32px; color: #409eff; animation: spin 1s linear infinite;"><Loading /></el-icon>
      <p style="color: #999; margin-top: 10px;">正在检索中...</p>
    </div>

    <div v-else-if="results.length === 0 && searched" style="text-align: center; padding: 60px;">
      <el-empty description="未找到匹配的图片，请尝试其他描述" />
    </div>

    <div v-else>
      <el-row :gutter="16">
        <el-col :span="4" v-for="photo in results" :key="photo.image_id">
          <el-card shadow="hover" style="cursor: pointer; margin-bottom: 16px;" @click="showDetail(photo)">
            <el-image
              :src="getThumbUrl(photo)"
              style="width: 100%; height: 120px; border-radius: 4px;"
              fit="cover"
            />
            <div style="margin-top: 8px; font-size: 12px; color: #e6a23c;">
              相似度: {{ (photo.score * 100).toFixed(1) }}%
            </div>
            <div style="margin-top: 4px; font-size: 12px; color: #666; line-height: 1.4;
                        overflow: hidden; text-overflow: ellipsis; display: -webkit-box;
                        -webkit-line-clamp: 2; -webkit-box-orient: vertical;">
              {{ photo.description || '无描述' }}
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <el-dialog v-model="dialogVisible" :title="'图片详情'" width="600px">
      <div v-if="selectedPhoto">
        <el-image
          :src="getOriginalUrl(selectedPhoto)"
          style="width: 100%; max-height: 400px; border-radius: 4px;"
          fit="contain"
        />
        <div style="margin-top: 16px;">
          <p><strong>描述：</strong>{{ selectedPhoto.description }}</p>
          <p><strong>标签：</strong>
            <el-tag v-for="tag in (selectedPhoto.tags || '').split(',')" :key="tag" style="margin-right: 4px;">
              {{ tag }}
            </el-tag>
          </p>
          <p v-if="selectedPhoto.shoot_time"><strong>拍摄时间：</strong>{{ selectedPhoto.shoot_time }}</p>
          <p v-if="selectedPhoto.camera_model"><strong>相机型号：</strong>{{ selectedPhoto.camera_model }}</p>
          <p v-if="selectedPhoto.resolution"><strong>分辨率：</strong>{{ selectedPhoto.resolution }}</p>
          <p><strong>路径：</strong>{{ selectedPhoto.original_path }}</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { searchByText } from '../api/index.js'
import { ElMessage } from 'element-plus'

const query = ref('')
const searching = ref(false)
const searched = ref(false)
const results = ref([])
const dialogVisible = ref(false)
const selectedPhoto = ref(null)

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

<style>
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
