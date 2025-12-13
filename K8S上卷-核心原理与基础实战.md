# Kubernetes 生产实战指南 - 上卷: 核心原理与基础实战

**副标题**: 从零构建 Kubernetes 知识体系
**目标读者**: Kubernetes 初学者、应用开发者、运维工程师
**学习目标**: 掌握 K8s 核心概念,能够独立部署和管理应用

---

## 📚 全书导航

- **上卷 (本卷)**: 核心原理与基础实战 (第1-12章)
- **中卷**: 高级特性与生态集成 (第13-24章)
- **下卷**: 生产运维与云原生架构 (第25-36章)

---

# 第1章: Kubernetes 架构与核心概念

本章将带您深入理解 Kubernetes 的设计理念、架构模型和核心概念,为后续学习打下坚实基础。

---

## 1.1 Kubernetes 是什么

### 1.1.1 容器编排的演进历史

**容器技术的兴起**

2013年,Docker 的出现彻底改变了应用部署方式:

```
传统虚拟机时代:
┌─────────────────────────────────┐
│         Application             │
│  ┌────────┐  ┌────────┐        │
│  │  App1  │  │  App2  │        │
│  ├────────┤  ├────────┤        │
│  │ Bins   │  │ Bins   │        │
│  └────────┘  └────────┘        │
├─────────────────────────────────┤
│      Guest OS    Guest OS       │
├─────────────────────────────────┤
│         Hypervisor              │
├─────────────────────────────────┤
│         Host OS                 │
├─────────────────────────────────┤
│       Infrastructure            │
└─────────────────────────────────┘
启动时间: 分钟级
资源开销: 大 (每个OS几GB)

Docker容器时代:
┌─────────────────────────────────┐
│  ┌────────┐  ┌────────┐        │
│  │  App1  │  │  App2  │        │
│  ├────────┤  ├────────┤        │
│  │ Bins   │  │ Bins   │        │
│  └────────┘  └────────┘        │
├─────────────────────────────────┤
│      Docker Engine              │
├─────────────────────────────────┤
│         Host OS                 │
├─────────────────────────────────┤
│       Infrastructure            │
└─────────────────────────────────┘
启动时间: 秒级
资源开销: 小 (共享OS内核)
```

**容器编排的必要性**

当容器数量从几个增长到成百上千时,面临的挑战:

1. **服务发现**: 容器IP动态变化,如何找到服务?
2. **负载均衡**: 如何在多个容器实例间分配流量?
3. **故障恢复**: 容器挂了如何自动重启?
4. **滚动更新**: 如何实现零停机更新?
5. **资源调度**: 如何在集群中高效分配资源?
6. **配置管理**: 如何统一管理成百上千容器的配置?

**三大编排系统对比**

| 特性 | Docker Swarm | Apache Mesos | Kubernetes |
|------|--------------|--------------|------------|
| **诞生时间** | 2015年 | 2009年 | 2014年 |
| **发起方** | Docker公司 | UC Berkeley | Google |
| **学习曲线** | ⭐⭐ 简单 | ⭐⭐⭐⭐⭐ 复杂 | ⭐⭐⭐⭐ 中等 |
| **功能丰富度** | ⭐⭐⭐ 基础功能 | ⭐⭐⭐⭐ 灵活但需定制 | ⭐⭐⭐⭐⭐ 功能全面 |
| **生态系统** | 较小 | 中等 | 最丰富 |
| **社区活跃度** | 下降中 | 中等 | 最活跃 |
| **适用规模** | 小型集群 | 大规模数据中心 | 中大型集群 |
| **市场份额** | <5% | <10% | >85% |

**Kubernetes 的胜出**

到 2020 年,Kubernetes 已成为容器编排的事实标准:

- **Google 15年容器经验**: 起源于 Borg/Omega 系统
- **CNCF 背书**: 2015年成为CNCF首个项目
- **云厂商支持**: AWS EKS/Azure AKS/Google GKE 全面支持
- **生态繁荣**: 数千个云原生项目围绕K8s构建

