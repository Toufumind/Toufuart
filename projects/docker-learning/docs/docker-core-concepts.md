# Docker核心概念深度理解

## 一、Docker架构概述

### 1.1 Docker组件架构
```
用户 → Docker CLI → Docker Daemon → Containerd → RunC → 容器
      ↓              ↓               ↓           ↓
   镜像仓库       镜像管理       容器运行时   底层运行时
```

### 1.2 关键组件详解

#### Docker Daemon (dockerd)
```go
// 简化版Docker Daemon架构
type DockerDaemon struct {
    ImageStore    ImageStorage      // 镜像存储
    ContainerStore ContainerStorage // 容器存储
    NetworkManager NetworkManager   // 网络管理
    VolumeManager  VolumeManager    // 卷管理
    
    // 核心方法
    PullImage(image string) error
    CreateContainer(config ContainerConfig) (string, error)
    StartContainer(id string) error
    StopContainer(id string) error
}
```

#### Containerd
```go
// Containerd作为容器运行时管理器
type Containerd struct {
    Tasks      map[string]*Task    // 任务管理
    Images     map[string]*Image   // 镜像管理
    Namespaces map[string]*Namespace // 命名空间
    
    // 支持多种运行时
    Runtimes map[string]Runtime {
        "runc":    &RunCRuntime{},
        "kata":    &KataRuntime{},
        "gvisor":  &GVisorRuntime{},
    }
}
```

#### RunC (OCI运行时)
```go
// RunC实现OCI运行时规范
type RunC struct {
    RootDir    string              // 容器根目录
    LogFile    string              // 日志文件
    PidFile    string              // PID文件
    
    // OCI规范实现
    Create(config *specs.Spec, id string) error
    Start(id string) error
    Kill(id string, signal syscall.Signal) error
    Delete(id string) error
}
```

## 二、镜像系统深度分析

### 2.1 镜像分层结构
```
应用层 (可写层)
    ↓
镜像层N (应用依赖)
    ↓
镜像层2 (系统工具)
    ↓
镜像层1 (基础系统)
    ↓
引导层 (scratch/空)
```

### 2.2 镜像构建过程
```dockerfile
# Dockerfile示例 - 多阶段构建
# 阶段1: 构建阶段
FROM golang:1.21 AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /app/main

# 阶段2: 运行阶段
FROM alpine:latest AS runner
WORKDIR /root/
COPY --from=builder /app/main .
RUN addgroup -S app && adduser -S app -G app
USER app
CMD ["./main"]
```

### 2.3 镜像存储机制
```go
// Docker镜像存储结构
type ImageStorage struct {
    Layers map[string]*Layer      // 层存储
    Manifests map[string]*Manifest // 清单文件
    Configs   map[string]*Config   // 配置信息
    
    // 层复用机制
    LayerCache *LRUCache           // 层缓存
    DiffIDs    map[string]string   // 差异ID映射
}

// 镜像层结构
type Layer struct {
    DiffID    string              // 差异ID (sha256)
    ChainID   string              // 链ID (累积sha256)
    Parent    *Layer              // 父层
    Size      int64               // 层大小
    TarPath   string              // tar包路径
    Created   time.Time           // 创建时间
}
```

## 三、容器运行时深度分析

### 3.1 容器创建过程
```go
func createContainer(config ContainerConfig) error {
    // 1. 创建容器根文件系统
    rootfs := createRootFS(config.Image)
    
    // 2. 配置命名空间
    namespaces := configureNamespaces(config)
    
    // 3. 配置控制组 (cgroups)
    cgroups := configureCgroups(config)
    
    // 4. 配置能力 (Capabilities)
    caps := configureCapabilities(config)
    
    // 5. 配置安全选项
    security := configureSecurity(config)
    
    // 6. 创建OCI运行时配置
    spec := createOCISpec(rootfs, namespaces, cgroups, caps, security)
    
    // 7. 调用RunC创建容器
    return runc.Create(spec, config.ID)
}
```

