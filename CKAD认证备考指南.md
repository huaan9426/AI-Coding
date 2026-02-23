# CKAD认证备考指南

**Certified Kubernetes Application Developer**

**副标题**: 基于《K8S上卷》的完整备考方案
**目标**: 2-3周通过CKAD认证考试
**前置要求**: 已完成《K8S上卷-核心原理与基础实战》学习

---

## 📊 备考进度追踪

- **上卷覆盖率**: 89% ✅
- **需补充内容**: 11%
- **预计学习时间**: 2-3周
- **推荐练习时间**: 每天2-3小时实操

---

# 第1部分：CKAD考试概述

## 1.1 考试基本信息

### 考试详情

| 项目 | 详情 |
|------|------|
| **考试名称** | Certified Kubernetes Application Developer (CKAD) |
| **认证机构** | Cloud Native Computing Foundation (CNCF) |
| **考试时长** | 2小时 |
| **题目数量** | 15-20道实操题 |
| **及格分数** | 66% |
| **考试形式** | 在线远程监考 + 真实K8S环境实操 |
| **Kubernetes版本** | 1.29+ |
| **考试费用** | $395 USD（含一次免费重考） |
| **证书有效期** | 3年 |
| **前置要求** | 无 |

### 考试环境

```
考试环境配置：
┌─────────────────────────────────────────────┐
│  浏览器: Chrome/Chromium                     │
│  ├─ 远程桌面连接到考试环境                   │
│  └─ 监考软件（摄像头+屏幕共享）              │
├─────────────────────────────────────────────┤
│  考试终端: Ubuntu 20.04 LTS                  │
│  ├─ kubectl (预装)                          │
│  ├─ vim/nano (文本编辑器)                   │
│  ├─ tmux (终端复用器)                       │
│  └─ 6-8个K8S集群（不同题目使用不同集群）     │
├─────────────────────────────────────────────┤
│  允许访问的文档:                             │
│  ├─ https://kubernetes.io/docs/             │
│  ├─ https://kubernetes.io/blog/             │
│  └─ https://helm.sh/docs/                   │
└─────────────────────────────────────────────┘

```

### 考试注意事项

**✅ 允许的操作**:
- 使用kubectl命令行工具
- 查看官方文档（kubernetes.io、helm.sh）
- 使用vim/nano编辑器
- 复制粘贴YAML模板
- 使用kubectl explain查看资源定义

**❌ 禁止的操作**:
- 使用第三方网站（Stack Overflow、GitHub等）
- 使用AI助手（ChatGPT、Claude等）
- 与他人交流
- 使用手机或第二台电脑
- 离开摄像头视野

---

## 1.2 考试大纲详解

### 考试领域权重分布

```
CKAD考试大纲（5大领域）:
┌────────────────────────────────────────────────┐
│  1. Application Design and Build (20%)        │
│     ├─ 定义、构建和修改容器镜像                 │
│     ├─ 理解Jobs和CronJobs                     │
│     ├─ 理解多容器Pod设计模式                   │
│     └─ 使用持久卷和临时卷                      │
├────────────────────────────────────────────────┤
│  2. Application Deployment (20%)              │
│     ├─ 使用K8S原语实现部署策略                 │
│     ├─ 理解Deployments和滚动更新               │
│     └─ 使用Helm管理应用                       │
├────────────────────────────────────────────────┤
│  3. Application Observability (15%)           │
│     ├─ 理解API弃用                            │
│     ├─ 实现探针和健康检查                      │
│     ├─ 使用内置CLI工具监控应用                 │
│     ├─ 使用日志                               │
│     └─ 调试应用                               │
├────────────────────────────────────────────────┤
│  4. Application Environment, Configuration    │
│     and Security (25%)                        │
│     ├─ 发现和使用CRD                          │
│     ├─ 理解认证、授权和准入控制                │
│     ├─ 理解和定义资源需求、限制和配额          │
│     ├─ 理解ConfigMaps和Secrets                │
│     ├─ 理解ServiceAccounts                    │
│     └─ 理解SecurityContexts                   │
├────────────────────────────────────────────────┤
│  5. Services and Networking (20%)             │
│     ├─ 演示对NetworkPolicies的基本理解         │
│     ├─ 提供和排查对应用的访问                  │
│     └─ 使用Ingress规则暴露应用                 │
└────────────────────────────────────────────────┘
```

### 上卷内容覆盖情况