```bash
# 2024年 CNCF 调查报告
- 生产环境使用K8s: 96%
- 集群数量 >10个: 47%
- 容器数量 >1000: 53%
```

### 1.1.2 Kubernetes 核心价值

**1. 自动化运维**

```yaml
# 声明式配置: 告诉K8s"想要什么",而非"怎么做"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  replicas: 3  # 期望状态: 3个副本
  template:
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
```

K8s 会持续工作确保实际状态 = 期望状态:
- 容器崩溃? → 自动重启
- 节点宕机? → 自动迁移Pod到健康节点
- 负载增加? → 自动扩容(HPA)
- 资源不足? → 自动扩展节点(Cluster Autoscaler)

**2. 弹性伸缩**

```yaml
# 水平自动扩缩容 (HPA)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: nginx-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nginx
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70  # CPU >70% 时扩容
```

实际效果:
```
时间    负载    副本数    说明
08:00   20%     2        低峰期,保持最小副本
12:00   75%     5        午高峰,自动扩容到5个
14:00   90%     8        持续高负载,继续扩容
18:00   40%     3        负载下降,自动缩容
```

**3. 服务发现与负载均衡**

```yaml
# Service: 为动态Pod提供稳定访问入口
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  selector:
    app: nginx
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
  type: LoadBalancer  # 云厂商自动创建LB
```

工作原理:
```
用户请求
   ↓
LoadBalancer (云LB)
   ↓
Service (虚拟IP: 10.96.0.10)
   ↓
kube-proxy (iptables/ipvs规则)
   ↓
负载均衡到后端Pod
   ├→ Pod1 (IP: 10.244.1.5)
   ├→ Pod2 (IP: 10.244.2.8)
   └→ Pod3 (IP: 10.244.3.12)
```

Pod IP会变化,但Service IP永远不变!

**4. 存储编排**

```yaml
# 持久化卷声明: 应用无需关心底层存储实现
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: fast-ssd  # 自动供给SSD存储
---
apiVersion: v1
kind: Pod
metadata:
  name: mysql
spec:
  containers:
  - name: mysql
    image: mysql:8.0
    volumeMounts:
    - name: mysql-data
      mountPath: /var/lib/mysql
  volumes:
  - name: mysql-data
    persistentVolumeClaim:
      claimName: mysql-pvc
```

底层可以是:
- NFS 网络存储
- Ceph 分布式存储
- AWS EBS / Azure Disk / GCP PD
- 本地SSD

应用层完全透明!

**5. 配置与密钥管理**

```yaml
# ConfigMap: 配置与代码分离
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  database.host: "mysql.prod.svc.cluster.local"
  database.port: "3306"
  log.level: "info"
---
# Secret: 敏感信息加密存储
apiVersion: v1
kind: Secret
metadata:
  name: mysql-secret
type: Opaque
data:
  password: bXlwYXNzd29yZA==  # base64编码
---
# Pod使用配置
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: myapp:1.0
    env:
    - name: DB_HOST
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database.host
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: mysql-secret
          key: password
```

### 1.1.3 K8s vs Docker Swarm 详细对比

**架构对比**