### 3.2 命名空间隔离
```go
// Linux命名空间类型
const (
    CLONE_NEWNS   = 0x00020000   // Mount namespace
    CLONE_NEWUTS  = 0x04000000   // UTS namespace (主机名)
    CLONE_NEWIPC  = 0x08000000   // IPC namespace
    CLONE_NEWPID  = 0x20000000   // PID namespace
    CLONE_NEWNET  = 0x40000000   // Network namespace
    CLONE_NEWUSER = 0x10000000   // User namespace
    CLONE_NEWCGROUP = 0x02000000 // Cgroup namespace
)

// 容器命名空间配置
type NamespaceConfig struct {
    Type string `json:"type"`  // 命名空间类型
    Path string `json:"path"`  // 命名空间路径
}

// 创建命名空间
func createNamespace(nsType string) (int, error) {
    var flags int
    
    switch nsType {
    case "pid":
        flags = syscall.CLONE_NEWPID
    case "net":
        flags = syscall.CLONE_NEWNET
    case "mnt":
        flags = syscall.CLONE_NEWNS
    case "ipc":
        flags = syscall.CLONE_NEWIPC
    case "uts":
        flags = syscall.CLONE_NEWUTS
    case "user":
        flags = syscall.CLONE_NEWUSER
    case "cgroup":
        flags = syscall.CLONE_NEWCGROUP
    }
    
    // 调用unshare系统调用
    return syscall.Unshare(flags)
}
```

### 3.3 控制组 (cgroups) 配置
```go
// cgroups v2配置
type CgroupConfig struct {
    Memory struct {
        Max  string `json:"max"`   // 内存限制
        Swap string `json:"swap"`  // 交换内存限制
        High string `json:"high"`  // 内存高水位线
    } `json:"memory"`
    
    CPU struct {
        Weight uint64 `json:"weight"`  // CPU权重
        Max    string `json:"max"`     // CPU时间限制
        Cpus   string `json:"cpus"`    // CPU集合
    } `json:"cpu"`
    
    Pids struct {
        Max int64 `json:"max"`  // 最大进程数
    } `json:"pids"`
    
    IO struct {
        Weight uint16 `json:"weight"`  // IO权重
        Max    string `json:"max"`     // IO限制
    } `json:"io"`
}

// 应用cgroups配置
func applyCgroupConfig(pid int, config CgroupConfig) error {
    // 创建cgroup目录
    cgroupPath := fmt.Sprintf("/sys/fs/cgroup/%d", pid)
    os.MkdirAll(cgroupPath, 0755)
    
    // 写入内存限制
    writeFile(cgroupPath+"/memory.max", config.Memory.Max)
    writeFile(cgroupPath+"/memory.swap.max", config.Memory.Swap)
    
    // 写入CPU限制
    writeFile(cgroupPath+"/cpu.weight", strconv.FormatUint(config.CPU.Weight, 10))
    writeFile(cgroupPath+"/cpu.max", config.CPU.Max)
    
    // 写入进程数限制
    writeFile(cgroupPath+"/pids.max", strconv.FormatInt(config.Pids.Max, 10))
    
    // 将进程加入cgroup
    writeFile(cgroupPath+"/cgroup.procs", strconv.Itoa(pid))
    
    return nil
}
```

## 四、网络系统深度分析

### 4.1 Docker网络模型
```
容器网络命名空间
    ↓
veth pair (虚拟以太网对)
    ↓
Docker网桥 (docker0)
    ↓
主机网络栈
    ↓
物理网络接口
```

