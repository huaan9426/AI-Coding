# CKAD补充内容：Helm与Kustomize实战

**目标**: 补充上卷缺失的11%内容，专注于CKAD考试要求

---

## 第1部分：Helm深入实践

### 1.1 Helm基础回顾

Helm是Kubernetes的包管理工具，类似于Linux的apt/yum。

**核心概念**:
- **Chart**: Helm包，包含运行应用所需的所有K8S资源定义
- **Release**: Chart的运行实例
- **Repository**: Chart仓库

### 1.2 Helm Chart结构

```
mychart/
├── Chart.yaml          # Chart元数据
├── values.yaml         # 默认配置值
├── charts/             # 依赖的子Chart
├── templates/          # K8S资源模板
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── _helpers.tpl   # 模板辅助函数
│   └── NOTES.txt      # 安装后提示信息
└── .helmignore        # 忽略文件列表
```

### 1.3 创建自定义Chart

**步骤1: 创建Chart骨架**

```bash
# 创建新Chart
helm create myapp

# 查看生成的文件
tree myapp/
```

**步骤2: 编辑Chart.yaml**

```yaml
# myapp/Chart.yaml
apiVersion: v2
name: myapp
description: A Helm chart for my application
type: application
version: 0.1.0        # Chart版本
appVersion: "1.0"     # 应用版本

# 可选：添加依赖
dependencies:
  - name: mysql
    version: "9.3.4"
    repository: "https://charts.bitnami.com/bitnami"
```

**步骤3: 配置values.yaml**

```yaml
# myapp/values.yaml
replicaCount: 3

image:
  repository: nginx
  pullPolicy: IfNotPresent
  tag: "1.21"

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: true
  className: "nginx"
  hosts:
    - host: myapp.example.com
      paths:
        - path: /
          pathType: Prefix

resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
```

**步骤4: 编写Deployment模板**

```yaml
# myapp/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "myapp.fullname" . }}
  labels:
    {{- include "myapp.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "myapp.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "myapp.selectorLabels" . | nindent 8 }}
    spec:
      containers:
      - name: {{ .Chart.Name }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - name: http
          containerPort: 80
          protocol: TCP
        resources:
          {{- toYaml .Values.resources | nindent 12 }}
```

### 1.4 Helm模板函数

**常用函数**:

```yaml
# 1. 字符串操作
{{ .Values.name | upper }}           # 转大写
{{ .Values.name | lower }}           # 转小写
{{ .Values.name | quote }}           # 添加引号
{{ .Values.name | default "nginx" }} # 默认值

# 2. 条件判断
{{- if .Values.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
...
{{- end }}

# 3. 循环
{{- range .Values.hosts }}
- host: {{ . }}
{{- end }}

# 4. 包含其他模板
{{- include "myapp.labels" . | nindent 4 }}

# 5. 格式化输出
{{- toYaml .Values.resources | nindent 12 }}
{{- toJson .Values.config }}
```

### 1.5 Helm命令实战

```bash
# 1. 验证Chart语法
helm lint myapp/

# 2. 模拟安装（查看生成的YAML）
helm install --dry-run --debug myapp ./myapp

# 3. 安装Chart
helm install myapp-release ./myapp

# 4. 使用自定义values
helm install myapp-release ./myapp -f custom-values.yaml

# 5. 命令行覆盖值
helm install myapp-release ./myapp --set replicaCount=5

# 6. 查看Release
helm list
helm status myapp-release

# 7. 升级Release
helm upgrade myapp-release ./myapp

# 8. 回滚Release
helm rollback myapp-release 1

# 9. 卸载Release
helm uninstall myapp-release

# 10. 查看Release历史
helm history myapp-release
```

### 1.6 CKAD考试中的Helm

**考试可能出现的题型**:

**题目1: 使用Helm安装应用**
```bash
# 添加仓库
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# 搜索Chart
helm search repo nginx

# 安装Chart
helm install my-nginx bitnami/nginx --set service.type=NodePort
```

**题目2: 自定义values安装**
```bash
# 创建custom-values.yaml
cat > custom-values.yaml << EOF
replicaCount: 3
service:
  type: LoadBalancer
  port: 8080
EOF

# 使用自定义values安装
helm install my-app bitnami/nginx -f custom-values.yaml
```

**题目3: 升级和回滚**
```bash
# 升级应用
helm upgrade my-app bitnami/nginx --set replicaCount=5

# 查看历史
helm history my-app

# 回滚到上一版本
helm rollback my-app

# 回滚到指定版本
helm rollback my-app 2
```