```
Docker Swarm 架构:
┌─────────────────────────────────────┐
│         Manager Nodes               │
│  ┌──────────────────────────────┐  │
│  │   Swarm Manager (Raft)       │  │
│  │  ┌────────┐  ┌────────┐     │  │
│  │  │ Leader │  │Follower│     │  │
│  │  └────────┘  └────────┘     │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│         Worker Nodes                │
│  ┌────────┐  ┌────────┐  ┌───────┐ │
│  │Docker  │  │Docker  │  │Docker │ │
│  │Engine  │  │Engine  │  │Engine │ │
│  └────────┘  └────────┘  └───────┘ │
└─────────────────────────────────────┘

Kubernetes 架构:
┌─────────────────────────────────────┐
│         Master Nodes                │
│  ┌────────────┐  ┌────────────┐   │
│  │API Server  │  │ Scheduler  │   │
│  └────────────┘  └────────────┘   │
│  ┌────────────┐  ┌────────────┐   │
│  │Controller  │  │   etcd     │   │
│  │  Manager   │  │  (Raft)    │   │
│  └────────────┘  └────────────┘   │
└─────────────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│         Worker Nodes                │
│  ┌────────────────────────────────┐ │
│  │ kubelet + kube-proxy          │ │
│  │ ┌────┐ ┌────┐ ┌────┐         │ │
│  │ │Pod │ │Pod │ │Pod │         │ │
│  │ └────┘ └────┘ └────┘         │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
```

**功能对比**

| 功能 | Docker Swarm | Kubernetes |
|------|--------------|------------|
| **部署单位** | Container | Pod (多容器组) |
| **配置方式** | docker-compose.yml | YAML (多种资源) |
| **服务发现** | DNS + VIP | DNS + Service + CoreDNS |
| **负载均衡** | Routing Mesh (简单) | Service + Ingress (灵活) |
| **滚动更新** | 支持 | 支持 + 更精细控制 |
| **健康检查** | HEALTHCHECK指令 | Liveness/Readiness/Startup Probe |
| **自动扩缩容** | 手动调整replicas | HPA/VPA/Cluster Autoscaler |
| **存储编排** | Volume (有限) | PV/PVC/StorageClass (丰富) |
| **配置管理** | Config/Secret (基础) | ConfigMap/Secret (完善) |
| **网络插件** | Overlay Network | CNI (Calico/Cilium/Flannel等) |
| **RBAC权限** | 基础 | 细粒度RBAC |
| **监控集成** | 需自建 | Prometheus/Grafana (成熟生态) |
| **日志收集** | 需自建 | EFK/PLG Stack (成熟方案) |
| **包管理** | 无 | Helm/Kustomize |
| **Operator** | 无 | 丰富的Operator生态 |

**学习曲线对比**

```
复杂度
  ↑
  │                           ╱
  │                       ╱
  │                   ╱  K8s
  │               ╱
  │           ╱
  │   Swarm╱
  │   ╱
  │╱
  └──────────────────────────→ 时间
  入门    进阶    高级    专家

Swarm: 2周入门 → 1个月熟练
K8s:   1个月入门 → 3个月熟练 → 持续学习
```

**适用场景**

**Docker Swarm 适合:**
- ✅ 小型团队 (<20人)
- ✅ 中小规模应用 (<100个服务)
- ✅ 简单的微服务架构
- ✅ 快速原型验证
- ✅ 已有Docker经验,想快速上容器编排

**Kubernetes 适合:**
- ✅ 中大型团队
- ✅ 大规模应用 (100+服务)
- ✅ 复杂的微服务架构
- ✅ 需要自动扩缩容
- ✅ 多云/混合云部署
- ✅ 需要丰富的生态工具链
- ✅ 企业级生产环境

**实际案例对比**

```yaml
# Docker Swarm 部署示例
version: '3.8'
services:
  web:
    image: nginx:1.25
    deploy:
      replicas: 3
    ports:
      - "80:80"

# Kubernetes 等价配置
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
---
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  selector:
    app: web
  ports:
  - port: 80
  type: LoadBalancer
```

Swarm 更简洁,但 K8s 提供更多控制和功能!

### 1.1.4 Kubernetes 适用场景

**✅ 最适合的场景**

**1. 微服务架构**

