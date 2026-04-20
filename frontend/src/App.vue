<template>
  <el-container style="min-height: 100vh">
    <el-header style="display: flex; align-items: center; justify-content: space-between; background: #409eff; color: white; padding: 0 20px;">
      <div style="display: flex; align-items: center; gap: 20px;">
        <span style="font-size: 20px; font-weight: bold;">图忆仓 TuYiCang</span>
        <el-menu mode="horizontal" background-color="#409eff" text-color="white" active-text-color="#fff" router style="border: none;">
          <el-menu-item index="/">首页</el-menu-item>
          <el-menu-item index="/text-search">文搜图</el-menu-item>
          <el-menu-item index="/image-search">图搜图</el-menu-item>
          <el-menu-item index="/album">相册管理</el-menu-item>
        </el-menu>
      </div>
      <el-button text @click="$router.push('/config')" style="color: white;">
        <el-icon><Setting /></el-icon> 配置
      </el-button>
    </el-header>

    <el-main>
      <router-view />
    </el-main>

    <el-footer style="text-align: center; color: #999; font-size: 12px; padding: 10px;">
      © 2026 图忆仓 TuYiCang - 私有化本地相册知识库
    </el-footer>
  </el-container>
</template>

<script setup>
</script>

<style>
html, body, #app {
  height: 100%;
  margin: 0;
}
</style>
