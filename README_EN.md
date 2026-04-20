# TuYiCang
A private local photo album knowledge base with dual core functions: **text-to-image search** and **image-to-image search**
English | [简体中文](README.md)
<div align="center">
  <img src="images/1.png" alt="Project Screenshot" width="45%" height="300px">
  <img src="images/2.png" alt="Project Screenshot" width="45%" height="300px">
</div>

## Project Introduction
TuYiCang is a lightweight local image retrieval system that realizes intelligent image management through multimodal AI technology.
The system adopts private local deployment. All models, data and images are stored on local devices without external network calls, fully protecting user privacy and data security.

### Core Features
- **Dual-mode Retrieval**: Supports both text-to-image search and image-to-image search
- **Intelligent Import**: Automatic scanning, preprocessing, deduplication and EXIF information extraction
- **Incremental Update**: Real-time monitoring of local album directories, automatic synchronization of newly added, modified and deleted images
- **Tag Management**: AI-generated image tags with support for manual editing and filtering
- **Private Deployment**: All data stored locally, offline available with complete privacy protection
- **Lightweight Design**: Quantized models with low VRAM usage, suitable for personal computer deployment

## Tech Stack
### Backend
- Programming Language: Python 3.9.10
- Multimodal Large Language Model (VLM): qwen3.5-0.8b (deployed via Ollama)
- Text Embedding Model: qwen3-embedding:0.6b (deployed via Ollama)
- Visual Embedding Model: Qwen3-VL-Embedding-2B (deployed via vLLM)
- Vector Database: milvus v2.4.8
- Metadata Database: SQLite 3.41.2

### Frontend
- Framework: Vue 3 + Element Plus
- Runtime Environment: Node.js 16.18.0
- Architecture: Frontend-backend separation

### Auxiliary Libraries
- Pillow 9.5.0 (image processing)
- exifread 2.3.2 (EXIF parsing)
- watchdog 2.3.1 (folder monitoring)
- PyYAML 6.0 (configuration parsing)
- requests 2.31.0 (API requests)

## System Architecture
The system is designed with 8 decoupled layers:
1. **Storage Layer**: Local disk storage (original images, preprocessed images, thumbnails, vector database, relational database)
2. **Database Layer**: SQLite database (metadata tables, system configuration tables)
3. **Preprocessing Layer**: File scanning, format adaptation, EXIF parsing, MD5 deduplication, image resizing
4. **Model Inference Layer**: Invocation of VLM, text embedding and visual embedding models
5. **Vector Index Layer**: Milvus Lite vector database, supporting textual semantic indexing and visual similarity indexing
6. **Business Logic Layer**: Retrieval engine, incremental monitoring, deduplication logic, result post-processing
7. **Configuration Management Layer**: Configuration loading, validation, updating, backup and resetting
8. **User Interaction Layer**: Frontend pages (homepage, text search, image search, album management, settings)

## Quick Start
### Environment Requirements
- Python 3.9.10 or above
- Node.js 16.18.0 or above
- GPU: 16GB VRAM is sufficient if long-context inference is not required
- Minimum 8GB system memory
- Minimum 10GB available disk space

### Installation Steps
#### 1. Clone the repository
```bash
git clone https://github.com/yourusername/TuYiCang.git
cd TuYiCang
```

#### 2. Install backend dependencies
```bash
pip install -r requirements.txt
```

#### 3. Install frontend dependencies
```bash
cd frontend
npm install
```

#### 4. Deploy model services
**Deploy Ollama (VLM + Text Embedding Model)**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull models
ollama pull qwen3.5-0.8b
ollama pull qwen3-embedding:0.6b

# Start Ollama service (auto-start by default)
ollama serve
```

**Deploy vLLM (Visual Embedding Model)**
```bash
# Install vLLM
pip install vllm

