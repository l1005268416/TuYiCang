<template>
  <el-container style="min-height: 100vh" class="app-container">
    <el-header class="app-header">
      <div class="header-content">
        <div class="logo-section" @click="$router.push('/')">
          <svg class="logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
            <circle cx="8.5" cy="8.5" r="1.5"/>
            <polyline points="21,15 16,10 5,21"/>
          </svg>
          <span class="logo-text">图忆仓</span>
        </div>
        
        <el-menu 
          mode="horizontal" 
          class="nav-menu"
          :ellipsis="false"
          router
        >
          <el-menu-item index="/">
            <el-icon><HomeFilled /></el-icon>
            <span>首页</span>
          </el-menu-item>
          <el-menu-item index="/text-search">
            <el-icon><Search /></el-icon>
            <span>文搜图</span>
          </el-menu-item>
          <el-menu-item index="/image-search">
            <el-icon><Picture /></el-icon>
            <span>图搜图</span>
          </el-menu-item>
          <el-menu-item index="/album">
            <el-icon><FolderOpened /></el-icon>
            <span>相册管理</span>
          </el-menu-item>
        </el-menu>

        <el-button class="config-btn" @click="$router.push('/config')">
          <el-icon><Setting /></el-icon>
          <span>配置</span>
        </el-button>
      </div>
    </el-header>

    <el-main class="app-main">
      <router-view />
    </el-main>

    <el-footer class="app-footer">
      <span>© 2026 图忆仓 TuYiCang · 私有化本地相册知识库</span>
    </el-footer>
  </el-container>
</template>

<script setup>
import { HomeFilled, Search, Picture, FolderOpened, Setting } from '@element-plus/icons-vue'
</script>

<style>
:root {
  --primary-color: #6366f1;
  --primary-light: #818cf8;
  --primary-dark: #4f46e5;
  --bg-dark: #0f172a;
  --bg-card: #1e293b;
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --border-color: #334155;
}

html, body, #app {
  height: 100%;
  margin: 0;
  background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
  min-height: 100vh;
}

.app-container {
  background: transparent;
}

.app-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  height: 64px;
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(99, 102, 241, 0.2);
  display: flex;
  align-items: center;
  padding: 0;
}

.header-content {
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.logo-section:hover {
  opacity: 0.8;
}

.logo-icon {
  width: 32px;
  height: 32px;
  color: #818cf8;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #818cf8, #c084fc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav-menu {
  background: transparent !important;
  border: none !important;
  flex: 1;
  justify-content: center;
  margin-left: 40px;
}

.nav-menu .el-menu-item {
  color: #94a3b8 !important;
  font-size: 14px;
  font-weight: 500;
  border: none !important;
  border-radius: 8px;
  margin: 0 4px;
  transition: all 0.2s;
}

.nav-menu .el-menu-item:hover {
  color: #f8fafc !important;
  background: rgba(99, 102, 241, 0.15) !important;
}

.nav-menu .el-menu-item.is-active {
  color: #818cf8 !important;
  background: rgba(99, 102, 241, 0.2) !important;
}

.nav-menu .el-menu-item .el-icon {
  margin-right: 6px;
}

.config-btn {
  background: rgba(99, 102, 241, 0.15) !important;
  border: 1px solid rgba(99, 102, 241, 0.3) !important;
  color: #94a3b8 !important;
  border-radius: 8px;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.config-btn:hover {
  background: rgba(99, 102, 241, 0.25) !important;
  border-color: rgba(99, 102, 241, 0.5) !important;
  color: #f8fafc !important;
}

.app-main {
  margin-top: 64px;
  min-height: calc(100vh - 64px - 48px);
  padding: 24px;
}

.app-footer {
  text-align: center;
  color: #64748b;
  font-size: 13px;
  padding: 16px;
  background: rgba(15, 23, 42, 0.5);
  border-top: 1px solid rgba(99, 102, 241, 0.1);
}

@media (max-width: 768px) {
  .header-content {
    padding: 0 12px;
  }
  
  .logo-text {
    display: none;
  }
  
  .nav-menu {
    margin-left: 0;
  }
  
  .nav-menu .el-menu-item span {
    display: none;
  }
  
  .config-btn span {
    display: none;
  }
}
</style>
