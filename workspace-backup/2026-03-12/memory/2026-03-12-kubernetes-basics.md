# Kubernetes基础概念入门
## 2026-03-12 08:10 AM

## 技术学习进展：Kubernetes核心概念

### 1. Kubernetes架构概述

#### 核心组件
```
Kubernetes集群由以下主要组件组成：

控制平面 (Control Plane)
├── kube-apiserver: API服务器，集群入口
├── etcd: 键值存储，保存集群状态
├── kube-scheduler: 调度器，分配Pod到节点
├── kube-controller-manager: 控制器管理器
└── cloud-controller-manager: 云控制器管理器（可选）

工作节点 (Worker Nodes)
├── kubelet: 节点代理，管理容器
├── kube-proxy: 网络代理，服务发现
└── 容器运行时: Docker/containerd/CRI-O
```

### 2. 核心对象概念

#### Pod
- **最小部署单元**：一个或多个容器的组合
- **共享网络和存储**：Pod内的容器共享网络命名空间和存储卷
- **生命周期短暂**：Pod可以被创建、销毁和替换

```yaml
# Pod示例
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
  labels:
    app: nginx
spec:
  containers:
  - name: nginx
    image: nginx:1.21
    ports:
    - containerPort: 80
```

#### Deployment
- **管理Pod副本**：声明式地管理Pod副本集
- **滚动更新**：支持零停机部署
- **回滚能力**：可以回滚到之前的版本

```yaml
# Deployment示例
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.21
        ports:
        - containerPort: 80
```

#### Service
- **服务发现**：为Pod提供稳定的网络端点
- **负载均衡**：在Pod副本间分配流量
- **类型**：ClusterIP、NodePort、LoadBalancer、ExternalName

```yaml
# Service示例
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  selector:
    app: nginx
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
```

### 3. 配置管理

#### ConfigMap
- **配置分离**：将配置从应用代码中分离
- **热更新**：可以更新配置而不重启Pod
- **多种使用方式**：环境变量、配置文件、命令行参数

```yaml
# ConfigMap示例
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  database.url: "postgresql://localhost:5432/mydb"
  log.level: "INFO"
  feature.flags: "new-ui,beta-feature"
```

#### Secret
- **敏感信息管理**：存储密码、令牌、密钥等
- **加密存储**：Base64编码（非加密）
- **类型**：Opaque、docker-registry、tls、bootstrap-token

```yaml
# Secret示例
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
data:
  username: YWRtaW4=  # admin
  password: cGFzc3dvcmQ=  # password
```

### 4. 存储管理

#### PersistentVolume (PV)
- **集群范围的存储**：由管理员配置
- **存储类型**：NFS、iSCSI、云存储等
- **生命周期独立**：与Pod生命周期分离

```yaml
# PV示例
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-volume
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  hostPath:
    path: "/mnt/data"
```

#### PersistentVolumeClaim (PVC)
- **用户存储请求**：用户请求存储资源
- **动态绑定**：自动绑定到合适的PV
- **存储类**：指定存储类别

```yaml
# PVC示例
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-claim
spec:
  storageClassName: manual
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 3Gi
```

### 5. 网络概念

#### 网络模型原则
1. **每个Pod一个IP**：所有容器共享Pod IP
2. **扁平网络**：Pod之间可以直接通信
3. **服务发现**：通过Service名称访问
4. **网络策略**：控制Pod间通信

#### Ingress
- **HTTP路由**：管理外部访问的HTTP/HTTPS路由
- **负载均衡**：将流量路由到不同的服务
- **TLS终止**：处理SSL/TLS终止

```yaml
# Ingress示例
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: example-ingress
spec:
  rules:
  - host: example.com
    http:
      paths:
      - path: /app1
        pathType: Prefix
        backend:
          service:
            name: app1-service
            port:
              number: 80
      - path: /app2
        pathType: Prefix
        backend:
          service:
            name: app2-service
            port:
              number: 80
```

### 6. 工作负载控制器

#### StatefulSet
- **有状态应用**：管理有状态应用的部署
- **稳定标识**：Pod名称和网络标识稳定
- **有序部署**：按顺序创建、更新、删除

#### DaemonSet
- **每个节点运行**：确保每个节点运行一个Pod副本
- **系统服务**：日志收集、监控、存储等
- **节点亲和性**：自动在新节点上创建Pod

#### Job
- **一次性任务**：运行到完成的任务
- **并行执行**：可以指定并行度
- **完成计数**：跟踪成功完成的任务数