---

## 第2部分：Kustomize实战

### 2.1 Kustomize简介

Kustomize是Kubernetes原生的配置管理工具，无需模板，通过overlay方式管理多环境配置。

**核心概念**:
- **Base**: 基础配置
- **Overlay**: 覆盖层（dev/staging/prod）
- **Patch**: 补丁文件

### 2.2 Kustomize目录结构

```
kustomize-demo/
├── base/                    # 基础配置
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   └── service.yaml
└── overlays/                # 环境特定配置
    ├── dev/
    │   ├── kustomization.yaml
    │   └── replica-patch.yaml
    ├── staging/
    │   └── kustomization.yaml
    └── prod/
        ├── kustomization.yaml
        └── resource-patch.yaml
```

### 2.3 创建Base配置

**base/deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: nginx:1.21
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
```

**base/service.yaml**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
```

**base/kustomization.yaml**:
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
  - service.yaml

commonLabels:
  app: myapp
  managed-by: kustomize
```

### 2.4 创建Overlay配置

**overlays/dev/kustomization.yaml**:
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: dev

bases:
  - ../../base

namePrefix: dev-

commonLabels:
  environment: dev

replicas:
  - name: myapp
    count: 2

images:
  - name: nginx
    newTag: 1.21-alpine
```

**overlays/prod/kustomization.yaml**:
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: prod

bases:
  - ../../base

namePrefix: prod-

commonLabels:
  environment: prod

replicas:
  - name: myapp
    count: 5

images:
  - name: nginx
    newTag: 1.21

patchesStrategicMerge:
  - resource-patch.yaml
```

**overlays/prod/resource-patch.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  template:
    spec:
      containers:
      - name: myapp
        resources:
          requests:
            cpu: 200m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
```

### 2.5 Kustomize命令

```bash
# 1. 查看生成的YAML（不应用）
kubectl kustomize overlays/dev/

# 2. 应用配置
kubectl apply -k overlays/dev/

# 3. 删除资源
kubectl delete -k overlays/dev/

# 4. 查看差异
kubectl diff -k overlays/prod/

# 5. 构建并保存到文件
kubectl kustomize overlays/prod/ > prod-manifest.yaml
```

### 2.6 Kustomize高级特性

**1. ConfigMap生成器**:
```yaml
# kustomization.yaml
configMapGenerator:
  - name: app-config
    literals:
      - DB_HOST=mysql.default.svc
      - DB_PORT=3306
    files:
      - application.properties
```

**2. Secret生成器**:
```yaml
secretGenerator:
  - name: db-secret
    literals:
      - username=admin
      - password=secret123
```

**3. JSON Patch**:
```yaml
patchesJson6902:
  - target:
      group: apps
      version: v1
      kind: Deployment
      name: myapp
    patch: |-
      - op: replace
        path: /spec/replicas
        value: 3
```

### 2.7 CKAD考试中的Kustomize

**题目1: 使用Kustomize部署应用**
```bash
# 查看生成的配置
kubectl kustomize ./overlays/dev

# 应用配置
kubectl apply -k ./overlays/dev

# 验证
kubectl get all -n dev
```

**题目2: 修改Kustomize配置**
```bash
# 修改副本数
cat >> overlays/dev/kustomization.yaml << EOF
replicas:
  - name: myapp
    count: 3
EOF

# 应用更改
kubectl apply -k ./overlays/dev
```

---

## 第3部分：多阶段构建优化

### 3.1 为什么需要多阶段构建

**单阶段构建的问题**:
```dockerfile
FROM golang:1.21
WORKDIR /app
COPY . .
RUN go build -o myapp
CMD ["./myapp"]

# 问题：镜像包含完整的Go编译环境，体积达到800MB+
```

**多阶段构建的优势**:
- ✅ 大幅减小镜像体积（从800MB降到10MB）
- ✅ 提高安全性（最终镜像不包含编译工具）
- ✅ 加快部署速度

### 3.2 多阶段构建示例

**Go应用**:
```dockerfile
# 阶段1: 构建
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o myapp .

# 阶段2: 运行
FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/myapp .
EXPOSE 8080
CMD ["./myapp"]

# 结果：镜像从800MB降到15MB
```

**Node.js应用**:
```dockerfile
# 阶段1: 构建
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# 阶段2: 运行
FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

**Java应用**:
```dockerfile
# 阶段1: 构建
FROM maven:3.8-openjdk-17 AS builder
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src ./src
RUN mvn package -DskipTests