### 4.2 网络驱动实现
```go
// 网络驱动接口
type NetworkDriver interface {
    CreateNetwork(name string, options map[string]interface{}) error
    DeleteNetwork(name string) error
    CreateEndpoint(network, endpoint string, options map[string]interface{}) error
    DeleteEndpoint(network, endpoint string) error
    Join(network, endpoint, sandbox string) error
    Leave(network, endpoint, sandbox string) error
}

// 网桥驱动实现
type BridgeDriver struct {
    networks map[string]*BridgeNetwork
    lock     sync.RWMutex
}

type BridgeNetwork struct {
    Name     string
    Bridge   string          // 网桥名称 (如docker0)
    Subnet   *net.IPNet      // 子网
    Gateway  net.IP          // 网关
    IPAM     IPAM            // IP地址管理
    Options  map[string]interface{}
}

// 创建网络
func (d *BridgeDriver) CreateNetwork(name string, options map[string]interface{}) error {
    d.lock.Lock()
    defer d.lock.Unlock()
    
    // 1. 创建网桥
    bridgeName := "br-" + name[:8]
    if err := createBridge(bridgeName); err != nil {
        return err
    }
    
    // 2. 配置IP地址
    subnet := options["subnet"].(string)
    gateway := options["gateway"].(string)
    
    ip, ipNet, _ := net.ParseCIDR(subnet)
    gw := net.ParseIP(gateway)
    
    // 3. 配置网桥IP
    if err := setBridgeIP(bridgeName, gw, ipNet); err != nil {
        return err
    }
    
    // 4. 存储网络配置
    d.networks[name] = &BridgeNetwork{
        Name:    name,
        Bridge:  bridgeName,
        Subnet:  ipNet,
        Gateway: gw,
        IPAM:    NewIPAM(ipNet),
    }
    
    return nil
}
```

### 4.3 容器网络配置过程
```go
func configureContainerNetwork(containerID, networkName string) error {
    // 1. 获取网络配置
    network := getNetwork(networkName)
    
    // 2. 创建veth pair
    hostVeth, containerVeth := createVethPair()
    
    // 3. 将host端加入网桥
    addToBridge(hostVeth, network.Bridge)
    
    // 4. 将container端加入容器网络命名空间
    moveToNamespace(containerVeth, containerID)
    
    // 5. 配置容器端IP地址
    ip := network.IPAM.Allocate()
    setInterfaceIP(containerVeth, ip, network.Subnet)
    
    // 6. 启动接口
    setInterfaceUp(containerVeth)
    
    // 7. 配置默认路由
    setDefaultRoute(containerVeth, network.Gateway)
    
    return nil
}
```

## 五、存储系统深度分析

### 5.1 存储驱动架构
```go
// 存储驱动接口
type StorageDriver interface {
    String() string
    Create(id, parent string) error
    Remove(id string) error
    Get(id, mountLabel string) (string, error)
    Put(id string) error
    Exists(id string) bool
    Status() [][2]string
    Cleanup() error
}

// 常用存储驱动
var drivers = map[string]StorageDriver{
    "overlay2": &Overlay2Driver{},
    "aufs":     &AufsDriver{},
    "devicemapper": &DeviceMapperDriver{},
    "btrfs":    &BtrfsDriver{},
    "zfs":      &ZfsDriver{},
}
```