| 考试领域 | 权重 | 上卷覆盖率 | 对应章节 | 状态 |
|---------|------|-----------|---------|------|
| **Application Design and Build** | 20% | 90% | 第2章、第5章 | ✅ 优秀 |
| **Application Deployment** | 20% | 85% | 第3章、第10章、第12章 | ✅ 良好 |
| **Application Observability** | 15% | 95% | 第2章、第9章、第11章 | ✅ 优秀 |
| **Environment & Configuration** | 25% | 85% | 第6章、第7章、第8章 | ✅ 良好 |
| **Services and Networking** | 20% | 90% | 第4章 | ✅ 优秀 |
| **总体覆盖率** | 100% | **89%** | 全书 | ✅ 良好 |

---

## 1.3 考试环境与技巧

### kubectl命令速度优化

**1. 配置命令别名**

```bash
# 考试开始后立即执行
alias k=kubectl
alias kgp='kubectl get pods'
alias kgd='kubectl get deploy'
alias kgs='kubectl get svc'
alias kd='kubectl describe'
alias kdel='kubectl delete'
alias kaf='kubectl apply -f'
alias kdf='kubectl delete -f'

# 设置默认命名空间（根据题目要求）
kubectl config set-context --current --namespace=<namespace>

# 启用kubectl自动补全
source <(kubectl completion bash)
complete -F __start_kubectl k
```

**2. vim编辑器优化**

```bash
# 在~/.vimrc中添加
cat >> ~/.vimrc << EOF
set nu                  " 显示行号
set expandtab           " Tab转空格
set tabstop=2           " Tab宽度
set shiftwidth=2        " 缩进宽度
set autoindent          " 自动缩进
set paste               " 粘贴模式
EOF
```

**3. 快速生成YAML模板**

```bash
# 生成Pod YAML（不创建）
kubectl run nginx --image=nginx --dry-run=client -o yaml > pod.yaml

# 生成Deployment YAML
kubectl create deployment nginx --image=nginx --replicas=3 --dry-run=client -o yaml > deploy.yaml

# 生成Service YAML
kubectl expose deployment nginx --port=80 --target-port=80 --type=ClusterIP --dry-run=client -o yaml > svc.yaml

# 生成Job YAML
kubectl create job test-job --image=busybox --dry-run=client -o yaml > job.yaml

# 生成CronJob YAML
kubectl create cronjob test-cron --image=busybox --schedule="*/5 * * * *" --dry-run=client -o yaml > cronjob.yaml

# 生成ConfigMap YAML
kubectl create configmap my-config --from-literal=key1=value1 --dry-run=client -o yaml > cm.yaml

# 生成Secret YAML
kubectl create secret generic my-secret --from-literal=password=mypass --dry-run=client -o yaml > secret.yaml
```

### 时间管理策略

```
考试时间分配（2小时 = 120分钟）:
┌────────────────────────────────────────┐
│  前5分钟: 环境准备                      │
│  ├─ 配置别名和自动补全                  │
│  ├─ 测试kubectl连接                    │
│  └─ 浏览所有题目，标记难度              │
├────────────────────────────────────────┤
│  前90分钟: 答题（按难度顺序）           │
│  ├─ 简单题（5-10分钟/题）: 40分钟       │
│  ├─ 中等题（10-15分钟/题）: 30分钟      │
│  └─ 困难题（15-20分钟/题）: 20分钟      │
├────────────────────────────────────────┤
│  最后25分钟: 检查与补救                 │
│  ├─ 验证所有答案（10分钟）              │
│  ├─ 重做跳过的题目（10分钟）            │
│  └─ 最后检查（5分钟）                   │
└────────────────────────────────────────┘

⚠️ 重要原则:
1. 遇到卡壳的题目，先标记跳过
2. 确保简单题全部拿分
3. 每题完成后立即验证（kubectl get/describe）
4. 注意切换正确的集群和命名空间
```

### 常见陷阱与避免方法

| 陷阱 | 后果 | 避免方法 |
|------|------|---------|
| **忘记切换集群** | 在错误集群操作 | 每题开始先执行题目给的切换命令 |
| **忘记切换命名空间** | 资源创建在错误NS | 使用`kubectl config set-context --current --namespace=xxx` |
| **YAML缩进错误** | 资源创建失败 | 使用`kubectl apply -f`立即验证 |
| **资源名称拼写错误** | 找不到资源 | 复制粘贴题目中的名称 |
| **端口号配置错误** | Service无法访问 | 区分port、targetPort、nodePort |
| **标签选择器不匹配** | Service找不到Pod | 确保labels和selector一致 |
| **资源配额单位错误** | 调度失败 | 记住：CPU用m，内存用Mi/Gi |
| **忘记验证答案