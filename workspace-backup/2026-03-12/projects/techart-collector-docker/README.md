# TechArt资源收集器 - Docker化部署

## 项目概述
将TechArt资源收集器容器化，实现标准化部署和自动化运行。

## 架构设计

### 组件
1. **收集器容器**: Python应用，执行资源收集和验证
2. **调度器容器**: Cron服务，定时触发收集任务
3. **数据卷**: 持久化存储收集的资源
4. **日志卷**: 存储运行日志

### 网络拓扑
```
+-------------------+     +---------------------+
|  调度器容器        |     |  收集器容器         |
|  (Cron Scheduler) |---->|  (Python Collector) |
+-------------------+     +---------------------+
         |                          |
         v                          v
+-------------------+     +---------------------+
|  日志卷           |     |  数据卷             |
|  (Logs Volume)    |     |  (Data Volume)      |
+-------------------+     +---------------------+
```

## 文件结构
```
techart-collector-docker/
├── docker-compose.yml          # Docker Compose配置
├── Dockerfile.collector        # 收集器Dockerfile
├── Dockerfile.scheduler        # 调度器Dockerfile
├── config/
│   ├── collector-config.json   # 收集器配置
│   └── cron-tab                # Cron调度配置
├── scripts/
│   ├── entrypoint.sh           # 收集器入口脚本
│   └── healthcheck.sh          # 健康检查脚本
├── data/                       # 数据卷挂载点
│   └── resources/              # 收集的资源
└── logs/                       # 日志卷挂载点
    ├── collector.log
    └── scheduler.log
```

## 配置详情

### 1. Docker Compose配置
```yaml
version: '3.8'

services:
  techart-collector:
    build:
      context: .
      dockerfile: Dockerfile.collector
    image: techart-collector:latest
    container_name: techart-collector
    restart: unless-stopped
    environment:
      - TZ=Asia/Shanghai
      - LOG_LEVEL=INFO
      - COLLECTOR_CONFIG=/app/config/collector-config.json
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config:ro
    networks:
      - techart-network
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 5m
      timeout: 30s
      retries: 3
      start_period: 1m
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M

  cron-scheduler:
    build:
      context: .
      dockerfile: Dockerfile.scheduler
    image: techart-scheduler:latest
    container_name: techart-scheduler
    restart: unless-stopped
    volumes:
      - ./config/cron-tab:/etc/crontabs/root:ro
      - ./data:/app/data:ro
      - ./logs:/app/logs
    depends_on:
      - techart-collector
    networks:
      - techart-network

networks:
  techart-network:
    driver: bridge

volumes:
  techart-data:
  techart-logs:
```

### 2. 收集器Dockerfile
```dockerfile
# Dockerfile.collector
FROM python:3.9-alpine AS builder

# 安装构建依赖
RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev curl

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# 运行阶段
FROM python:3.9-alpine
LABEL maintainer="TechArt Team"
LABEL version="2.0"
LABEL description="TechArt资源收集器"

# 安装运行时依赖
RUN apk add --no-cache curl git tzdata \
    && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone \
    && apk del tzdata

WORKDIR /app

# 从构建阶段复制Python包
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app:$PYTHONPATH

# 复制应用代码
COPY collector.py .
COPY async_validator.py .
COPY scripts/entrypoint.sh .
COPY scripts/healthcheck.sh .

# 创建非root用户
RUN addgroup -g 1000 appgroup \
    && adduser -u 1000 -G appgroup -s /bin/sh -D appuser \
    && chown -R appuser:appgroup /app \
    && chmod +x scripts/*.sh

USER appuser

# 健康检查
HEALTHCHECK --interval=5m --timeout=30s --start-period=1m --retries=3 \
  CMD ./scripts/healthcheck.sh

# 入口点
ENTRYPOINT ["./scripts/entrypoint.sh"]
CMD ["collect"]

# 构建指令
# docker build -t techart-collector:latest -f Dockerfile.collector .
```

