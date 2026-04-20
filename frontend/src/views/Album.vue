<template>
  <div style="padding: 20px; max-width: 1400px; margin: 0 auto;">
    <h2 style="margin-bottom: 20px;">相册管理</h2>

    <el-row :gutter="20">
      <el-col :span="4">
        <el-card shadow="hover">
          <template #header>
            <span>文件夹分类</span>
          </template>
          <el-tree
            :data="categories"
            :props="{ label: 'name', children: 'children' }"
            style="background: transparent;"
            @node-click="handleCategoryClick"
          />
        </el-card>
      </el-col>

      <el-col :span="20">
        <el-card style="margin-bottom: 16px;">
          <el-row :gutter="10" align="middle">
            <el-col :span="6">
              <el-input v-model="searchTag" placeholder="搜索标签" clearable />
            </el-col>
            <el-col :span="6">
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始"
                end-placeholder="结束"
                style="width: 100%;"
              />
            </el-col>
            <el-col :span="4">
              <el-button type="primary" @click="loadPhotos">查询</el-button>
            </el-col>
            <el-col :span="4" style="text-align: right;">
              <span style="color: #999; font-size: 12px;">共 {{ total }} 张图片</span>
            </el-col>
          </el-row>
        </el-card>

        <el-row :gutter="10">
          <el-col :span="4" v-for="photo in photos" :key="photo.image_id">
            <el-card shadow="hover" style="cursor: pointer;" @click="showDetail(photo)">
              <el-image
                :src="getThumbUrl(photo.thumb_path)"
                style="width: 100%; height: 120px; border-radius: 4px;"
                fit="cover"
              />
              <div style="margin-top: 4px; font-size: 11px; color: #999; overflow: hidden;
                          text-overflow: ellipsis; white-space: nowrap;">
                {{ photo.folder_tag || '根目录' }}
              </div>
              <div style="margin-top: 4px; font-size: 11px; color: #666; overflow: hidden;
                          text-overflow: ellipsis; white-space: nowrap;">
                {{ photo.shoot_time || photo.create_time || '' }}
              </div>
            </el-card>
          </el-col>
        </el-row>

        <div style="text-align: center; margin-top: 20px;">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="total"
            layout="prev, pager, next"
            @current-change="handlePageChange"
          />
        </div>
      </el-col>
    </el-row>

    <el-dialog v-model="dialogVisible" title="图片详情" width="700px">
      <div v-if="selectedPhoto">
        <el-image
          :src="getOriginalUrl(selectedPhoto.original_path)"
          style="width: 100%; max-height: 400px; border-radius: 4px;"
          fit="contain"
        />
        <div style="margin-top: 16px;">
          <p><strong>描述：</strong>{{ selectedPhoto.description }}</p>
          <p><strong>标签：</strong>
            <el-tag v-for="tag in (selectedPhoto.tags || '').split(',')" :key="tag" style="margin-right: 4px;">
              {{ tag }}
            </el-tag>
            <el-button text size="small" @click="editTags" style="margin-left: 8px;">编辑</el-button>
          </p>
          <p v-if="selectedPhoto.shoot_time"><strong>拍摄时间：</strong>{{ selectedPhoto.shoot_time }}</p>
          <p v-if="selectedPhoto.camera_model"><strong>相机型号：</strong>{{ selectedPhoto.camera_model }}</p>
          <p v-if="selectedPhoto.gps"><strong>GPS位置：</strong>{{ selectedPhoto.gps }}</p>
          <p v-if="selectedPhoto.resolution"><strong>分辨率：</strong>{{ selectedPhoto.resolution }}</p>
          <p><strong>路径：</strong>{{ selectedPhoto.original_path }}</p>
          <p><strong>入库时间：</strong>{{ selectedPhoto.create_time }}</p>
        </div>
        <div style="margin-top: 20px; text-align: right;">
          <el-button type="danger" @click="handleDelete(selectedPhoto.image_id)">删除图片</el-button>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="tagDialogVisible" title="编辑标签" width="400px">
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
  folderTag.value = node.name
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
