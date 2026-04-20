<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">
        <el-icon class="title-icon"><Setting /></el-icon>
        配置管理
      </h2>
      <p class="page-desc">管理系统配置参数</p>
    </div>

    <div class="config-tabs">
      <el-tabs v-model="activeGroup" type="card" class="config-tabs-inner">
        <el-tab-pane
          v-for="key in allGroups"
          :key="key"
          :label="getGroupLabel(key)"
          :name="key"
        />
      </el-tabs>
    </div>

    <div class="configs-grid">
      <div 
        v-for="item in visibleConfigs" 
        :key="item._saveKey" 
        class="config-card"
      >
        <div class="config-header">
          <span class="config-label">
            <span v-if="item.is_required" class="required-mark">*</span>
            {{ item._keyLabel }}
          </span>
          <el-tooltip :content="item.desc" placement="top">
            <el-icon class="help-icon"><QuestionFilled /></el-icon>
          </el-tooltip>
        </div>
        <div class="config-current">
          当前值: <code>{{ item.value }}</code>
        </div>
        
        <div class="config-input">
          <el-switch
            v-if="isBoolean(item.value)"
            :model-value="item._localValue === 'true'"
            @update:model-value="onInput(item._saveKey, $event ? 'true' : 'false')"
            active-text="是"
            inactive-text="否"
            class="bool-switch"
          />
          <el-input-number
            v-else-if="isNumber(item.value)"
            :model-value="parseNumber(item._localValue)"
            @update:model-value="onInput(item._saveKey, $event?.toString())"
            :min="0"
            class="number-input"
          />
          <el-input
            v-else
            :model-value="item._localValue"
            @update:model-value="onInput(item._saveKey, $event)"
            class="text-input"
          />
        </div>
      </div>
    </div>

    <div class="actions-bar">
      <el-button type="primary" @click="handleSave" :loading="saving" class="action-btn">
        <el-icon><Check /></el-icon>
        保存配置
      </el-button>
      <el-button @click="handleReset" class="action-btn">
        <el-icon><RefreshLeft /></el-icon>
        重置为默认值
      </el-button>
      <el-button @click="handleExport" class="action-btn">
        <el-icon><Download /></el-icon>
        导出配置
      </el-button>
      <el-upload
        action=""
        :auto-upload="false"
        :on-change="handleImport"
        :limit="1"
        accept=".json"
        class="import-upload"
      >
        <el-button class="action-btn">
          <el-icon><Upload /></el-icon>
          导入配置
        </el-button>
      </el-upload>
    </div>

    <div v-if="errorMsg" class="error-message">
      <el-alert :title="errorMsg" type="error" show-close />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getConfigs, batchUpdateConfigs, resetConfigs, exportConfigs } from '../api/index.js'
import { ElMessage, ElMessageBox } from 'element-plus'
import { QuestionFilled, Upload, Setting, Check, RefreshLeft, Download } from '@element-plus/icons-vue'

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

<style scoped>
.page-container {
  max-width: 1200px;
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
  color: #f472b6;
}

.page-desc {
  color: #64748b;
  margin: 0;
}

.config-tabs {
  background: rgba(30, 41, 59, 0.6);
  border-radius: 16px;
  padding: 20px 20px 0 20px;
  border: 1px solid rgba(99, 102, 241, 0.15);
  margin-bottom: 24px;
}

.config-tabs-inner {
  background: transparent !important;
}

.config-tabs-inner :deep(.el-tabs__header) {
  margin: 0;
}

.config-tabs-inner :deep(.el-tabs__nav-wrap) {
  background: transparent;
}

.config-tabs-inner :deep(.el-tabs__item) {
  color: #64748b;
  background: rgba(15, 23, 42, 0.4);
  border: 1px solid transparent;
  border-radius: 10px 10px 0 0;
  margin-right: 4px;
  padding: 12px 20px;
}

.config-tabs-inner :deep(.el-tabs__item:hover) {
  color: #f8fafc;
}

.config-tabs-inner :deep(.el-tabs__item.is-active) {
  color: #818cf8;
  background: rgba(99, 102, 241, 0.2);
  border-color: rgba(99, 102, 241, 0.2);
}

.config-tabs-inner :deep(.el-tabs__content) {
  display: none;
}

.configs-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 32px;
}

.config-card {
  background: rgba(30, 41, 59, 0.6);
  border-radius: 14px;
  padding: 20px;
  border: 1px solid rgba(99, 102, 241, 0.15);
  transition: all 0.3s;
}

.config-card:hover {
  border-color: rgba(99, 102, 241, 0.3);
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.config-label {
  color: #f8fafc;
  font-weight: 500;
  font-size: 14px;
}

.required-mark {
  color: #f87171;
  margin-right: 4px;
}

.help-icon {
  color: #64748b;
  cursor: help;
  transition: color 0.2s;
}

.help-icon:hover {
  color: #818cf8;
}

.config-current {
  color: #64748b;
  font-size: 12px;
  margin-bottom: 12px;
}

.config-current code {
  background: rgba(15, 23, 42, 0.6);
  padding: 2px 8px;
  border-radius: 4px;
  color: #34d399;
  font-family: monospace;
}

.config-input :deep(.el-switch) {
  --el-switch-on-color: #6366f1;
}

.config-input :deep(.el-input__wrapper) {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(99, 102, 241, 0.2);
  box-shadow: none;
  border-radius: 10px;
}

.config-input :deep(.el-input__inner) {
  color: #f8fafc;
}

.config-input :deep(.el-input-number) {
  width: 100%;
}

.config-input :deep(.el-input-number .el-input__wrapper) {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.actions-bar {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-btn {
  padding: 12px 20px;
  border-radius: 10px;
}

.action-btn.primary {
  background: linear-gradient(135deg, #6366f1, #818cf8) !important;
  border: none !important;
}

.action-btn:not(.primary) {
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  color: #f8fafc !important;
}

.action-btn:not(.primary):hover {
  background: rgba(255, 255, 255, 0.1) !important;
}

.import-upload {
  display: inline-block;
}

.error-message {
  margin-top: 20px;
}

@media (max-width: 1024px) {
  .configs-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .actions-bar {
    flex-direction: column;
  }

  .actions-bar .el-button {
    width: 100%;
  }
}
</style>
