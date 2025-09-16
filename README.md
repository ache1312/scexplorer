# scExplorer

**scExplorer** is a comprehensive, production-ready web application for single-cell RNA sequencing (scRNA-seq) data analysis. It combines state-of-the-art methods with an intuitive interface so researchers can derive biological insights without extensive computational expertise.

[![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)](https://github.com/networkbiolab/scexplorer)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://hub.docker.com/)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![R](https://img.shields.io/badge/R-4.0%2B-blue.svg)](https://r-project.org)

## 🚀 Live Demo

Try scExplorer online (no installation):  
https://apps.cienciavida.org/scexplorer/

OpenAPI / API docs:  
https://apps.cienciavida.org/backend/docs

---

## 📋 Table of Contents

1. [Features](#-features)  
2. [System Requirements](#-system-requirements)  
3. [Installation Guide](#-installation-guide)  
4. [Client–Server Architecture (HPC Integration)](#-client-server-architecture-hpc-integration)  
5. [API Usage](#-api-usage)  
6. [Upload Requirements](#-upload-requirements)  
7. [Large Datasets & Performance](#-large-datasets--performance)  
8. [Troubleshooting](#-troubleshooting)  
9. [Contributing](#-contributing)  
10. [License](#-license)

---

## 🌟 Features

### Core Analysis Pipeline
- **📤 Data Upload:** `.h5ad` (Scanpy), `.rds` (Seurat), `.h5` (10x HDF5), and 10x Cell Ranger (`matrix.mtx`, `features.tsv.gz`, `barcodes.tsv.gz`)
- **🧹 Quality Control:** Cell/gene filtering, mitochondrial content filters, doublet detection (Scrublet)
- **📊 Dimensionality Reduction:** PCA with highly variable gene selection; UMAP for visualization
- **🎯 Clustering:** Leiden clustering with resolution tuning; Clustree to explore cluster stability
- **🔬 Differential Expression:** Wilcoxon and t-test alternatives; export full results
- **📌 Heatmaps:** Gene- and cell-level heatmaps with optional z-score and hierarchical clustering
- **🔗 Batch Integration:** Harmony, Scanorama, ComBat, BBKNN
- **🎨 Visualization:** Interactive plots with overlays; configurable color palettes, fonts, axes, legends; export SVG/PNG

### Advanced Features (v1.2+)

- **🧩 Multi-Dataset Support:** Integrate up to **five** datasets per run via the web UI
- **⚡ HPC Support:** SLURM integration for scalable computing; job queueing and email notifications
- **📁 Reproducibility:** Automated PDF reports; exportable configuration files; UUID-based provenance
- **🌐 Stable REST API:** Documented endpoints for programmatic use and interoperability
- **🖼️ Smart Plot Rendering:** **Automatic rasterization** for large plots (>~100k–200k cells) to preserve interactivity
- **🏷️ Cluster Annotation:** Leiden-based labels propagate to downstream plots and exports

### Platform Flexibility
- **🐳 Containerized:** Docker-based deployment for reproducibility
- **☁️ Flexible:** Standalone or **client–server** (frontend local, backend on HPC)
- **🖥️ Cross-Platform:** Linux, macOS, and Windows
- **📱 Responsive UI:** Works well on modern browsers


---

## 🖥️ System Requirements

**Minimum:**
- RAM: 8 GB (16 GB recommended for >20k cells)
- Storage: 10 GB free space
- CPU: 4 cores (8+ recommended)
- OS: Ubuntu 20.04+/macOS 10.15+/Windows 10+

**HPC/Production:**
- RAM: 128+ GB
- Storage: SSD, 100+ GB free
- Network: Outbound email for notifications (optional)

**Software:**
- Docker 20.10+ and Docker Compose 2.0+
- Modern browser (Chrome 90+, Firefox 88+, Safari 14+)

---

## 📖  Installation Guide

### 1) Install Docker / Compose

Ubuntu/Debian:
```bash
sudo apt update
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo usermod -aG docker $USER && newgrp docker

````

macOS:

```bash
brew install --cask docker
```

Windows:

* Install Docker Desktop and enable WSL2.

### 2) Clone & Configure

```bash
git clone https://github.com/networkbiolab/scexplorer.git
cd scexplorer
mkdir -p uploads logs
cp .env.example .env 2>/dev/null || true
# edit .env as needed
```

### 3) Launch

```bash
docker-compose up -d
docker-compose ps
docker-compose logs -f
```

### 4) Verify

```bash
curl -I http://localhost/scexplorer
curl http://localhost/backend/
```

---

## ⚙️ Simple Local vs HCP Setups

You can run scExplorer in two convenient modes without changing code:

- **All-Local (no Slurm, optional email off)**  
  - Backend: set `EXECUTION_MODE=local` and optionally `ENABLE_EMAIL=false`.  
  - Frontend: set `BACKEND_URL=http://localhost:8000/backend`.  
  - Behavior: backend runs jobs inline (no SLURM required); UI works at `http://localhost:3000`.  

- **Frontend + Remote HCP Backend (current production)**  
  - Frontend only: set `BACKEND_URL=https://apps.cienciavida.org/backend`.  
  - Behavior: frontend calls the HCP server; no local Python/Slurm needed.  

Environment examples are provided in `backend/.env.example` and `frontend/.env.example`.

**Notes:**  
- In local mode the backend writes the same `.out/.err` files as SLURM and all existing endpoints continue to work.  
- Email sending is skipped when `ENABLE_EMAIL=false` or `SENDGRID_API_KEY` is not provided.  



---

## 🔌 API Usage

* Explore the live OpenAPI docs: `https://apps.cienciavida.org/backend/docs`
* The **stable** REST API coordinates: upload → QC → integration → embedding → clustering → DEA → visualization → report.



---

## ⬆️ Upload Requirements

The upload panel in the web UI lists accepted formats and the configured maximum file size.

| Format       | Description     | Typical Limit\* | Notes                        |
| ------------ | --------------- | --------------- | ---------------------------- |
| `.h5ad`      | AnnData/Scanpy  | 2 GB            | Recommended for Python users |
| `.rds`       | Seurat objects  | 2 GB            | Recommended for R users      |
| `.h5`        | 10x HDF5        | 2 GB            | Single-file 10x format       |
| `mtx/tsv.gz` | 10x Cell Ranger | 2 GB total      | Matrix + features + barcodes |

\* The default limit can be changed by the administrator; the UI displays the active limit next to the upload control and in tooltips.

---

## 📈 Large Datasets & Performance

* For datasets above \~100k–200k cells, scExplorer **automatically rasterizes** plots to preserve interactivity.
* Export remains available (SVG/PNG), and styling options (colors, font families/sizes, axes, legend placement) apply regardless of rendering mode.

---

## 🔧 Troubleshooting

**Docker permissions**

```bash
sudo usermod -aG docker $USER && newgrp docker
```

**Port conflicts**

```bash
docker-compose down
sudo lsof -i :80
sudo kill -9 <PID>
```

**File permissions**

```bash
sudo chown -R $(whoami):$(whoami) uploads/ logs/
chmod 755 uploads/
```

**Memory issues**

```bash
free -h
# On Docker Desktop: increase memory to 8GB+
```

**Health checks**

```bash
docker-compose logs backend
docker-compose logs frontend
```

---

## 👥 Contributing

We welcome community contributions via issues and pull requests.

### Development Setup

```bash
# Fork & clone
git clone https://github.com/YOUR-USERNAME/scexplorer.git
cd scexplorer
git remote add upstream https://github.com/networkbiolab/scexplorer.git
```

Backend:

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```



### Roadmap (high-level)

* Trajectory inference
* RNA velocity
* GRN/SCENIC
* Enhanced large-scale visualization

---

## 📜 License

MIT — see [LICENSE](LICENSE) for details.



