# Docker安装和配置指南 - Ubuntu 24.04 LTS (WSL2)

## 系统环境
- **操作系统**: Ubuntu 24.04 LTS (noble)
- **内核版本**: 6.6.87.2-microsoft-standard-WSL2
- **架构**: x86_64
- **环境**: WSL2 (Windows Subsystem for Linux)

## 安装步骤

### 1. 卸载旧版本（如果存在）
```bash
sudo apt-get remove docker docker-engine docker.io containerd runc
```

### 2. 安装依赖包
```bash
sudo apt-get update
sudo apt-get install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release
```

### 3. 添加Docker官方GPG密钥
```bash
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
```

### 4. 设置存储库
```bash
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

### 5. 安装Docker引擎
```bash
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 6. 验证安装
```bash
sudo docker run hello-world
```

## WSL2特定配置

### 1. 启动Docker服务
```bash
# 启动Docker服务
sudo service docker start

# 设置开机自启
sudo systemctl enable docker
```

### 2. 非root用户运行Docker（可选）
```bash
# 创建docker组（如果不存在）
sudo groupadd docker

# 将当前用户添加到docker组
sudo usermod -aG docker $USER

# 应用组更改
newgrp docker

# 验证非root用户权限
docker run hello-world
```

### 3. WSL2与Windows Docker Desktop集成（如果已安装）
```bash
# 如果Windows已安装Docker Desktop，可以配置集成
echo "export DOCKER_HOST=tcp://localhost:2375" >> ~/.bashrc
source ~/.bashrc
```

## 配置优化

### 1. Docker守护进程配置
```bash
# 创建或编辑配置文件
sudo nano /etc/docker/daemon.json
```

**推荐配置**：
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 65536,
      "Soft": 65536
    }
  }
}
```

### 2. 重启Docker服务应用配置
```bash
sudo systemctl restart docker
```

## 验证安装

### 基本命令测试
```bash
# 检查Docker版本
docker --version
docker-compose --version

# 检查Docker运行状态
sudo systemctl status docker

# 运行测试容器
docker run --rm hello-world

# 查看Docker信息
docker info
```

### 性能测试
```bash
# 运行一个简单的性能测试容器
docker run --rm -it alpine sh -c "time echo 'Docker is working!'"

# 检查资源使用
docker stats --no-stream
```

## 故障排除

### 常见问题1：权限拒绝
```bash
# 错误：Got permission denied while trying to connect to the Docker daemon socket
sudo usermod -aG docker $USER
newgrp docker
```

### 常见问题2：WSL2 Docker服务启动失败
```bash
# 检查WSL2版本
wsl --version

# 更新WSL2内核
wsl --update

# 重启WSL2
wsl --shutdown
# 然后重新打开终端
```

### 常见问题3：存储驱动问题
```bash
# 检查当前存储驱动
docker info | grep "Storage Driver"

# 如果使用devicemapper，建议切换到overlay2
```

## 安全建议

### 1. 启用用户命名空间
```bash
# 编辑Docker配置
sudo nano /etc/docker/daemon.json

# 添加用户命名空间配置
{
  "userns-remap": "default"
}
```

### 2. 限制容器资源
```bash
# 运行容器时设置资源限制
docker run --memory=512m --cpus=1.0 --rm hello-world
```

### 3. 定期更新
```bash
# 更新Docker和相关组件
sudo apt-get update
sudo apt-get upgrade docker-ce docker-ce-cli containerd.io
```

## 下一步
安装完成后，可以开始：
1. **学习Docker基础命令**
2. **创建第一个自定义镜像**
3. **部署实际应用容器**
4. **学习Docker Compose编排**

## 参考文档
- [Docker官方安装指南](https://docs.docker.com/engine/install/ubuntu/)
- [WSL2 Docker集成](https://docs.docker.com/desktop/wsl/)
- [Docker安全最佳实践](https://docs.docker.com/engine/security/)