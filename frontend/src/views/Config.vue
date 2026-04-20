<template>
  <div style="padding: 20px; max-width: 1200px; margin: 0 auto;">
    <h2 style="margin-bottom: 20px;">配置管理</h2>

    <el-tabs v-model="activeGroup" type="card">
      <el-tab-pane
        v-for="key in allGroups"
        :key="key"
        :label="getGroupLabel(key)"
        :name="key"
      />
    </el-tabs>

    <div style="margin-top: 20px;">
      <el-row :gutter="20">
        <el-col :span="12" v-for="item in visibleConfigs" :key="item._saveKey">
          <el-card shadow="hover" style="margin-bottom: 16px;">
            <template #header>
              <div style="display: flex; align-items: center; justify-content: space-between;">
                <span>
                  <span v-if="item.is_required" style="color: #f56c6c; margin-right: 4px;">*</span>
                  {{ item._keyLabel }}
                </span>
                <el-tooltip :content="item.desc" placement="top">
                  <el-icon style="cursor: help;"><QuestionFilled /></el-icon>
                </el-tooltip>
              </div>
            </template>
            <div style="margin-bottom: 8px; color: #999; font-size: 12px;">
              当前: {{ item.value }}
            </div>
            <el-input
              v-if="isBoolean(item.value)"
              :model-value="item._localValue"
              @update:model-value="onInput(item._saveKey, $event)"
            >
              <template #prepend>
                <el-switch
                  :model-value="item._localValue === 'true'"
                  @update:model-value="onInput(item._saveKey, $event ? 'true' : 'false')"
                  :active-value="true"
                  :inactive-value="false"
                />
              </template>
            </el-input>
            <el-input-number
              v-else-if="isNumber(item.value)"
              :model-value="parseNumber(item._localValue)"
              @update:model-value="onInput(item._saveKey, $event?.toString())"
              :min="0"
              style="width: 100%;"
            />
            <el-input
              v-else
              :model-value="item._localValue"
              @update:model-value="onInput(item._saveKey, $event)"
              style="width: 100%;"
            />
          </el-card>
        </el-col>
      </el-row>
    </div>

    <div style="margin-top: 20px; display: flex; gap: 10px;">
      <el-button type="primary" @click="handleSave" :loading="saving">保存配置</el-button>
      <el-button @click="handleReset">重置为默认值</el-button>
      <el-button @click="handleExport">导出配置</el-button>
      <el-upload
        action=""
        :auto-upload="false"
        :on-change="handleImport"
        :limit="1"
        accept=".json"
      >
        <el-button>
          <el-icon><Upload /></el-icon> 导入配置
        </el-button>
      </el-upload>
    </div>

    <div v-if="errorMsg" style="margin-top: 16px; color: #f56c6c;">
      <el-alert :title="errorMsg" type="error" show-close />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getConfigs, batchUpdateConfigs, resetConfigs, exportConfigs } from '../api/index.js'
import { ElMessage, ElMessageBox } from 'element-plus'
import { QuestionFilled, Upload } from '@element-plus/icons-vue'

const allGroups = ['core', 'model_services', 'performance', 'retrieval', 'preprocessing']

const groupLabels = {
  core: '核心系统配置',
  model_services: '模型服务配置',
  performance: '性能与并发控制',
  retrieval: '检索策略与算法',
  preprocessing: '图片预处理与清洗'
}

const activeGroup = ref('core')
const flatConfigs = ref({})
const localValues = ref({})
const saving = ref(false)
const errorMsg = ref('')

