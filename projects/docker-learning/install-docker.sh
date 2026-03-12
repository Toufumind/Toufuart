#!/bin/bash
# Docker安装脚本

echo "=== 开始安装Docker ==="

# 1. 更新包列表
echo "更新包列表..."
sudo apt-get update

# 2. 安装依赖
echo "安装依赖包..."
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 3. 添加Docker官方GPG密钥
echo "添加Docker GPG密钥..."
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 4. 设置存储库
echo "设置Docker存储库..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. 安装Docker引擎
echo "安装Docker引擎..."
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 6. 启动Docker服务
echo "启动Docker服务..."
sudo service docker start
sudo systemctl enable docker

# 7. 将用户添加到docker组
echo "配置用户权限..."
sudo groupadd docker 2>/dev/null || true
sudo usermod -aG docker $USER

# 8. 验证安装
echo "验证Docker安装..."
docker --version
docker-compose --version

echo "=== Docker安装完成 ==="
echo "请重新登录或运行 'newgrp docker' 使组更改生效"