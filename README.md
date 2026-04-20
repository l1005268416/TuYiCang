# 图忆仓（TuYiCang）

[简体中文](README.md) | [English](README_EN.md)

私有化本地相册知识库，基于多模态AI+多模态统一空间embedding技术，实现文搜图 + 图搜图双核心功能
<div align="center">
  <img src="images/1.png" alt="Project Screenshot" width="30%" height="170px">
  <img src="images/2.png" alt="Project Screenshot" width="30%" height="170px">
  <img src="images/4.png" alt="Project Screenshot" width="30%" height="170px">
</div>

## 项目简介

图忆仓是一款轻量化的本地相册检索系统，通过多模态AI技术实现智能图片管理。系统采用私有化部署，所有模型、数据、图片均存储于本地设备，无外网调用，保障用户隐私安全。

### 核心特性

- **双模检索**：支持文本搜索图片（文搜图）和图片搜索图片（图搜图）
- **智能入库**：自动扫描、预处理、去重、提取EXIF信息
- **增量更新**：实时监控本地相册目录，自动同步新增、修改、删除的图片
- **标签管理**：AI自动生成图片标签，支持手动编辑和筛选
- **私有化部署**：所有数据本地存储，无需联网，隐私安全
- **轻量化设计**：量化模型，显存占用低，适配个人电脑部署

## 技术栈

### 后端

- **编程语言**：Python 3.9.10
- **多模态模型（VLM）**：qwen3.5-0.8b（Ollama部署）
- **文本嵌入模型**：qwen3-embedding:0.6b（Ollama部署）
- **视觉嵌入模型**：Qwen3-VL-Embedding-2B（vLLM部署）
- **向量数据库**：milvus:v2.4.8
- **元数据数据库**：SQLite 3.41.2


### 前端

- **框架**：Vue 3 + Element Plus
- **运行环境**：Node.js 16.18.0
- **架构**：前后端分离

### 辅助工具

- Pillow 9.5.0（图片处理）
- exifread 2.3.2（EXEXIF解析）
- watchdog 2.3.1（文件夹监控）
- PyYAML 6.0（配置解析）
- requests 2.31.0（API调用）

## 系统架构

系统采用8层架构设计，各层独立解耦：

1. **存储层**：本地磁盘存储（原图、预处理图、缩略图、向量库、数据库）
2. **数据库层**：SQLite数据库（元数据表、系统配置表）
3. **预处理层**：文件扫描、格式兼容、EXIF解析、MD5去重、图片缩放
4. **模型推理层**：VLM、文本嵌入、视觉嵌入模型调用
5. **向量索引层**：Milvus 向量库，支持文本语义索引和视觉相似度索引
6. **业务逻辑层**：检索引擎、增量监控、去重逻辑、结果后处理

7. **配置管理层**：配置加载、校验、更新、备份与重置
8. **用户交互层**：前端页面（首页、文搜图、图搜图、相册管理、配置管理）

## 快速开始

### 环境要求

- Python 3.9.10+
- Node.js 16.18.0+
- GPU 如果不需要跑长上下文，16GB显存即可
- 至少 8GB 内存
- 至少 10GB 可用磁盘空间

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/l1005268416/TuYiCang.git
cd TuYiCang
```

#### 2. 安装后端依赖

```bash
pip install -r requirements.txt
```

#### 3. 安装前端依赖

```bash
cd frontend
npm install
```

#### 4. 部署模型服务

**部署 Ollama（VLM + 文本嵌入模型）**

```bash
# 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 拉取模型
ollama pull qwen3.5-0.8b
ollama pull qwen3-embedding:0.6b

# 启动 Ollama 服务(通常状况系统会自启)
ollama serve
```

**部署 vLLM（视觉嵌入模型）**

```bash
# 安装 vLLM
pip install vllm