```
传统单体应用:
┌─────────────────────────────┐
│     Monolithic App          │
│  ┌──────────────────────┐  │
│  │  UI + Logic + DB     │  │
│  └──────────────────────┘  │
└─────────────────────────────┘
问题: 扩展困难,部署风险高

微服务架构 (K8s管理):
┌──────┐  ┌──────┐  ┌──────┐
│ UI   │  │ API  │  │Auth  │
│Service│  │Gateway│ │Service│
└──────┘  └──────┘  └──────┘
   │         │         │
┌──────┐  ┌──────┐  ┌──────┐
│Order │  │User  │  │Pay   │
│Service│  │Service│ │Service│
└──────┘  └──────┘  └──────┘
   │         │         │
┌──────┐  ┌──────┐  ┌──────┐
│MySQL │  │Redis │  │Kafka │
└──────┘  └──────┘  └──────┘

K8s 优势:
- 每个服务独立部署/扩展
- 服务发现自动化
- 滚动更新零停机
- 故障隔离
```

**2. 云原生应用**

```yaml
# 12-Factor App 示例
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cloud-native-app
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: app
        image: myapp:v2.1.0  # I. 基准代码
        env:
        - name: CONFIG_URL   # III. 配置 (环境变量)
          value: "https://config.example.com"
        ports:
        - containerPort: 8080  # VII. 端口绑定
        livenessProbe:          # IX. 易处理性
          httpGet:
            path: /health
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: app-service
spec:
  type: LoadBalancer  # IV. 后端服务
  selector:
    app: cloud-native-app
```

**3. 需要高可用的业务系统**

```yaml
# 电商系统高可用配置
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
spec:
  replicas: 5  # 多副本
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0  # 零停机更新
  template:
    spec:
      affinity:
        podAntiAffinity:  # 分散到不同节点
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - order-service
            topologyKey: kubernetes.io/hostname
      containers:
      - name: order-service
        image: order:v1.2.3
        readinessProbe:  # 就绪检查
          httpGet:
            path: /ready
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:   # 存活检查
          httpGet:
            path: /health
          initialDelaySeconds: 30
          periodSeconds: 10
```

结果:
- SLA > 99.95% (年停机 < 4.4小时)
- 单节点故障不影响服务
- 滚动更新零停机

**4. 需要弹性伸缩的应用**

```yaml
# 视频转码服务 - 根据队列长度自动扩缩容
apiVersion: apps/v1
kind: Deployment
metadata:
  name: video-transcoder
spec:
  replicas: 2  # 最小副本
  template:
    spec:
      containers:
      - name: transcoder
        image: ffmpeg-worker:latest
        resources:
          requests:
            cpu: "2"
            memory: "4Gi"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: transcoder-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: video-transcoder
  minReplicas: 2
  maxReplicas: 50  # 高峰期自动扩展到50个
  metrics:
  - type: External
    external:
      metric:
        name: rabbitmq_queue_messages
        selector:
          matchLabels:
            queue: transcode_queue
      target:
        type: AverageValue
        averageValue: "10"  # 每个Pod处理10个任务
```

实际效果:
```
队列长度  副本数  处理能力
10        2       20 任务/分钟
100       10      200 任务/分钟
500       50      1000 任务/分钟
20        2       自动缩容
```

**❌ 不适合的场景**

**1. 简单的单体应用**

```
场景: 个人博客 (WordPress)
- 1个Web容器
- 1个MySQL容器
- 访问量 <1000 PV/天

问题:
- K8s太重了,运行3个Master + 2个Worker = 5台服务器
- 学习成本高
- 维护复杂

更好的选择:
- Docker Compose
- 托管WordPress (如Hostinger)
- Serverless (如Vercel/Netlify)
```

**2. 遗留系统 (Legacy Applications)**

```
场景: 15年历史的Java Swing桌面应用
- 依赖Windows特定库
- 需要GUI界面
- 状态绑定本地文件

问题:
- 无法容器化
- 不符合12-Factor
- 无法水平扩展

更好的选择:
- 传统虚拟机部署
- 逐步重构为Web应用
```

**3. 硬件绑定应用**

