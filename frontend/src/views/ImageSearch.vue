<template>
  <div style="padding: 20px; max-width: 1400px; margin: 0 auto;">
    <h2 style="margin-bottom: 20px;">图搜图</h2>

    <el-card style="margin-bottom: 20px;">
      <el-upload
        ref="uploadRef"
        drag
        action=""
        :auto-upload="false"
        :on-change="handleUpload"
        :limit="1"
        accept="image/*"
      >
        <el-icon style="font-size: 48px; color: #80bff6; margin-bottom: 10px;"><Upload /></el-icon>
        <div>拖拽参考图片到此处，或 <span style="color: #409eff;">点击选择文件</span></div>
      </el-upload>

      <div v-if="previewUrl" style="margin-top: 20px; text-align: center;">
        <el-image
          :src="previewUrl"
          style="max-width: 300px; max-height: 200px; border-radius: 8px;"
          fit="contain"
          :preview-src-list="[previewUrl]"
        />
        <el-button type="primary" @click="handleSearch" style="margin-top: 16px;" :loading="searching">
          开始图搜图
        </el-button>
        <el-button @click="resetUpload" style="margin-top: 16px; margin-left: 10px;">
          重新上传
        </el-button>
      </div>
    </el-card>

    <div v-if="searching" style="text-align: center; padding: 40px;">
      <el-icon style="font-size: 32px; color: #409eff; animation: spin 1s linear infinite;"><Loading /></el-icon>
      <p style="color: #999; margin-top: 10px;">正在检索中...</p>
    </div>

    <div v-else-if="results.length === 0 && searched" style="text-align: center; padding: 60px;">
      <el-empty description="未找到相似的图片，请尝试其他参考图片" />
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
          </el-card>
        </el-col>
      </el-row>
    </div>

    <el-dialog v-model="dialogVisible" title="图片详情" width="600px">
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
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { searchByImage } from '../api/index.js'
import { ElMessage } from 'element-plus'

const uploadRef = ref(null)
const previewUrl = ref('')
const selectedFile = ref(null)
const searching = ref(false)
const searched = ref(false)
const results = ref([])
const dialogVisible = ref(false)
const selectedPhoto = ref(null)

function handleUpload(file) {
  selectedFile.value = file.raw
  previewUrl.value = URL.createObjectURL(file.raw)
  searched.value = false
  results.value = []
}

async function handleSearch() {
  if (!selectedFile.value) return
  searching.value = true
  searched.value = true
  try {
    const res = await searchByImage(selectedFile.value)
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

function resetUpload() {
  uploadRef.value?.clearFiles()
  previewUrl.value = ''
  selectedFile.value = null
  searched.value = false
  results.value = []
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
