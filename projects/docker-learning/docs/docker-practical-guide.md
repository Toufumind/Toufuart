# Docker实践指南 - 从安装到生产部署

## 一、Docker安装问题解决

### 1.1 网络问题解决方案

#### 问题：curl连接被重置
```bash
# 错误信息
curl: (35) Recv failure: Connection reset by peer

# 解决方案1：使用国内镜像
export DOCKER_MIRROR="https://mirrors.aliyun.com/docker-ce"
curl -fsSL ${DOCKER_MIRROR}/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 解决方案2：使用代理
export https_proxy=http://127.0.0.1:7890
export http_proxy=http://127.0.0.1:7890

# 解决方案3：手动下载
wget -O docker.gpg https://download.docker.com/linux/ubuntu/gpg
sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg < docker.gpg
```

#### 问题：Ubuntu 24.04 Docker仓库问题
```bash
# 检查Ubuntu版本代号
lsb_release -cs  # 输出: noble

# 正确的Docker仓库配置
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu noble stable" | sudo tee /etc/apt/sources.list.d/docker.list
```

### 1.2 完整安装脚本（带错误处理）
```bash
#!/bin/bash
# docker-install-with-retry.sh

set -e  # 遇到错误立即退出

echo "=== Docker安装脚本（带重试机制）==="

# 函数：重试命令
retry_command() {
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "尝试 $attempt/$max_attempts: $1"
        
        if eval "$1"; then
            echo "成功"
            return 0
        else
            echo "失败，等待重试..."
            sleep $((attempt * 2))
            ((attempt++))
        fi
    done
    
    echo "所有尝试都失败"
    return 1
}

# 1. 更新包列表
retry_command "sudo apt-get update"

# 2. 安装依赖
retry_command "sudo apt-get install -y ca-certificates curl gnupg lsb-release"

# 3. 添加Docker GPG密钥（多源重试）
DOCKER_GPG_SOURCES=(
    "https://download.docker.com/linux/ubuntu/gpg"
    "https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg"
    "https://mirrors.tuna.tsinghua.edu.cn/docker-ce/linux/ubuntu/gpg"
)

for source in "${DOCKER_GPG_SOURCES[@]}"; do
    echo "尝试从 $source 下载GPG密钥..."
    if curl -fsSL "$source" | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg 2>/dev/null; then
        echo "GPG密钥下载成功"
        break
    fi
done

# 4. 设置存储库
sudo mkdir -p /etc/apt/keyrings
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. 再次更新并安装
retry_command "sudo apt-get update"
retry_command "sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin"

# 6. 启动服务
sudo systemctl start docker
sudo systemctl enable docker

# 7. 验证安装
docker --version
docker-compose --version

echo "=== Docker安装完成 ==="
```

## 二、Docker基础实践

### 2.1 第一个容器实践
```bash
# 1. 运行Hello World容器
docker run --rm hello-world

# 2. 运行交互式容器
docker run -it --rm ubuntu:24.04 bash

# 3. 运行后台容器
docker run -d --name my-nginx -p 8080:80 nginx

# 4. 查看容器状态
docker ps
docker logs my-nginx
docker stats my-nginx

# 5. 停止和清理
docker stop my-nginx
docker rm my-nginx
```

### 2.2 镜像管理实践
```bash
# 1. 搜索镜像
docker search ubuntu

# 2. 拉取镜像
docker pull ubuntu:24.04
docker pull python:3.11-slim

# 3. 查看镜像
docker images
docker image ls

# 4. 删除镜像
docker rmi ubuntu:24.04

# 5. 导出和导入镜像
docker save -o ubuntu.tar ubuntu:24.04
docker load -i ubuntu.tar
```

### 2.3 容器网络实践
```bash
# 1. 查看网络
docker network ls

# 2. 创建自定义网络
docker network create my-network

# 3. 运行容器到自定义网络
docker run -d --name web --network my-network nginx
docker run -d --name app --network my-network python:3.11

# 4. 容器间通信测试
docker exec app ping web

# 5. 端口映射
docker run -d --name nginx-public -p 80:80 -p 443:443 nginx
```

## 三、Dockerfile编写实践

### 3.1 基础Dockerfile示例
```dockerfile
# 多阶段构建示例
# 阶段1: 构建阶段
FROM python:3.11-slim AS builder

WORKDIR /app

# 复制依赖文件
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 阶段2: 运行阶段
FROM python:3.11-slim AS runtime

WORKDIR /app

# 从构建阶段复制已安装的包
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app

# 设置环境变量
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

# 创建非root用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "app.py"]
```

### 3.2 优化技巧
```dockerfile
# 1. 使用.dockerignore减少构建上下文
# .dockerignore文件内容
.git
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
venv
.env
.DS_Store
.dockerignore
Dockerfile
README.md

# 2. 层优化 - 将不常变化的层放在前面
# 错误示例（每次代码变更都重新安装依赖）
COPY . .
RUN pip install -r requirements.txt

# 正确示例（依赖层缓存）
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# 3. 多阶段构建减少镜像大小
FROM node:18 AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 四、Docker Compose实践

### 4.1 基础docker-compose.yml
```yaml
version: '3.8'

