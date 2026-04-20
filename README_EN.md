# TuYiCang
[简体中文](README.md) | [English](README_EN.md)

A private local photo album knowledge base. Based on multimodal AI and unified multimodal space embedding technology, it implements two core functions: **text-to-image search** and **image-to-image search**.

<div align="center">
  <img src="images/1.png" alt="Project Screenshot" width="30%" height="170px">
  <img src="images/2.png" alt="Project Screenshot" width="30%" height="170px">
  <img src="images/4.png" alt="Project Screenshot" width="30%" height="170px">
</div>

## Project Introduction
TuYiCang is a lightweight local photo album retrieval system that enables intelligent image management via multimodal AI technology.
Adopting private local deployment, all models, data and images are stored on local devices with no external network requests, fully protecting user privacy.

### Core Features
- **Dual-Mode Retrieval**: Supports text-to-image search and image-to-image search
- **Intelligent Import**: Automatic scanning, preprocessing, deduplication and EXIF information extraction
- **Incremental Update**: Real-time monitoring of local album directories, with automatic synchronization of newly added, modified and deleted images
- **Tag Management**: AI-generated image tags, with support for manual editing and filtering
- **Private Deployment**: All data stored locally, offline usable, privacy-oriented
- **Lightweight Design**: Quantized models with low video memory usage, suitable for personal computer deployment

## Tech Stack
### Backend
- Programming Language: Python 3.9.10
- Multimodal Large Language Model (VLM): qwen3.5-0.8b (deployed via Ollama)
- Text Embedding Model: qwen3-embedding:0.6b (deployed via Ollama)
- Vision Embedding Model: Qwen3-VL-Embedding-2B (deployed via vLLM)
- Vector Database: Milvus v2.4.8
- Metadata Database: SQLite 3.41.2

### Frontend
- Framework: Vue 3 + Element Plus
- Runtime Environment: Node.js 16.18.0
- Architecture: Frontend-backend separation

### Auxiliary Tools
- Pillow 9.5.0 (image processing)
- exifread 2.3.2 (EXIF parsing)
- watchdog 2.3.1 (folder monitoring)
- PyYAML 6.0 (configuration parsing)
- requests 2.31.0 (API calling)

## System Architecture
The system adopts an 8-layer decoupled architecture:
1. **Storage Layer**: Local disk storage (original images, preprocessed images, thumbnails, vector database, general database)
2. **Database Layer**: SQLite database (metadata tables, system configuration tables)
3. **Preprocessing Layer**: File scanning, format adaptation, EXIF parsing, MD5 deduplication, image resizing
4. **Model Inference Layer**: Calls of VLM, text embedding and vision embedding models
5. **Vector Index Layer**: Milvus vector database, supporting text semantic indexing and visual similarity indexing
6. **Business Logic Layer**: Retrieval engine, incremental monitoring, deduplication logic, result post-processing
7. **Configuration Management Layer**: Configuration loading, validation, updating, backup and resetting
8. **User Interaction Layer**: Frontend pages (homepage, text-to-image search, image-to-image search, album management, configuration management)

## Quick Start
### Environment Requirements
- Python 3.9.10 or above
- Node.js 16.18.0 or above
- GPU: 16GB video memory is sufficient if long-context inference is not required
- At least 8GB RAM
- At least 10GB available disk space

### Installation Steps
#### 1. Clone the project
```bash
git clone https://github.com/l1005268416/TuYiCang.git
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

**Deploy vLLM (Vision Embedding Model)**
```bash
# Install vLLM
pip install vllm

# Start vision embedding model service
vllm serve Qwen3-VL-Embedding-2B \
--runner pooling \
--max-model-len 36000 \
--served-model-name Qwen3-VL-Embedding-2B \
--port 8022
```

#### 5. System Configuration
After the first launch, configure the system through the Web UI:
1. Visit http://localhost:8080
2. Enter the **Configuration Management** page
3. Set parameters including album path and model service addresses
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
1. Set the root album path in configurations
2. The system automatically scans images in the directory
3. Preprocessing is executed (deduplication, resizing, EXIF parsing)
4. Models are called to generate text descriptions, tags and vectors
5. Data is stored (metadata, vectors, thumbnails)

### Text-to-Image Search
1. Enter the **Text-to-Image** page
2. Input search keywords (e.g. "sunset by the sea", "cat")
3. The system converts keywords into text semantic vectors
4. Retrieve similar images from the vector database
5. Display results sorted by similarity

### Image-to-Image Search
1. Enter the **Image-to-Image** page
2. Upload a reference image
3. The system converts the image into visual vectors
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
│   │   ├── preprocessing/  # Preprocessing module
│   │   ├── inference/      # Model inference module
│   │   ├── vector/         # Vector index module
│   │   └── business/       # Business logic module
│   ├── database/           # Database module
│   ├── config/             # Configuration management module
│   ├── api/                # API interfaces
│   └── main.py             # Program entry
├── frontend/               # Frontend source code
│   ├── src/
│   │   ├── components/     # Components
│   │   ├── views/          # Pages
│   │   ├── api/            # API requests
│   │   └── utils/          # Utility functions
│   └── package.json
├── config/                 # Configuration files
│   └── config.yaml
├── data/                   # Data directory
│   ├── database/           # SQLite database
│   ├── vector/             # Vector database
│   └── cache/              # Cache files
│       └── thumb/          # Thumbnails
├── doc/                    # Documents
│   └── TuYiCangSDDD.md    # Detailed system design document
├── requirements.txt        # Python dependencies
└── README.md              # Project documentation
```