# Launch visual embedding model service
vllm serve Qwen3-VL-Embedding-2B \
--runner pooling \
--max-model-len 36000 \
--served-model-name Qwen3-VL-Embedding-2B \
--port 8022
```

#### 5. System Configuration
After the first launch, configure the system via the Web UI:
1. Visit http://localhost:8080
2. Navigate to the **Configuration Management** page
3. Set album path, model service addresses and other parameters
4. Save configurations to the database automatically

#### 6. Start Services
**Start backend service**
```bash
python app.py
```

**Start frontend service**
```bash
cd frontend
npm run dev
```

#### 7. Access the System
Open your browser and visit: http://localhost:8080

## User Guide
### Image Import
1. Set the root album path in the configuration
2. The system automatically scans images in the directory
3. Preprocessing is executed (deduplication, resizing, EXIF parsing)
4. Models are called to generate text descriptions, tags and feature vectors
5. All data is stored (metadata, vectors, thumbnails)

### Text-to-Image Search
1. Enter the **Text Search** page
2. Input keywords (e.g. "sunset by the sea", "cat")
3. The system converts keywords into textual semantic vectors
4. Retrieve similar images from the vector database
5. Display results sorted by similarity

### Image-to-Image Search
1. Enter the **Image Search** page
2. Upload a reference image
3. The system converts the image into visual feature vectors
4. Retrieve similar images from the vector database
5. Display results sorted by similarity

### Incremental Update
The system monitors album directories in real time via watchdog:
- New images: imported automatically
- Modified images: reprocessed automatically
- Deleted images: removed from the database automatically

### Tag Management
1. View image tags on the album management page
2. Support manual tag editing
3. Support image filtering by tags
4. Support batch tag operations

## Project Structure
```
TuYiCang/
├── backend/                 # Backend source code
│   ├── core/               # Core modules
│   │   ├── preprocessing/  # Image preprocessing module
│   │   ├── inference/      # Model inference module
│   │   ├── vector/         # Vector index module
│   │   └── business/       # Business logic module
│   ├── database/           # Database module
│   ├── config/             # Configuration management module
│   ├── api/                # API interfaces
│   └── main.py             # Program entry
├── frontend/               # Frontend source code
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── views/          # Page views
│   │   ├── api/            # Frontend API requests
│   │   └── utils/          # Utility functions
│   └── package.json
├── config/                 # Configuration files
│   └── config.yaml
├── data/                   # Data directory
│   ├── database/           # SQLite database files
│   ├── vector/             # Vector database files
│   └── cache/              # Cache files
│       └── thumb/          # Image thumbnails
├── doc/                    # Documentation
│   └── TuYiCangSDDD.md    # Detailed system design document
├── requirements.txt        # Python dependency list
└── README.md              # Project readme
```

## Configuration Details
System settings are managed via the Web UI, with all configuration data saved in the SQLite database.

### Main Configuration Items
- **Album Settings**
  - photo_root_path: Root path of local album
  - valid_extensions: Supported image formats (.jpg, .jpeg, .png, .webp, .bmp)
  - min_file_size_kb: Minimum file size (default: 50KB)
  - max_file_size_mb: Maximum file size (default: 50MB)

- **Model Service Settings**
  - ollama_api_url: Ollama API address (default: http://localhost:11434)
  - vllm_api_url: vLLM API address (default: http://localhost:8022)

- **Preprocessing Settings**
  - target_max_edge: Maximum edge length for image resizing (default: 1024 pixels)
  - enable_vision_dedup: Enable visual similarity deduplication (default: true)

- **Retrieval Settings**
  - text_top_k: Number of results returned by text search (default: 20)
  - vision_top_k: Number of results returned by image search (default: 20)
  - vision_similarity_threshold: Visual similarity threshold (default: 0.65)

- **System Settings**
  - cache_dir: Cache directory (default: ./data/cache)
  - database_path: Database file path (default: ./data/database/tuycang.db)
  - vector_store_path: Vector storage path (default: ./data/vector)

## Performance Metrics
- Supported image capacity: 10,000+
- Text-to-image search latency: < 2 seconds
- Image-to-image search latency: < 3 seconds
- Image import speed: Approximately 5–10 images per minute (hardware-dependent)
- VRAM usage: Approximately 6–12GB

## FAQ
### Q: Why is model inference slow?
A: Try the following optimizations:
1. Enable GPU acceleration
2. Adjust batch size
3. Switch to smaller model variants

### Q: How to back up project data?
A: Regularly back up the following directories:
- `data/database/` (metadata database)
- `data/vector/` (vector database)
- `data/cache/` (thumbnail cache)

### Q: What image formats are supported?
A: .jpg, .jpeg, .png, .webp, .bmp. All unsupported formats will be automatically converted to JPG.

### Q: How to reset the system?
A:
1. Delete all files under `C:\Users\Username\AppData\Local\tuyicang`, and the system will reinitialize automatically.
2. Clear all data in Milvus.

### Q: Can I use other models?
A: Yes. The system supports flexible model deployment and can be extended following OpenAI-compatible API specifications.

### Q: Why is VRAM usage so high?
A: Qwen3-VL-Embedding-2B consumes the most VRAM (~13GB). Due to hardware limitations of the V100 GPU, quantized versions could not be applied.
The attempted Qwen3-VL-Embedding-2B-GPTQ-Int4 caused array overflow during image vectorization.
If your GPU supports Qwen3-VL-Embedding-2B-GPTQ-Int4, VRAM usage will be greatly reduced.

### Q: Is Milvus mandatory for deployment?
A: No. Without Milvus, vectors will be stored in memory and lost after system restart.
Milvus can also be deployed via Docker for persistent storage.

### Q: Why is Qwen3-VL-Embedding-2B also used for text embedding?
A: Qwen3-VL-Embedding-2B provides a unified text-and-visual semantic space.
Text search based on this model outperforms the pipeline of VLM image captioning + separate text embedding model retrieval.
Text descriptions generated by VLM models are inherently lossy compression, and much fine-grained visual information that cannot be expressed in words will be discarded.

## Development Roadmap
- [√] System architecture construction
- [√] VLM model inference
- [√] Text embedding function
- [√] Image embedding function
- [√] Asynchronous inference & retry mechanism
- [√] Metadata management
- [√] Initial image loading
- [√] Incremental update mechanism
- [√] Text-to-image search
- [√] Image-to-image search
- [√] System configuration management
- [√] API interface development
- [ ] Album management UI optimization
- [ ] Image category classification
- [ ] Batch import & export functions

## License
MIT License

## Contact
- Project Repository: https://github.com/l1005268416/TuYiCang
- Issue Tracker: https://github.com/l1005268416/TuYiCang/issues

## Acknowledgements
Thanks to the following open-source projects:
- Ollama
- vLLM
- Milvus
- Vue.js
- Element Plus