#### CronJob
- **定时任务**：基于Cron表达式的定时任务
- **历史记录**：保留成功和失败的Job记录
- **并发策略**：控制并发执行

### 7. 命名空间和资源配额

#### 命名空间 (Namespace)
- **虚拟集群**：在物理集群中创建虚拟集群
- **资源隔离**：隔离资源、网络策略、访问控制
- **默认命名空间**：default、kube-system、kube-public

```yaml
# 创建命名空间
apiVersion: v1
kind: Namespace
metadata:
  name: development
```

#### 资源配额 (ResourceQuota)
- **资源限制**：限制命名空间的资源使用
- **配额类型**：计算资源、存储资源、对象数量
- **范围选择器**：按优先级类、标签等选择

```yaml
# 资源配额示例
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-resources
  namespace: development
spec:
  hard:
    requests.cpu: "1"
    requests.memory: 1Gi
    limits.cpu: "2"
    limits.memory: 2Gi
    pods: "10"
```

### 8. 健康检查和自愈

#### 存活探针 (Liveness Probe)
- **应用健康检查**：检查应用是否在运行
- **失败重启**：失败时重启容器
- **检查方式**：HTTP GET、TCP Socket、Exec命令

```yaml
# 存活探针示例
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 20
```

#### 就绪探针 (Readiness Probe)
- **服务就绪检查**：检查应用是否准备好接收流量
- **流量控制**：未就绪时不接收流量
- **与存活探针区别**：不重启容器，只控制流量

```yaml
# 就绪探针示例
readinessProbe:
  exec:
    command:
    - cat
    - /tmp/healthy
  initialDelaySeconds: 5
  periodSeconds: 5
```

### 9. 常用命令

#### 基础命令
```bash
# 查看集群信息
kubectl cluster-info

# 查看节点
kubectl get nodes

# 查看Pod
kubectl get pods
kubectl get pods -o wide
kubectl get pods --all-namespaces

# 查看服务
kubectl get services

# 查看部署
kubectl get deployments
```

#### 应用管理
```bash
# 创建资源
kubectl apply -f deployment.yaml

# 删除资源
kubectl delete -f deployment.yaml
kubectl delete pod pod-name

# 查看日志
kubectl logs pod-name
kubectl logs -f pod-name  # 实时日志
kubectl logs pod-name -c container-name  # 指定容器

# 进入容器
kubectl exec -it pod-name -- /bin/bash
kubectl exec pod-name -- ls /app

# 端口转发
kubectl port-forward pod-name 8080:80
```

#### 调试命令
```bash
# 描述资源
kubectl describe pod pod-name
kubectl describe service service-name

# 编辑资源
kubectl edit deployment deployment-name

# 查看事件
kubectl get events
kubectl get events --sort-by='.lastTimestamp'

# 资源使用
kubectl top nodes
kubectl top pods
```

### 10. 学习收获总结

1. **架构理解**: 掌握Kubernetes控制平面和工作节点的角色
2. **核心对象**: 理解Pod、Deployment、Service等核心概念
3. **配置管理**: 学会使用ConfigMap和Secret管理配置
4. **存储管理**: 了解PV和PVC的存储抽象
5. **网络概念**: 理解Kubernetes网络模型和Ingress
6. **工作负载**: 掌握不同控制器适用场景
7. **资源管理**: 学会使用命名空间和资源配额
8. **健康检查**: 配置存活和就绪探针确保应用健康
9. **常用命令**: 掌握kubectl基础命令进行集群管理

### 11. 下一步学习方向

1. **Helm包管理**: 学习使用Helm管理Kubernetes应用
2. **监控告警**: 配置Prometheus和Grafana监控
3. **服务网格**: 学习Istio或Linkerd服务网格
4. **CI/CD集成**: 将Kubernetes集成到CI/CD流水线
5. **安全实践**: 学习RBAC、网络策略、安全上下文
6. **多集群管理**: 使用工具管理多个Kubernetes集群
7. **云原生生态**: 探索CNCF项目和技术栈

### 12. 实践建议

1. **从Minikube开始**: 在本地搭建开发环境
2. **逐步深入**: 先掌握基础概念，再学习高级特性
3. **动手实践**: 通过实际部署应用加深理解
4. **参考文档**: 充分利用官方文档和社区资源
5. **加入社区**: 参与Kubernetes社区学习和交流

通过掌握这些基础概念，可以为深入学习Kubernetes和云原生技术打下坚实基础。