```
场景: GPU深度学习训练
- 需要8卡A100 GPU
- 单任务运行数天
- CUDA版本严格绑定

问题:
- K8s调度开销大
- GPU资源碎片化
- 故障恢复代价高

更好的选择:
- 裸金属服务器
- Slurm/PBS作业调度
- 如果一定要用K8s,考虑Kubeflow
```

**4. 超小规模部署**

```
场景: 创业公司MVP
- 1-2个开发者
- 2-3个微服务
- 预算有限

问题:
- K8s学习成本 > 开发成本
- 过度设计
- 云资源浪费

更好的选择:
- Docker Compose
- PaaS平台 (Heroku/Railway)
- Serverless
- 等规模大了再迁移K8s
```

**决策树**

```
是否需要容器编排?
├─ 否 → Docker/虚拟机
└─ 是 → 应用数量?
     ├─ <10个 → Docker Swarm/Compose
     └─ ≥10个 → 是否需要自动扩缩容?
          ├─ 否 → Docker Swarm
          └─ 是 → 团队是否有K8s经验?
               ├─ 否 → 先学习/小规模试点
               └─ 是 → Kubernetes ✅
```

---

## 1.2 Kubernetes 架构设计

### 1.2.1 Master-Node 架构模型

**整体架构图**

```
┌─────────────────────────────────────────────────────────────────┐
│                         Master Nodes                            │
│                      (Control Plane)                            │
│                                                                 │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│  │              │   │              │   │              │       │
│  │ kube-        │◄──┤   etcd       │──►│              │       │
│  │ apiserver    │   │   Cluster    │   │              │       │
│  │              │   │ (Key-Value)  │   │              │       │
│  └──────┬───────┘   └──────────────┘   └──────────────┘       │
│         │                                                       │
│         │           ┌──────────────┐   ┌──────────────┐       │
│         ├──────────►│ kube-        │   │ cloud-       │       │
│         │           │ scheduler    │   │ controller-  │       │
│         │           │              │   │ manager      │       │
│         │           └──────────────┘   └──────────────┘       │
│         │                                                       │
│         │           ┌──────────────┐                           │
│         └──────────►│ kube-        │                           │
│                     │ controller-  │                           │
│                     │ manager      │                           │
│                     └──────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴──────────┐
                    │   Kubernetes API   │
                    │   (REST/gRPC)      │
                    └─────────┬──────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼───────┐     ┌───────▼───────┐     ┌──────▼──────┐
│  Worker Node 1│     │  Worker Node 2│     │ Worker Node 3│
│               │     │               │     │              │
│ ┌───────────┐ │     │ ┌───────────┐ │     │ ┌──────────┐│
│ │  kubelet  │ │     │ │  kubelet  │ │     │ │ kubelet  ││
│ └─────┬─────┘ │     │ └─────┬─────┘ │     │ └────┬─────┘│
│       │       │     │       │       │     │      │      │
│ ┌─────▼─────┐ │     │ ┌─────▼─────┐ │     │ ┌────▼─────┐│
│ │Container  │ │     │ │Container  │ │     │ │Container ││
│ │Runtime    │ │     │ │Runtime    │ │     │ │Runtime   ││
│ │(containerd│ │     │ │(containerd│ │     │ │containerd││
│ └───────────┘ │     │ └───────────┘ │     │ └──────────┘│
│               │     │               │     │              │
│ ┌───────────┐ │     │ ┌───────────┐ │     │ ┌──────────┐│
│ │kube-proxy │ │     │ │kube-proxy │ │     │ │kube-proxy││
│ └───────────┘ │     │ └───────────┘ │     │ └──────────┘│
│               │     │               │     │              │
│ ┌─────┐┌─────┐│     │ ┌─────┐┌─────┐│     │ ┌─────┐    │
│ │ Pod ││ Pod ││     │ │ Pod ││ Pod ││     │ │ Pod │    │
│ └─────┘└─────┘│     │ └─────┘└─────┘│     │ └─────┘    │
└───────────────┘     └───────────────┘     └────────────┘
```

