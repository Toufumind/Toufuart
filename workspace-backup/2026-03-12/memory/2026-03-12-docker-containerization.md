# Docker容器化技术学习笔记 - 2026-03-12

## 1. Docker概述

### 什么是Docker？
Docker是一个开源的应用容器引擎，允许开发者将应用及其依赖打包到一个可移植的容器中，然后发布到任何流行的Linux或Windows机器上。

### 核心概念
1. **镜像 (Image)**：只读模板，包含运行应用所需的代码、运行时、库、环境变量和配置文件
2. **容器 (Container)**：镜像的运行实例，包含运行时需要的所有内容
3. **仓库 (Registry)**：存储镜像的地方，如Docker Hub
4. **Dockerfile**：用于构建镜像的文本文件

### Docker vs 虚拟机的区别
| 特性 | Docker容器 | 虚拟机 |
|------|------------|--------|
| 启动时间 | 秒级 | 分钟级 |
| 性能 | 接近原生 | 有损耗 |
| 内存占用 | 小 | 大 |
| 隔离性 | 进程级 | 系统级 |
| 镜像大小 | MB级 | GB级 |
| 部署速度 | 快 | 慢 |

## 2. Docker安装与配置

### Ubuntu 24.04安装Docker
```bash
# 1. 卸载旧版本
sudo apt-get remove docker docker-engine docker.io containerd runc

# 2. 安装依赖
sudo apt-get update
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 3. 添加Docker官方GPG密钥
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 4. 设置仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. 安装Docker引擎
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 6. 验证安装
sudo docker run hello-world

# 7. 将用户添加到docker组（避免每次使用sudo）
sudo usermod -aG docker $USER
# 需要重新登录生效
```

### Docker Compose安装
```bash
# 安装Docker Compose
sudo apt-get install -y docker-compose-plugin

# 验证
docker compose version
```

## 3. Dockerfile编写

### 基础Dockerfile结构
```dockerfile
# 基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 运行命令
CMD ["python", "app.py"]
```

### 优化Dockerfile的最佳实践
```dockerfile
# 1. 使用特定版本的基础镜像
FROM python:3.12-slim-bullseye

# 2. 设置非root用户（安全）
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser

# 3. 使用多阶段构建减少镜像大小
# 第一阶段：构建依赖
FROM python:3.12-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# 第二阶段：运行环境
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "app.py"]

# 4. 合理使用.dockerignore
# .dockerignore文件内容：
.git
__pycache__
*.pyc
*.pyo
*.pyd
.Python
.env
.venv
*.log
*.sqlite3
```

## 4. 针对TechArt资源收集器的Docker配置

### 基础Dockerfile
```dockerfile
# Dockerfile.techart
FROM python:3.12-slim

# 元数据
LABEL maintainer="TechArt Team <techart@example.com>"
LABEL version="1.0.0"
LABEL description="TechArt资源收集器容器"

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Shanghai

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY collector.py .
COPY async_validator.py .
COPY skills/ ./skills/

# 创建数据目录
RUN mkdir -p /data

# 设置数据卷
VOLUME /data

# 设置健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# 运行收集器
CMD ["python", "collector.py"]
```

### requirements.txt
```txt
# TechArt资源收集器依赖
aiohttp>=3.9.0
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0

# 开发依赖
pytest>=7.0.0
pytest-asyncio>=0.21.0
black>=23.0.0
flake8>=6.0.0

# 工具
python-dotenv>=1.0.0
```

### .dockerignore文件
```gitignore
# 忽略文件
.git
.gitignore
.dockerignore
.vscode
.idea
__pycache__
*.pyc
*.pyo
*.pyd
.Python
.env
.venv
.env.local
.env.development.local
.env.test.local
.env.production.local
npm-debug.log*
yarn-debug.log*
yarn-error.log*
node_modules
dist
build
*.log
*.sqlite3
*.db
.DS_Store
Thumbs.db
```

## 5. Docker Compose配置

### docker-compose.yml
```yaml
version: '3.8'

services:
  techart-collector:
    build:
      context: .
      dockerfile: Dockerfile.techart
    container_name: techart-collector
    restart: unless-stopped
    environment:
      - TZ=Asia/Shanghai
      - PYTHONUNBUFFERED=1
    volumes:
      - ./data:/data
      - ./logs:/app/logs
    networks:
      - techart-network
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # 可选：数据库服务
  postgres:
    image: postgres:15-alpine
    container_name: techart-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_USER=techart
      - POSTGRES_PASSWORD=techart_password
      - POSTGRES_DB=techart_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - techart-network
    ports:
      - "5432:5432"

  # 可选：Redis缓存
  redis:
    image: redis:7-alpine
    container_name: techart-redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - techart-network
    ports:
      - "6379:6379"

networks:
  techart-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
```

### 环境变量配置 (.env)
```env
# 应用配置
TECHART_ENV=production
TECHART_LOG_LEVEL=INFO
TECHART_DATA_DIR=/data

# 数据库配置
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=techart_db
POSTGRES_USER=techart
POSTGRES_PASSWORD=techart_password

# Redis配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# 收集器配置
COLLECTOR_BATCH_SIZE=10
COLLECTOR_INTERVAL_HOURS=24
COLLECTOR_MAX_RETRIES=3
```

## 6. 构建和运行

### 构建镜像
```bash
# 构建基础镜像
docker build -t techart-collector:latest -f Dockerfile.techart .

# 带标签构建
docker build -t techart-collector:1.0.0 -t techart-collector:latest -f Dockerfile.techart .

# 使用Docker Compose构建
docker-compose build
```