### 3. 调度器Dockerfile
```dockerfile
# Dockerfile.scheduler
FROM alpine:latest

# 安装cron和必要工具
RUN apk add --no-cache dcron curl tzdata \
    && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone \
    && apk del tzdata

# 创建cron用户
RUN adduser -D -u 1000 cronuser

USER cronuser

# 复制cron配置
COPY config/cron-tab /etc/crontabs/cronuser

# 启动cron
CMD ["crond", "-f", "-l", "8"]
```

### 4. 收集器配置
```json
{
  "collector_config": {
    "daily_target": 10,
    "search_engines": ["zhihu", "github", "medium", "official_docs"],
    "validation": {
      "min_content_length": 500,
      "require_tech_keywords": 2,
      "check_http_status": true,
      "timeout_seconds": 10
    },
    "output": {
      "format": "markdown",
      "include_summary": true,
      "include_validation": true,
      "auto_git_commit": true
    },
    "schedule": {
      "enabled": true,
      "cron_expression": "0 2 * * *",  # 每天凌晨2点
      "timezone": "Asia/Shanghai"
    }
  }
}
```

### 5. Cron调度配置
```
# cron-tab
# 每天凌晨2点运行收集器
0 2 * * * curl -X POST http://techart-collector:8080/collect > /dev/null 2>&1

# 每小时检查健康状态
0 * * * * curl -f http://techart-collector:8080/health > /dev/null 2>&1 || echo "Health check failed"

# 每天凌晨3点清理旧日志
0 3 * * * find /app/logs -name "*.log" -mtime +7 -delete
```

### 6. 入口脚本
```bash
#!/bin/bash
# scripts/entrypoint.sh

set -e

echo "=== TechArt资源收集器启动 ==="
echo "时间: $(date)"
echo "工作目录: $(pwd)"
echo "用户: $(whoami)"
echo ""

# 检查配置
if [ -f "$COLLECTOR_CONFIG" ]; then
    echo "使用配置: $COLLECTOR_CONFIG"
else
    echo "警告: 配置文件未找到，使用默认配置"
fi

# 执行命令
case "$1" in
    collect)
        echo "开始资源收集..."
        python collector.py --config "$COLLECTOR_CONFIG"
        ;;
    validate)
        echo "开始资源验证..."
        python async_validator.py --config "$COLLECTOR_CONFIG"
        ;;
    health)
        echo "健康检查..."
        python -c "import sys; sys.exit(0)"
        ;;
    *)
        echo "用法: $0 {collect|validate|health}"
        exit 1
        ;;
esac

echo "=== 执行完成 ==="
```

### 7. 健康检查脚本
```bash
#!/bin/bash
# scripts/healthcheck.sh

# 检查Python环境
python -c "import sys; print('Python版本:', sys.version)" || exit 1

# 检查必要模块
python -c "import requests, json, re" || exit 1

# 检查配置文件
if [ -f "/app/config/collector-config.json" ]; then
    python -c "import json; json.load(open('/app/config/collector-config.json'))" || exit 1
fi

# 检查数据目录可写
touch /app/data/test.txt && rm /app/data/test.txt || exit 1

echo "健康检查通过"
exit 0
```

## 部署步骤

### 1. 环境准备
```bash
# 克隆项目
git clone <repository-url>
cd techart-collector-docker

# 创建目录结构
mkdir -p data logs config scripts

# 复制配置文件
cp ../techart-resource-collector/collector.py .
cp ../techart-resource-collector/async_validator.py .
cp ../techart-resource-collector/requirements.txt .
```

### 2. 构建镜像
```bash
# 构建收集器镜像
docker build -t techart-collector:latest -f Dockerfile.collector .

# 构建调度器镜像
docker build -t techart-scheduler:latest -f Dockerfile.scheduler .

# 查看镜像
docker images | grep techart
```

### 3. 运行服务
```bash
# 使用docker-compose启动
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f techart-collector
```

### 4. 测试功能
```bash
# 手动触发收集
docker-compose exec techart-collector ./scripts/entrypoint.sh collect

# 检查健康状态
docker-compose exec techart-collector ./scripts/entrypoint.sh health

# 查看收集的资源
ls -la data/resources/
```