# 启动视觉嵌入模型服务
vllm serve Qwen3-VL-Embedding-2B \
--runner pooling \
--max-model-len 36000 \
--served-model-name \
Qwen3-VL-Embedding-2B \
--port 8022
```

#### 5. 配置系统

首次启动后，通过 Web UI 界面进行系统配置：

1. 访问 http://localhost:8080
2. 进入"配置管理"页面
3. 配置相册路径、模型服务地址等参数
4. 配置自动保存到数据库

#### 6. 启动服务

**启动后端服务**

```bash
python app.py
```

**启动前端服务**

```bash
cd frontend
npm run dev
```

#### 7. 访问系统

打开浏览器访问：http://localhost:8080

## 使用指南

### 图片入库

1. 在配置文件中设置相册根路径
2. 系统自动扫描目录中的图片
3. 执行预处理（去重、缩放、EXIF解析）
4. 调用模型生成文本描述、标签和向量
5. 数据入库（元数据、向量、缩略图）

### 文搜图

1. 进入"文搜图"页面
2. 输入搜索关键词（如"海边日落"、"猫咪"）
3. 系统将关键词转换为文本语义向量
4. 在向量库中检索相似图片
5. 展示检索结果（按相似度排序）

### 图搜图

1. 进入"图搜图"页面
2. 上传参考图片
3. 系统将图片转换为视觉向量
4. 在向量库中检索相似图片
5. 展示检索结果（按相似度排序）

### 增量更新

系统通过 watchdog 实时监控相册目录：
- 新增图片：自动入库
- 修改图片：重新处理
- 删除图片：从数据库中移除

### 标签管理

1. 在相册管理页面查看图片标签
2. 支持手动编辑标签
3. 支持按标签筛选图片
4. 支持批量标签操作

## 项目结构

```
TuYiCang/
├── backend/                 # 后端代码
│   ├── core/               # 核心模块
│   │   ├── preprocessing/  # 预处理模块
│   │   ├── inference/      # 模型推理模块
│   │   ├── vector/         # 向量索引模块
│   │   └── business/       # 业务逻辑模块
│   ├── database/           # 数据库模块
│   ├── config/             # 配置管理模块
│   ├── api/                # API接口
│   └── main.py             # 主程序入口
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── components/     # 组件
│   │   ├── views/          # 页面
│   │   ├── api/            # API调用
│   │   └── utils/          # 工具函数
│   └── package.json
├── config/                 # 配置文件
│   └── config.yaml
├── data/                   # 数据目录
│   ├── database/           # SQLite数据库
│   ├── vector/             # 向量库
│   └── cache/              # 缓存文件
│       └── thumb/          # 缩略图
├── doc/                    # 文档
│   └── TuYiCangSDDD.md    # 详细设计文档
├── requirements.txt        # Python依赖
└── README.md              # 项目说明
```

## 配置说明

系统配置通过 Web UI 界面进行管理，配置数据存储在 SQLite 数据库中。

### 主要配置项

- **相册配置**
  - photo_root_path：相册根路径
  - valid_extensions：支持的图片格式（.jpg、.jpeg、.png、.webp、.bmp）
  - min_file_size_kb：最小文件大小（默认 50KB）
  - max_file_size_mb：最大文件大小（默认 50MB）

- **模型服务配置**
  - ollama_api_url：Ollama API地址（默认 http://localhost:11434）
  - vllm_api_url：vLLM API地址（默认 http://localhost:8022）

- **预处理配置**
  - target_max_edge：图片缩放最大边长（默认 1024 像素）
  - enable_vision_dedup：是否启用视觉相似去重（默认 true）

- **检索配置**
  - text_top_k：文搜图返回结果数量（（默认 20）
  - vision_top_k：图搜图返回结果数量（默认 20）
  - vision_similarity_threshold：视觉相似度阈值（默认 0.65）

- **系统配置**
  - cache_dir：缓存目录（默认 ./data/cache）
  - database_path：数据库路径（默认 ./data/database/tuycang.db）
  - vector_store_path：向量库路径（默认 ./data/vector）

## 性能指标

- **支持图片数量**：10,000+
- **文搜图响应时间**：< 1秒
- **图搜图响应时间**：< 1秒
- **入库速度**：约 5-10 张/分钟（取决于硬件配置）
- **显存占用**：约 6-12GB
- **速率**：V100显卡下，VLM速度约0.55s/次，文本嵌入约0.26s/次，视觉嵌入约0.20s/次
``` plain
[2026-04-20 18:20:43] [INFO] [app.services.inference] VLM inference completed in 0.55s (attempt 1)
[2026-04-20 18:20:44] [INFO] [httpx] HTTP Request: POST http://192.168.1.149:11434/v1/embeddings "HTTP/1.1 200 OK"
[2026-04-20 18:20:44] [INFO] [app.services.inference] Text embedding inference completed in 0.26s (attempt 1)
[2026-04-20 18:20:44] [INFO] [httpx] HTTP Request: POST http://192.168.1.149:8022/v1/embeddings "HTTP/1.1 200 OK"
[2026-04-20 18:20:44] [INFO] [app.services.inference] Vision embedding inference completed in 0.20s (attempt 1)
```
## 常见问题

### Q: 模型推理速度慢怎么办？

A: 可以尝试以下优化：
1. 使用GPU加速
2. 调整批处理大小
3. 使用更小的模型版本

### Q: 如何备份数据？

A: 定期备份以下目录：
- `data/database/`（元数据数据库）
- `data/vector/`（向量库）
- `data/cache/`（缩略图缓存）

### Q: 支持哪些图片格式？

A: 支持 .jpg、.jpeg、.png、.webp、.bmp 格式，其他格式会自动转换为 jpg。

### Q: 如何重置系统？

A: 删除 `C:\Users\Username\AppData\Local\tuyicang` 目录下的所有文件，系统会自动重新初始化。
B: 清空Milvus数据

### Q: 可以使用其他模型么？
A: 可以，模型部署可以多样化，系统可以按照openai的api调用规范进行扩展。

### Q: 显存为什么占用这么多？

A:Qwen3-VL-Embedding-2B是显存占用大头（13G），因个人显卡(V100)限制，无法运行相关的量化模型，试过Qwen3-VL-Embedding-2B-GPTQ-Int4，图片转向量会数组超限。如果你的显卡支持Qwen3-VL-Embedding-2B-GPTQ-Int4，将大大降低显存占用。

### Q: milvus必须部署么？

A: 可以不部署，不部署的情况下向量存储进内存，重启后会丢失。用milvus的话，可以用docker部署。

### Q: 为什么文本嵌入也使用了Qwen3-VL-Embedding-2B？

A: Qwen3-VL-Embedding-2B是统一语义空间，是支持文本和视觉；文搜图利用Qwen3-VL-Embedding-2B效果要比经VLM模型识别后嵌入，再通过文本嵌入模型（qwen3-embedding）做向量库的检索效果好，无论VLM多么强大，它生成的文字描述都是一种有损压缩。许多无法用简单文字精确表达的视觉信息会大量丢失。

<img src="images/3.png" alt="Qwen3-VL-Embedding-2B文搜图效果" width="45%" height="300px">

## 开发计划
- [√] 架构搭建
- [√] VLM模型推理功能
- [√] 文本嵌入功能
- [√] 图片嵌入功能
- [√] 异步推理与重试功能
- [√] 元数据管理功能
- [√] 图片初始化加载功能
- [√] 增量更新功能
- [√] 文搜图功能
- [√] 图搜图功能
- [√] 系统配置管理功能
- [√] 接口开发
- [√] 相册管理界面功能
- [√] 添加图片分类功能
- [ ] 支持批量导入导出

## 许可证

MIT License

## 联系方式

- 项目地址：https://github.com/l1005268416/TuYiCang
- 问题反馈：https://github.com/l1005268416/TuYiCang/issues

## 致谢

感谢以下开源项目的支持：
- Ollama
- vLLM
- Milvus
- Vue.js
- Element Plus