const configsByGroup = computed(() => {
  const result = {}
  for (const g of allGroups) {
    result[g] = []
  }
  for (const [fullKey, meta] of Object.entries(flatConfigs.value)) {
    let group = meta._group || 'core'
    let matchedGroup = 'core'
    for (const g of allGroups) {
      if (group === g || group.startsWith(g + '.')) {
        matchedGroup = g
        break
      }
    }
    let keyLabel = fullKey
    let saveKey = fullKey
    if (matchedGroup === 'model_services') {
      keyLabel = fullKey.startsWith('model_services.') ? fullKey.slice('model_services.'.length) : fullKey
    }
    result[matchedGroup].push({
      _saveKey: saveKey,
      _keyLabel: keyLabel,
      value: meta.value,
      _localValue: localValues.value[saveKey] ?? meta.value,
      desc: meta.desc || '',
      is_required: meta.is_required || false
    })
  }
  // Sort model_services to match INT_KEYS order
  const intKeys = {
    core: ['photo_root_path', 'cache_dir', 'db_path', 'log_level'],
    model_services: ['vlm.api_base', 'vlm.model_name', 'vlm.api_key', 'vlm.temperature',
                      'text_embedding.api_base', 'text_embedding.model_name', 'text_embedding.api_key',
                      'text_embedding.timeout', 'vision_embedding.api_base', 'vision_embedding.model_name',
                      'vision_embedding.api_key', 'vision_embedding.timeout'],
    performance: ['max_concurrent_requests', 'text_embedding_batch_size', 'request_timeout', 'max_retries', 'retry_delay'],
    retrieval: ['text_similarity_threshold', 'vision_similarity_threshold', 'default_top_k', 'sort_by_similarity'],
    preprocessing: ['valid_extensions', 'min_file_size_kb', 'max_file_size_mb', 'target_max_edge', 'use_file_mtime_as_fallback'],
  }
  for (const g of allGroups) {
    const order = intKeys[g] || []
    if (order.length > 0) {
      result[g].sort((a, b) => {
        const ia = order.indexOf(a._keyLabel)
        const ib = order.indexOf(b._keyLabel)
        if (ia === -1 && ib === -1) return 0
        if (ia === -1) return 1
        if (ib === -1) return -1
        return ia - ib
      })
    }
  }
  return result
})

const visibleConfigs = computed(() => {
  return configsByGroup.value[activeGroup.value] || []
})

function getGroupLabel(key) {
  return groupLabels[key] || key
}

function isBoolean(val) {
  return val === 'true' || val === 'false'
}

function isNumber(val) {
  if (val === '' || val == null) return false
  return !isNaN(Number(val))
}

function parseNumber(val) {
  if (val === '' || val == null) return 0
  return Number(val)
}

function onInput(saveKey, newValue) {
  localValues.value[saveKey] = String(newValue)
}

onMounted(async () => {
  await loadConfigs()
})

async function loadConfigs() {
  errorMsg.value = ''
  try {
    const res = await getConfigs()
    if (res.data.success) {
      flatConfigs.value = res.data.data
      syncLocalValues()
    }
  } catch (e) {
    errorMsg.value = '配置加载失败'
    console.error(e)
  }
}

function syncLocalValues() {
  const flat = {}
  for (const [key, meta] of Object.entries(flatConfigs.value)) {
    flat[key] = meta.value != null ? String(meta.value) : ''
  }
  localValues.value = flat
}

async function handleSave() {
  saving.value = true
  errorMsg.value = ''
  try {
    const updates = []
    for (const [key, localVal] of Object.entries(localValues.value)) {
      const orig = flatConfigs.value[key]
      if (!orig) continue
      if (String(orig.value) !== String(localVal)) {
        updates.push({
          config_key: key,
          config_value: String(localVal)
        })
      }
    }

    if (updates.length === 0) {
      ElMessage.info('没有修改的配置')
      saving.value = false
      return
    }

    const res = await batchUpdateConfigs(updates)
    if (res.data.success) {
      ElMessage.success('配置保存成功')
      await loadConfigs()
    } else {
      errorMsg.value = res.data.message || '保存失败'
      if (res.data.data?.failed_items?.length) {
        errorMsg.value += '\n' + res.data.data.failed_items.map(i => `${i.config_key}: ${i.error}`).join('\n')
      }
    }
  } catch (e) {
    errorMsg.value = '保存请求失败'
    console.error(e)
  } finally {
    saving.value = false
  }
}

async function handleReset() {
  try {
    await ElMessageBox.confirm('确定将所有配置恢复为默认值吗？', '确认重置', {
      type: 'warning'
    })
    const res = await resetConfigs()
    if (res.data.success) {
      ElMessage.success('配置已重置为默认值')
      await loadConfigs()
    }
  } catch {
    // cancelled
  }
}

async function handleExport() {
  try {
    const res = await exportConfigs()
    const blob = new Blob([res.data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `tuyicang_config_${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('配置导出成功')
  } catch (e) {
    ElMessage.error('配置导出失败')
  }
}

async function handleImport(file) {
  try {
    const text = await file.text()
    const formData = new FormData()
    formData.append('file', new Blob([text], { type: 'application/json' }), file.name)

    const { importConfigs: importApi } = await import('../api/index.js')
    const res = await importApi(file)
    if (res.data.success) {
      ElMessage.success('配置导入成功')
      await loadConfigs()
    } else {
      ElMessage.error('配置导入失败')
    }
  } catch (e) {
    ElMessage.error('配置导入失败')
  }
}
</script>