### 5. 监控和维护
```bash
# 查看容器资源使用
docker stats techart-collector techart-scheduler

# 查看服务日志
docker-compose logs --tail=100

# 重启服务
docker-compose restart

# 更新服务
docker-compose pull
docker-compose up -d --force-recreate
```

## 监控和告警

### 1. 日志监控
```bash
# 实时查看日志
docker-compose logs -f --tail=50

# 导出日志
docker-compose logs --no-color > techart-logs-$(date +%Y%m%d).txt

# 错误日志分析
grep -i "error\|failed\|exception" logs/collector.log
```

### 2. 性能监控
```bash
# CPU和内存使用
docker stats --no-stream techart-collector

# 容器内进程
docker-compose exec techart-collector ps aux

# 磁盘使用
docker system df
```

### 3. 健康检查
```bash
# 手动健康检查
curl -f http://localhost:8080/health

# 查看健康状态
docker inspect --format='{{.State.Health.Status}}' techart-collector
```

## 备份和恢复

### 1. 数据备份
```bash
# 备份数据卷
docker run --rm -v techart-data:/data -v $(pwd):/backup alpine \
    tar czf /backup/techart-data-$(date +%Y%m%d).tar.gz -C /data .

# 备份配置
tar czf techart-config-$(date +%Y%m%d).tar.gz config/
```

### 2. 数据恢复
```bash
# 恢复数据卷
docker run --rm -v techart-data:/data -v $(pwd):/backup alpine \
    tar xzf /backup/techart-data-20260312.tar.gz -C /data

# 恢复配置
tar xzf techart-config-20260312.tar.gz
```

## 故障排除

### 常见问题
1. **容器启动失败**
   ```bash
   # 查看详细错误
   docker-compose logs --tail=50
   
   # 检查端口冲突
   netstat -tulpn | grep :8080
   ```

2. **收集器无输出**
   ```bash
   # 检查网络连接
   docker-compose exec techart-collector curl -I https://zhihu.com
   
   # 检查配置文件
   docker-compose exec techart-collector cat /app/config/collector-config.json
   ```

3. **磁盘空间不足**
   ```bash
   # 清理旧日志
   find logs -name "*.log" -mtime +7 -delete
   
   # 清理Docker缓存
   docker system prune -f
   ```

### 调试模式
```bash
# 进入容器调试
docker-compose exec techart-collector /bin/sh

# 手动运行收集器
docker-compose exec techart-collector python collector.py --debug

# 查看环境变量
docker-compose exec techart-collector env
```

## 扩展和优化

### 1. 水平扩展
```yaml
# docker-compose.scale.yml
services:
  techart-collector:
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      update_config:
        parallelism: 1
        delay: 10s
```

### 2. 负载均衡
```yaml
# 添加负载均衡器
services:
  nginx-proxy:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - techart-collector
```

### 3. 监控集成
```yaml
# 添加监控服务
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## 安全最佳实践

### 1. 镜像安全
```bash
# 扫描镜像漏洞
docker scan techart-collector:latest

# 使用签名镜像
docker trust sign techart-collector:latest
```

### 2. 网络安全
```yaml
# 限制网络访问
services:
  techart-collector:
    networks:
      techart-network:
        aliases:
          - collector
    # 仅允许调度器访问
    expose:
      - "8080"
```

### 3. 数据安全
```bash
# 加密数据卷
docker volume create --driver local \
    --opt type=encrypted \
    --opt device=tmpfs \
    techart-data-encrypted
```

## 总结

通过Docker化部署，TechArt资源收集器实现了：
1. **标准化部署**: 一致的运行环境
2. **自动化运维**: 定时任务和健康检查
3. **可扩展架构**: 支持水平扩展
4. **监控告警**: 完整的监控体系
5. **安全加固**: 遵循安全最佳实践

这套方案可以轻松部署到任何支持Docker的环境，包括本地开发机、云服务器和Kubernetes集群。

---
*项目创建时间: 2026-03-12*
*版本: 1.0*
*状态: 设计完成，待实现*