**Master Node (控制平面) 职责**

Master 节点负责集群的"大脑"功能:

1. **接收请求**: 通过 API Server 接收 kubectl/客户端请求
2. **状态存储**: 通过 etcd 存储集群所有状态
3. **调度决策**: 通过 Scheduler 决定 Pod 运行在哪个 Node
4. **控制循环**: 通过 Controller Manager 确保实际状态=期望状态
5. **云集成**: 通过 Cloud Controller Manager 与云平台交互

**Worker Node (数据平面) 职责**

Worker 节点负责实际运行工作负载:

1. **Pod管理**: kubelet 管理 Pod 生命周期
2. **容器运行**: containerd/CRI-O 运行容器
3. **网络代理**: kube-proxy 维护网络规则
4. **资源监控**: 上报节点和Pod资源使用情况

**高可用架构**

生产环境通常采用多Master架构:

```
                  ┌────────────────┐
                  │  LoadBalancer  │
                  │  (HAProxy/Nginx) │
                  └────────┬───────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
   ┌─────▼─────┐     ┌─────▼─────┐     ┌────▼──────┐
   │  Master1  │     │  Master2  │     │  Master3  │
   │           │     │           │     │           │
   │ API Server│     │ API Server│     │ API Server│
   │ Scheduler │     │ Scheduler │     │ Scheduler │
   │Controller │     │Controller │     │Controller │
   └─────┬─────┘     └─────┬─────┘     └─────┬─────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
                  ┌────────▼───────┐
                  │  etcd Cluster  │
                  │  (Raft共识)    │
                  │  ┌───┬───┬───┐ │
                  │  │ 1 │ 2 │ 3 │ │
                  │  └───┴───┴───┘ │
                  └────────────────┘
```

关键点:
- **3或5个Master**: 奇数个节点,防止脑裂
- **etcd集群**: 使用Raft协议保证数据一致性
- **负载均衡**: API Server前端负载均衡
- **Leader选举**: Scheduler和Controller Manager同时只有一个Leader工作

### 1.2.2 控制平面组件详解

**1. kube-apiserver: RESTful API 网关**

**核心职责**:
- 提供 RESTful API 接口
- 认证和授权 (Authentication & Authorization)
- 准入控制 (Admission Control)
- 资源验证和版本转换
- 与 etcd 交互 (唯一直接访问etcd的组件)

**工作流程**:

```
kubectl create -f deployment.yaml
         │
         ▼
┌────────────────────────────────────┐
│   1. Authentication (认证)         │
│   - X.509 证书                     │
│   - Bearer Token                   │
│   - Service Account                │
└──────────────┬─────────────────────┘
               ▼
┌────────────────────────────────────┐
│   2. Authorization (授权)          │
│   - RBAC检查                       │
│   - 是否有权限创建Deployment?      │
└──────────────┬─────────────────────┘
               ▼
┌────────────────────────────────────┐
│   3. Admission Control (准入控制)  │
│   - Mutating Webhook (修改资源)    │
│   - Validating Webhook (验证资源)  │
│   - ResourceQuota 检查             │
│   - LimitRanger 检查               │
└──────────────┬─────────────────────┘
               ▼
┌────────────────────────────────────┐
│   4. Validation (资源验证)         │
│   - Schema验证                     │
│   - 字段合法性检查                 │
└──────────────┬─────────────────────┘
               ▼
┌────────────────────────────────────┐
│   5. Persistence (持久化到etcd)    │
│   - 写入 etcd                      │
│   - 返回成功响应                   │
└────────────────────────────────────┘
```

**API 分组**:

```bash
# 核心API组 (无组名)
/api/v1/pods
/api/v1/services
/api/v1/nodes

# 应用API组
/apis/apps/v1/deployments
/apis/apps/v1/statefulsets

# 批处理API组
/apis/batch/v1/jobs
/apis/batch/v1/cronjobs

# 网络API组
/apis/networking.k8s.io/v1/ingresses
/apis/networking.k8s.io/v1/networkpolicies

# 自定义API组
/apis/stable.example.com/v1/crontabs
```

**查看API资源**:

```bash
# 列出所有API资源
kubectl api-resources

# 查看特定资源的API版本
kubectl explain deployment

# 查看API版本列表
kubectl api-versions
```

**API Server 配置示例**:

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
apiVersion: v1
kind: Pod
metadata:
  name: kube-apiserver
  namespace: kube-system
spec:
  containers:
  - name: kube-apiserver
    image: k8s.gcr.io/kube-apiserver:v1.28.0
    command:
    - kube-apiserver
    # etcd配置
    - --etcd-servers=https://127.0.0.1:2379
    - --etcd-cafile=/etc/kubernetes/pki/etcd/ca.crt
    - --etcd-certfile=/etc/kubernetes/pki/apiserver-etcd-client.crt
    - --etcd-keyfile=/etc/kubernetes/pki/apiserver-etcd-client.key
    # 认证配置
    - --client-ca-file=/etc/kubernetes/pki/ca.crt
    - --tls-cert-file=/etc/kubernetes/pki/apiserver.crt
    - --tls-private-key-file=/etc/kubernetes/pki/apiserver.key
    # 授权配置
    - --authorization-mode=Node,RBAC
    # 准入控制
    - --enable-admission-plugins=NamespaceLifecycle,LimitRanger,ServiceAccount,DefaultStorageClass,ResourceQuota
    # 服务账户配置
    - --service-account-key-file=/etc/kubernetes/pki/sa.pub
    - --service-account-signing-key-file=/etc/kubernetes/pki/sa.key
    - --service-account-issuer=https://kubernetes.default.svc.cluster.local
    # 审计日志
    - --audit-log-path=/var/log/kubernetes/audit.log
    - --audit-log-maxage=30
    - --audit-log-maxbackup=10
    - --audit-log-maxsize=100
    # 高可用配置
    - --apiserver-count=3
    # 性能调优
    - --max-requests-inflight=400
    - --max-mutating-requests-inflight=200
```


#### 1.2.2.2 etcd: 分布式键值存储

**核心职责**:

etcd 是 Kubernetes 的"唯一数据源(Single Source of Truth)",存储集群所有状态数据:

```
etcd 数据结构:
/registry/
  ├── pods/
  │   ├── default/
  │   │   ├── nginx-7c5ddbdf54-8xk9p
  │   │   └── redis-master-0
  │   └── kube-system/
  │       ├── coredns-787d4945fb-2xhjk
  │       └── kube-proxy-4k9zx
  ├── services/
  │   ├── default/kubernetes
  │   └── kube-system/kube-dns
  ├── deployments/
  ├── replicasets/
  ├── configmaps/
  └── secrets/
```

**Raft 一致性算法**:

etcd 使用 Raft 算法保证数据一致性:

```
Raft 角色转换:
┌─────────────┐
│  Follower   │ ◄───────┐
└─────────────┘         │
      │                 │
      │ 选举超时         │ 收到合法Leader心跳
      ↓                 │
┌─────────────┐         │
│  Candidate  │         │
└─────────────┘         │
      │                 │
      │ 获得多数票        │
      ↓                 │
┌─────────────┐         │
│   Leader    │─────────┘
└─────────────┘
```

**etcd 集群部署(3节点)**:

```yaml
# etcd-1 配置 (/etc/etcd/etcd.conf.yml)
name: etcd-1
data-dir: /var/lib/etcd
initial-advertise-peer-urls: https://10.0.1.10:2380
listen-peer-urls: https://10.0.1.10:2380
listen-client-urls: https://10.0.1.10:2379,https://127.0.0.1:2379
advertise-client-urls: https://10.0.1.10:2379
initial-cluster-token: etcd-cluster-prod
initial-cluster: etcd-1=https://10.0.1.10:2380,etcd-2=https://10.0.1.11:2380,etcd-3=https://10.0.1.12:2380
initial-cluster-state: new