services:
  # Web服务
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/mydb
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./app:/app
    networks:
      - app-network
    restart: unless-stopped

  # 数据库服务
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: mydb
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - app-network
    restart: unless-stopped

  # Redis缓存
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    networks:
      - app-network
    restart: unless-stopped

  # 监控服务
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    networks:
      - app-network
    restart: unless-stopped

  # 日志收集
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - app-network
    restart: unless-stopped

# 网络定义
networks:
  app-network:
    driver: bridge

# 卷定义
volumes:
  postgres-data:
  redis-data:
  prometheus-data:
```

### 4.2 生产环境配置
```yaml
version: '3.8'

x-logging: &default-logging
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"

x-deploy: &default-deploy
  replicas: 2
  update_config:
    parallelism: 1
    delay: 10s
    order: start-first
  restart_policy:
    condition: on-failure
    delay: 5s
    max_attempts: 3
    window: 120s
  resources:
    limits:
      cpus: '0.5'
      memory: 512M
    reservations:
      cpus: '0.25'
      memory: 256M

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.prod
      args:
        - NODE_ENV=production
    image: myapp:${TAG:-latest}
    ports:
      - "${PORT:-3000}:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    secrets:
      - db_password
    configs:
      - source: app_config
        target: /app/config/production.json
    deploy:
      <<: *default-deploy
      placement:
        constraints:
          - node.role == worker
    logging: *default-logging
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

secrets:
  db_password:
    external: true

configs:
  app_config:
    external: true
```

## 五、监控和日志

### 5.1 容器监控
```bash
# 1. 实时监控
docker stats

# 2. 查看容器资源使用
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"

# 3. 检查容器详细信息
docker inspect <container_id>

# 4. 查看容器进程
docker top <container_id>

# 5. 性能分析
docker run -it --rm --pid=container:<container_id> alpine sh -c "apk add procps && top"
```

### 5.2 日志管理
```bash
# 1. 查看日志
docker logs <container_id>

# 2. 实时查看日志
docker logs -f <container_id>

# 3. 查看特定时间段的日志
docker logs --since 1h <container_id>

# 4. 查看最后N行日志
docker logs --tail 100 <container_id>

# 5. 导出日志到文件
docker logs <container_id> > container.log 2>&1

# 6. 使用日志驱动
docker run --log-driver=json-file --log-opt max-size=10m --log-opt max-file=3 nginx
```

## 六、安全最佳实践

### 6.1 安全配置
```bash
# 1. 非root用户运行
docker run --user 1000:1000 nginx

# 2. 只读根文件系统
docker run --read-only nginx

# 3. 能力限制
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE nginx

# 4. 安全选项
docker run --security-opt=no-new-privileges nginx
docker run --security-opt=apparmor:docker-default nginx

# 5. 资源限制
docker run --memory=512m --cpus=1.0 nginx
docker run --pids-limit=100 nginx
```

### 6.2 镜像安全扫描
```bash
# 1. 使用Trivy扫描镜像
docker run --rm aquasec/trivy image nginx:latest

# 2. 使用Docker Scout
docker scout quickview nginx:latest

# 3. 检查镜像层
docker history nginx:latest

# 4. 验证镜像签名
docker trust inspect nginx:latest
```

## 七、故障排除

### 7.1 常见问题解决
```bash
# 问题1: 容器启动失败
docker logs <container_id>  # 查看错误日志
docker inspect <container_id>  # 检查配置

# 问题2: 端口冲突
netstat -tulpn | grep :80  # 检查端口占用
docker ps  # 查看运行中的容器

# 问题3: 磁盘空间不足
docker system df  # 查看Docker磁盘使用
docker system prune  # 清理未使用的资源

# 问题4: 网络连接问题
docker network inspect bridge  # 检查网络配置
iptables -L  # 检查防火墙规则

# 问题5: 性能问题
docker stats  # 监控资源使用
docker exec <container_id> top  # 查看容器内进程
```

### 7.2 调试技巧
```bash
# 1. 进入运行中的容器
docker exec -it <container_id> bash

# 2. 检查容器网络
docker exec <container_id> ip addr
docker exec <container_id> ping google.com

# 3. 检查容器文件系统
docker exec <container_id> ls -la /
docker exec <container_id> df -h

# 4. 检查环境变量
docker exec <container_id> env

# 5. 临时调试容器
docker run --rm -it --entrypoint=bash nginx:latest
```

## 八、生产部署检查清单

### 8.1 部署前检查
- [ ] 镜像已扫描安全漏洞
- [ ] 使用非root用户运行
- [ ] 配置资源限制（CPU、内存）
- [ ] 设置健康检查
- [ ] 配置日志轮转
- [ ] 使用只读根文件系统（如适用）
- [ ] 限制容器能力
- [ ] 配置网络策略
- [ ] 设置重启策略
- [ ] 配置监控和告警

### 8.2 运行时监控
- [ ] 容器资源使用监控
- [ ] 应用性能监控
- [ ] 日志收集和分析
- [ ] 安全事件监控
- [ ] 备份和恢复测试

## 总结

Docker实践需要：
1. **理解原理**：知道Docker如何工作
2. **掌握工具**：熟练使用Docker命令和Compose
3. **遵循最佳实践**：安全、性能、可维护性
4. **持续学习**：跟踪Docker生态发展

通过实践逐步掌握，从简单容器到复杂编排，从开发环境到生产部署。