### 5.2 Overlay2驱动实现
```go
type Overlay2Driver struct {
    home    string              // 驱动根目录
    layers  map[string]*LayerInfo
    lock    sync.RWMutex
}

type LayerInfo struct {
    Parent   string            // 父层ID
    Path     string            // 层路径
    DiffPath string            // 差异路径
    WorkDir  string            // 工作目录
}

// 创建Overlay2挂载
func (d *Overlay2Driver) Create(id, parent string) error {
    // 创建层目录结构
    layerDir := path.Join(d.home, id)
    diffDir := path.Join(layerDir, "diff")
    workDir := path.Join(layerDir, "work")
    
    os.MkdirAll(diffDir, 0755)
    os.MkdirAll(workDir, 0755)
    
    // 存储层信息
    d.layers[id] = &LayerInfo{
        Parent:   parent,
        Path:     layerDir,
        DiffPath: diffDir,
        WorkDir:  workDir,
    }
    
    return nil
}

// 挂载Overlay2文件系统
func (d *Overlay2Driver) Get(id, mountLabel string) (string, error) {
    layer := d.layers[id]
    
    // 构建lowerdir列表（所有父层）
    lowerDirs := []string{}
    current := layer
    for current.Parent != "" {
        parent := d.layers[current.Parent]
        lowerDirs = append([]string{parent.DiffPath}, lowerDirs...)
        current = parent
    }
    
    // 挂载选项
    opts := fmt.Sprintf(
        "lowerdir=%s,upperdir=%s,workdir=%s",
        strings.Join(lowerDirs, ":"),
        layer.DiffPath,
        layer.WorkDir,
    )
    
    // 挂载点
    mountpoint := path.Join(d.home, "mnt", id)
    os.MkdirAll(mountpoint, 0755)
    
    // 执行挂载
    return mountpoint, syscall.Mount("overlay", mountpoint, "overlay", 0, opts)
}
```

## 六、安全机制深度分析

### 6.1 安全配置选项
```go
type SecurityConfig struct {
    // 用户命名空间
    UsernsMode string `json:"usernsMode"`  // "host" | "private"
    
    // 能力配置
    CapAdd  []string `json:"capAdd"`   // 添加的能力
    CapDrop []string `json:"capDrop"`  // 删除的能力
    
    // SELinux/AppArmor
    SecurityOpt []string `json:"securityOpt"`
    
    // 只读根文件系统
    ReadonlyRootfs bool `json:"readonlyRootfs"`
    
    // 无特权模式
    Privileged bool `json:"privileged"`
    
    // 用户和组
    User string `json:"user"`  // "uid:gid"
    
    // 设备白名单
    Devices []DeviceMapping `json:"devices"`
}

// 应用安全配置
func applySecurityConfig(pid int, config SecurityConfig) error {
    // 1. 配置能力
    if len(config.CapDrop) > 0 {
        dropCapabilities(pid, config.CapDrop)
    }
    if len(config.CapAdd) > 0 {
        addCapabilities(pid, config.CapAdd)
    }
    
    // 2. 配置SELinux/AppArmor
    if len(config.SecurityOpt) > 0 {
        applySecurityOptions(pid, config.SecurityOpt)
    }
    
    // 3. 配置只读根文件系统
    if config.ReadonlyRootfs {
        makeRootfsReadonly(pid)
    }
    
    // 4. 配置用户
    if config.User != "" {
        setContainerUser(pid, config.User)
    }
    
    // 5. 配置设备
    for _, device := range config.Devices {
        allowDevice(pid, device)
    }
    
    return nil
}
```

### 6.2 能力 (Capabilities) 管理
```go
// Linux能力常量
const (
    CAP_CHOWN = 0
    CAP_DAC_OVERRIDE = 1
    CAP_DAC_READ_SEARCH = 2
    CAP_FOWNER = 3
    CAP_FSETID = 4
    CAP_KILL = 5
    CAP_SETGID = 6
    CAP_SETUID = 7
    CAP_SETPCAP = 8
    CAP_LINUX_IMMUTABLE = 9
    CAP_NET_BIND_SERVICE = 10
    // ... 更多能力
    CAP_BLOCK_SUSPEND = 36
    CAP_AUDIT_READ = 37
    CAP_PERFMON = 38
    CAP_BPF = 39
    CAP_CHECKPOINT_RESTORE = 40
)

// 能力集操作
type CapSet struct {
    Effective   uint64  // 有效能力
    Permitted   uint64  // 允许能力
    Inheritable uint64  // 可继承能力
    Bounding    uint64  // 边界能力
    Ambient     uint64  // 环境能力
}

// 删除容器能力
func dropCapabilities(pid int, caps []string) error {
    var capSet CapSet
    
    // 获取当前能力集
    getCapabilities(pid, &capSet)
    
    // 删除指定能力
    for _, capName := range