### 运行容器
```bash
# 运行单个容器
docker run -d \
  --name techart-collector \
  -v $(pwd)/data:/data \
  -v $(pwd)/logs:/app/logs \
  -e TZ=Asia/Shanghai \
  techart-collector:latest

# 使用Docker Compose运行
docker-compose up -d

# 查看日志
docker logs -f techart-collector

# 进入容器
docker exec -it techart-collector bash

# 停止容器
docker stop techart-collector
docker rm techart-collector

# 使用Docker Compose停止
docker-compose down
```

### 生产环境部署脚本
```bash
#!/bin/bash
# deploy_techart.sh

set -e

echo "=== TechArt资源收集器部署 ==="

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装"
    exit 1
fi

# 检查Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装"
    exit 1
fi

# 创建目录
mkdir -p data logs backups

# 复制配置文件
if [ ! -f .env ]; then
    echo "创建.env配置文件..."
    cp .env.example .env
    echo "请编辑.env文件配置环境变量"
fi

# 构建镜像
echo "构建Docker镜像..."
docker-compose build

# 启动服务
echo "启动服务..."
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo "检查服务状态..."
docker-compose ps

# 查看日志
echo "查看日志..."
docker-compose logs --tail=20 techart-collector

echo "=== 部署完成 ==="
echo "管理命令:"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo "  进入容器: docker-compose exec techart-collector bash"
```

## 7. 监控和维护

### 监控脚本
```bash
#!/bin/bash
# monitor_techart.sh

echo "=== TechArt收集器监控 ==="
echo "时间: $(date)"

# 检查容器状态
echo "容器状态:"
docker ps --filter "name=techart" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 检查资源使用
echo -e "\n资源使用:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | grep techart

# 检查日志错误
echo -e "\n最近错误:"
docker logs techart-collector --tail=50 2>&1 | grep -i error | tail -5

# 检查健康状态
echo -e "\n健康检查:"
docker inspect --format='{{.State.Health.Status}}' techart-collector

# 数据目录大小
echo -e "\n数据目录:"
du -sh data/ 2>/dev/null || echo "数据目录不存在"

echo "=== 监控完成 ==="
```

### 备份脚本
```bash
#!/bin/bash
# backup_techart.sh

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "备份TechArt数据..."

# 备份数据库
docker-compose exec -T postgres pg_dump -U techart techart_db > "$BACKUP_DIR/techart_db.sql"

# 备份数据文件
tar -czf "$BACKUP_DIR/data.tar.gz" data/

# 备份日志
tar -czf "$BACKUP_DIR/logs.tar.gz" logs/

# 备份配置
cp .env "$BACKUP_DIR/"
cp docker-compose.yml "$BACKUP_DIR/"
cp Dockerfile.techart "$BACKUP_DIR/"

echo "备份完成: $BACKUP_DIR"
echo "文件大小:"
du -sh "$BACKUP_DIR"/*
```

### 更新脚本
```bash
#!/bin/bash
# update_techart.sh

echo "更新TechArt收集器..."

# 拉取最新代码
git pull origin main

# 重建镜像
docker-compose build --no-cache

# 重启服务
docker-compose down
docker-compose up -d

# 等待启动
sleep 10

# 检查状态
docker-compose ps

echo "更新完成"
```

## 8. 多环境配置

### 开发环境配置 (docker-compose.dev.yml)
```yaml
version: '3.8'

services:
  techart-collector:
    build:
      context: .
      dockerfile: Dockerfile.techart
      target: development  # 多阶段构建的开发阶段
    container_name: techart-collector-dev
    restart: unless-stopped
    environment:
      - TECHART_ENV=development
      - TECHART_LOG_LEVEL=DEBUG
    volumes:
      - ./data:/data
      - ./logs:/app/logs
      - .:/app  # 挂载代码目录，支持热重载
    ports:
      - "8000:8000"
    command: python collector.py --debug
```

### 测试环境配置 (docker-compose.test.yml)
```yaml
version: '3.8'

services:
  techart-collector:
    build:
      context: .
      dockerfile: Dockerfile.techart
    container_name: techart-collector-test
    environment:
      - TECHART_ENV=test
      - TECHART_LOG_LEVEL=INFO
    volumes:
      - ./test_data:/data
    command: pytest tests/ -v
```

### 生产环境配置 (docker-compose.prod.yml)
```yaml
version: '3.8'

services:
  techart-collector:
    build:
      context: .
      dockerfile: Dockerfile.techart
      target: production  # 多阶段构建的生产阶段
    container_name: techart-collector-prod
    restart: always
    environment:
      - TECHART_ENV=production
      - TECHART_LOG_LEVEL=WARNING
    volumes:
      - /var/techart/data:/data
      - /var/techart/logs:/app/logs
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
      restart_policy:
        condition: on-failure
        max_attempts: 3
```

## 9. 安全最佳实践

### 安全Dockerfile
```dockerfile
# 使用非root用户
FROM python:3.12-slim

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser -s /bin/false appuser

WORKDIR /app

# 复制文件并设置权限
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

# 切换到非root用户
USER appuser

# 只暴露必要端口
EXPOSE 8000

CMD ["python", "collector.py"]
```

### 安全扫描
```bash
# 使用Trivy扫描镜像漏洞
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:latest \
  image techart-collector:latest

# 使用Hadolint检查Dockerfile
docker run --rm -i hadolint/hadolint < Dockerfile.techart
```

## 10. 应用到TechArt资源收集器

### 实施步骤
1. **创建Docker配置**：Dockerfile, docker-compose.yml, .dockerignore
2. **编写部署脚本**：构建、运行、监控、备份脚本
3. **设置多环境**：开发、测试、生产环境配置
4. **实施安全措施