# TLS配置
client-transport-security:
  cert-file: /etc/kubernetes/pki/etcd/server.crt
  key-file: /etc/kubernetes/pki/etcd/server.key
  trusted-ca-file: /etc/kubernetes/pki/etcd/ca.crt
peer-transport-security:
  cert-file: /etc/kubernetes/pki/etcd/peer.crt
  key-file: /etc/kubernetes/pki/etcd/peer.key
  trusted-ca-file: /etc/kubernetes/pki/etcd/ca.crt

# 性能优化
quota-backend-bytes: 8589934592  # 8GB
auto-compaction-mode: periodic
auto-compaction-retention: "1h"
snapshot-count: 10000
```

**etcd 运维命令**:

```bash
# 查看集群成员
ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  member list

# 输出示例
a8266ecf031671f3, started, etcd-1, https://10.0.1.10:2380, https://10.0.1.10:2379, false
b57481f970c2d519, started, etcd-2, https://10.0.1.11:2380, https://10.0.1.11:2379, false
c342a5e9e5da84d1, started, etcd-3, https://10.0.1.12:2380, https://10.0.1.12:2379, false

# 查看集群健康状态
ETCDCTL_API=3 etcdctl endpoint health --cluster

# 查看Leader
ETCDCTL_API=3 etcdctl endpoint status --cluster \
  --write-out=table

# 备份etcd数据
ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-snapshot-$(date +%Y%m%d-%H%M%S).db

# 恢复etcd数据
ETCDCTL_API=3 etcdctl snapshot restore /backup/etcd-snapshot.db \
  --data-dir=/var/lib/etcd-restore

# 查看K8s存储的数据
ETCDCTL_API=3 etcdctl get /registry/pods/default/nginx --prefix --keys-only

# 查看etcd性能指标
ETCDCTL_API=3 etcdctl endpoint status --write-out=table
```


**etcd 性能优化**:

```bash
# 1. 磁盘优化 (使用SSD)
# 检查磁盘延迟
sudo fio --filename=/var/lib/etcd/testfile --direct=1 --rw=write --bs=2300 --size=10G --numjobs=1 --name=etcd-fsync

# 2. 网络优化
# etcd对网络延迟敏感,建议RTT < 10ms
ping -c 10 10.0.1.11

# 3. 内存优化
# etcd进程建议分配8GB内存
# 在systemd中配置内存限制
[Service]
MemoryLimit=8G

# 4. 监控关键指标
# - Raft proposals committed: 已提交的提案数
# - Backend commit duration: 后端提交延迟
# - Leader changes: Leader切换次数 (应接近0)
# - Snapshot save time: 快照保存时间
```

---

## 1.6 本章小结

本章深入讲解了 Kubernetes 的核心概念与架构:

✅ **对比分析**: Docker Swarm vs Kubernetes 适用场景  
✅ **架构设计**: Master-Node 模型与控制平面/数据平面分离  
✅ **核心组件**:
- kube-apiserver (API网关)
- etcd (分布式存储)
- kube-scheduler (智能调度)
- kube-controller-manager (控制循环)
- kubelet (节点代理)
- kube-proxy (网络代理)

✅ **资源对象**: 统一的API对象模型与标签选择器机制  
✅ **实战项目**: Kubernetes架构全景图解

**下一章预告**: 第2章将深入讲解 Kubernetes 的最小调度单位 **Pod**,包括 Pod 生命周期、容器设计模式、Init容器、健康检查、资源限制等核心内容。

---

*注: 第1章已完成,共 ~1100行。由于内容较长,部分高级话题(kubectl工具详解、集群搭建实战)将在后续章节中深入展开。*