## Configuration Details
System configurations are managed via Web UI and stored in the SQLite database.

### Main Configuration Items
- **Album Settings**
  - `photo_root_path`: Root path of photo album
  - `valid_extensions`: Supported image formats (.jpg, .jpeg, .png, .webp, .bmp)
  - `min_file_size_kb`: Minimum file size (default: 50KB)
  - `max_file_size_mb`: Maximum file size (default: 50MB)

- **Model Service Settings**
  - `ollama_api_url`: Ollama API address (default: http://localhost:11434)
  - `vllm_api_url`: vLLM API address (default: http://localhost:8022)

- **Preprocessing Settings**
  - `target_max_edge`: Maximum edge length for image resizing (default: 1024 pixels)
  - `enable_vision_dedup`: Enable visual similarity deduplication (default: true)

- **Retrieval Settings**
  - `text_top_k`: Number of results returned by text-to-image search (default: 20)
  - `vision_top_k`: Number of results returned by image-to-image search (default: 20)
  - `vision_similarity_threshold`: Visual similarity threshold (default: 0.65)

- **System Settings**
  - `cache_dir`: Cache directory (default: ./data/cache)
  - `database_path`: Database path (default: ./data/database/tuycang.db)
  - `vector_store_path`: Vector database path (default: ./data/vector)

## Performance Metrics
- Support for **10,000+ images**
- Text-to-image search response time: **< 1 second**
- Image-to-image search response time: **< 1 second**
- Image import speed: Approximately 5–10 images per minute (depends on hardware)
- Video memory usage: Approximately 6–12GB
- Inference speed (on NVIDIA V100):
  - VLM inference: ~0.55s per request
  - Text embedding: ~0.26s per request
  - Vision embedding: ~0.20s per request

```plain
[2026-04-20 18:20:43] [INFO] [app.services.inference] VLM inference completed in 0.55s (attempt 1)
[2026-04-20 18:20:44] [INFO] [httpx] HTTP Request: POST http://192.168.1.149:11434/v1/embeddings "HTTP/1.1 200 OK"
[2026-04-20 18:20:44] [INFO] [app.services.inference] Text embedding inference completed in 0.26s (attempt 1)
[2026-04-20 18:20:44] [INFO] [httpx] HTTP Request: POST http://192.168.1.149:8022/v1/embeddings "HTTP/1.1 200 OK"
[2026-04-20 18:20:44] [INFO] [app.services.inference] Vision embedding inference completed in 0.20s (attempt 1)
```

## FAQ
### Q: How to solve slow model inference speed?
A: Try the following optimizations:
1. Use GPU acceleration
2. Adjust batch size
3. Switch to smaller model versions

### Q: How to back up data?
A: Regularly back up the following directories:
- `data/database/` (metadata database)
- `data/vector/` (vector database)
- `data/cache/` (thumbnail cache)

### Q: What image formats are supported?
A: .jpg, .jpeg, .png, .webp, .bmp are supported. Other formats will be automatically converted to JPG.

### Q: How to reset the system?
A:
1. Delete all files under `C:\Users\Username\AppData\Local\tuyicang`, and the system will reinitialize automatically.
2. Clear all data in Milvus.

### Q: Can other models be used?
A: Yes. Flexible model deployment is supported, and the system can be extended following the OpenAI API specification.

### Q: Why is video memory usage so high?
A: Qwen3-VL-Embedding-2B is the main consumer of video memory (around 13GB). Due to hardware limitations of the NVIDIA V100 GPU, quantized versions cannot be used properly. The attempted Qwen3-VL-Embedding-2B-GPTQ-Int4 model caused array overflow during image vectorization.
If your GPU supports Qwen3-VL-Embedding-2B-GPTQ-Int4, video memory usage will be greatly reduced.

### Q: Is Milvus mandatory for deployment?
A: No. Without Milvus, vectors will be stored in memory and lost after system restart. Milvus can also be deployed via Docker.

### Q: Why is Qwen3-VL-Embedding-2B also used for text embedding?
A: Qwen3-VL-Embedding-2B builds a **unified semantic space** that supports both text and vision modalities.
Text-to-image search performs better with this unified embedding model than the pipeline of VLM captioning + separate text embedding. Text descriptions generated by VLM are inherently lossy compression, and large amounts of fine-grained visual information that cannot be described in simple words will be lost.

<img src="images/3.png" alt="Qwen3-VL-Embedding-2B Text-to-Image Search Effect" width="45%" height="300px">

## Development Roadmap
- [√] Architecture construction
- [√] VLM model inference
- [√] Text embedding function
- [√] Image embedding function
- [√] Asynchronous inference & retry mechanism
- [√] Metadata management
- [√] Initial image loading
- [√] Incremental update
- [√] Text-to-image search
- [√] Image-to-image search
- [√] System configuration management
- [√] API development
- [ ] Album management interface optimization
- [ ] Image classification function
- [ ] Batch import & export support

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