# 阶段2: 运行
FROM openjdk:17-jre-slim
WORKDIR /app
COPY --from=builder /app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

### 3.3 镜像优化最佳实践

```dockerfile
# 1. 使用小体积基础镜像
FROM alpine:latest          # 5MB
FROM scratch                # 0MB（仅适用于静态编译）
FROM distroless/static      # Google的最小镜像

# 2. 合并RUN命令减少层数
RUN apt-get update && \
    apt-get install -y package1 package2 && \
    rm -rf /var/lib/apt/lists/*

# 3. 使用.dockerignore
# .dockerignore
.git
node_modules
*.md
.env

# 4. 利用构建缓存
COPY package.json package-lock.json ./
RUN npm install
COPY . .

# 5. 使用非root用户
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser
USER appuser
```

---

## 第4部分：CRD使用实战

### 4.1 什么是CRD

CRD (Custom Resource Definition) 允许你扩展Kubernetes API，创建自定义资源类型。

**常见的CRD示例**:
- Prometheus的`ServiceMonitor`
- Istio的`VirtualService`
- Cert-Manager的`Certificate`

### 4.2 查看和使用CRD

```bash
# 1. 列出所有CRD
kubectl get crd

# 2. 查看特定CRD详情
kubectl describe crd servicemonitors.monitoring.coreos.com

# 3. 查看CRD的API版本
kubectl api-resources | grep monitoring

# 4. 使用kubectl explain查看CRD字段
kubectl explain servicemonitor
kubectl explain servicemonitor.spec
```

### 4.3 使用Prometheus ServiceMonitor

**安装Prometheus Operator**:
```bash
# 使用Helm安装
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack
```

**创建ServiceMonitor**:
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: myapp-monitor
  namespace: default
spec:
  selector:
    matchLabels:
      app: myapp
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

### 4.4 使用Cert-Manager Certificate

**安装Cert-Manager**:
```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

**创建Certificate**:
```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: myapp-tls
  namespace: default
spec:
  secretName: myapp-tls-secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - myapp.example.com
```

### 4.5 CKAD考试中的CRD

**考试重点**:
- ✅ 能够列出和查看CRD
- ✅ 能够创建和管理自定义资源
- ✅ 理解CRD与普通资源的关系
- ❌ 不需要编写CRD定义（那是CKA/CKS的内容）

**常见题目**:
```bash
# 题目：创建一个ServiceMonitor监控myapp服务
kubectl apply -f - <<EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: myapp-monitor
spec:
  selector:
    matchLabels:
      app: myapp
  endpoints:
  - port: web
    interval: 30s
EOF

# 验证
kubectl get servicemonitor
kubectl describe servicemonitor myapp-monitor
```

---

## 第5部分：CKAD快速参考

### 5.1 kubectl命令速查

```bash
# Helm
helm install <release> <chart>
helm upgrade <release> <chart>
helm rollback <release> <revision>
helm uninstall <release>
helm list

# Kustomize
kubectl apply -k <directory>
kubectl kustomize <directory>
kubectl delete -k <directory>

# CRD
kubectl get crd
kubectl get <crd-name>
kubectl describe crd <crd-name>
kubectl explain <crd-name>

# 多阶段构建
docker build -t myapp:v1 .
docker images
docker history myapp:v1
```

### 5.2 考试检查清单

**考前准备**:
- [ ] 配置kubectl别名和自动补全
- [ ] 熟悉vim/nano编辑器
- [ ] 记住常用kubectl命令
- [ ] 练习快速生成YAML模板

**考试中**:
- [ ] 每题开始先切换集群和命名空间
- [ ] 使用--dry-run生成YAML模板
- [ ] 立即验证每个答案
- [ ] 遇到困难先跳过，标记后续回来
- [ ] 预留时间检查所有答案

**重点领域**:
- [ ] Pod设计模式（Sidecar/Init/Ambassador）
- [ ] Deployment滚动更新和回滚
- [ ] Service和Ingress配置
- [ ] ConfigMap和Secret使用
- [ ] 资源限制和QoS
- [ ] 健康检查（Liveness/Readiness/Startup）
- [ ] 持久卷和临时卷
- [ ] NetworkPolicy基础
- [ ] Helm基本操作
- [ ] Kustomize基本使用

---

**祝你CKAD考试顺利通过！** 🎉
