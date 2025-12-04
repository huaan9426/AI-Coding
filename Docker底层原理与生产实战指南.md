# Docker 底层原理与生产实战指南

> **硬核技术文档 · 从底层到实战的完整知识体系**
>
> 适用人群：DevOps工程师、后端开发、系统架构师、运维工程师
>
> 目标：掌握Docker底层原理、容器化最佳实践、生产环境部署与优化

---

## 📚 文档结构

### 第一部分：底层原理与核心技术（1-5章）
- 第1章：Linux容器技术基础
- 第2章：Docker架构与组件
- 第3章：镜像原理与存储驱动
- 第4章：网络原理与实现
- 第5章：资源隔离与限制

### 第二部分：镜像构建与优化（6-8章）
- 第6章：Dockerfile最佳实践
- 第7章：多阶段构建与优化
- 第8章：镜像安全与扫描

### 第三部分：容器运行时与编排（9-12章）
- 第9章：容器生命周期管理
- 第10章：数据持久化与卷管理
- 第11章：容器编排基础
- 第12章：Docker Compose实战

### 第四部分：生产环境部署（13-16章）
- 第13章：高可用架构设计
- 第14章：监控与日志管理
- 第15章：CI/CD集成
- 第16章：安全加固与合规

### 第五部分：性能优化与故障排查（17-19章）
- 第17章：性能调优实战
- 第18章：故障排查技巧
- 第19章：生产环境最佳实践

---

## 第一部分：底层原理与核心技术

---

## 第 1 章：Linux容器技术基础

### 1.1 容器技术的本质

#### 1.1.1 容器 vs 虚拟机

**虚拟机架构**：
```
┌─────────────────────────────────────────┐
│          Application (App)              │
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │  Bins/   │  │  Bins/   │  │ Bins/  ││
│  │  Libs    │  │  Libs    │  │ Libs   ││
│  └──────────┘  └──────────┘  └────────┘│
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │ Guest OS │  │ Guest OS │  │Guest OS││
│  └──────────┘  └──────────┘  └────────┘│
│         Hypervisor (VMware/KVM)         │
│              Host OS                     │
│            Infrastructure                │
└─────────────────────────────────────────┘
```

**容器架构**：
```
┌─────────────────────────────────────────┐
│          Application (App)              │
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │  Bins/   │  │  Bins/   │  │ Bins/  ││
│  │  Libs    │  │  Libs    │  │ Libs   ││
│  └──────────┘  └──────────┘  └────────┘│
│      Docker Engine (Container Runtime)  │
│              Host OS (Linux)            │
│            Infrastructure                │
└─────────────────────────────────────────────┘
```

**核心区别**：

| 特性 | 虚拟机 | 容器 |
|-----|-------|------|
| 隔离级别 | 硬件级别 | 进程级别 |
| 启动时间 | 分钟级 | 秒级 |
| 资源占用 | GB级内存 | MB级内存 |
| 性能损耗 | 5-10% | <2% |
| 镜像大小 | GB级 | MB级 |
| 操作系统 | 完整OS | 共享宿主机内核 |

---

### 1.2 Linux Namespace（命名空间）

#### 1.2.1 Namespace 类型详解

**7种Namespace**：

| Namespace | 系统调用参数 | 隔离内容 | 内核版本 |
|-----------|-------------|---------|---------|
| **Mount** | CLONE_NEWNS | 文件系统挂载点 | 2.4.19 |
| **UTS** | CLONE_NEWUTS | 主机名和域名 | 2.6.19 |
| **IPC** | CLONE_NEWIPC | 进程间通信 | 2.6.19 |
| **PID** | CLONE_NEWPID | 进程ID | 2.6.24 |
| **Network** | CLONE_NEWNET | 网络栈 | 2.6.29 |
| **User** | CLONE_NEWUSER | 用户和用户组 | 3.8 |
| **Cgroup** | CLONE_NEWCGROUP | Cgroup根目录 | 4.6 |

---

#### 1.2.2 PID Namespace 实战

**查看容器PID隔离**：
```bash
# 宿主机视角
$ docker run -d --name nginx nginx:alpine
$ docker top nginx
UID    PID     PPID    ...    CMD
root   12345   12320   ...    nginx: master process

# 容器内视角
$ docker exec nginx ps aux
PID   USER     COMMAND
1     root     nginx: master process    # 在容器内PID=1
7     nginx    nginx: worker process

# 查看PID namespace
$ docker inspect nginx | grep Pid
"Pid": 12345,

$ ls -l /proc/12345/ns/
total 0
lrwxrwxrwx 1 root root 0 ... cgroup -> 'cgroup:[4026532454]'
lrwxrwxrwx 1 root root 0 ... ipc -> 'ipc:[4026532452]'
lrwxrwxrwx 1 root root 0 ... mnt -> 'mnt:[4026532450]'
lrwxrwxrwx 1 root root 0 ... net -> 'net:[4026532455]'
lrwxrwxrwx 1 root root 0 ... pid -> 'pid:[4026532453]'
lrwxrwxrwx 1 root root 0 ... uts -> 'uts:[4026532451]'
```

**手动创建PID Namespace（C语言示例）**：
```c
#define _GNU_SOURCE
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <unistd.h>

static char child_stack[1048576];

static int child_fn() {
    printf("容器内 PID: %d\n", getpid());  // 输出 1
    printf("容器内 PPID: %d\n", getppid()); // 输出 0

    // 执行shell
    char *const args[] = {"/bin/bash", NULL};
    execvp(args[0], args);
    return 1;
}

int main() {
    printf("宿主机 PID: %d\n", getpid());

    // 创建新的PID namespace
    int child_pid = clone(child_fn,
                         child_stack + sizeof(child_stack),
                         CLONE_NEWPID | SIGCHLD,
                         NULL);

    waitpid(child_pid, NULL, 0);
    return 0;
}

// 编译运行:
// gcc -o pid_namespace pid_namespace.c
// sudo ./pid_namespace
```

---

#### 1.2.3 Network Namespace 实战

**手动创建网络命名空间**：
```bash
# 创建network namespace
$ sudo ip netns add container1
$ sudo ip netns list
container1

# 在namespace内执行命令
$ sudo ip netns exec container1 ip addr
1: lo: <LOOPBACK> mtu 65536 qdisc noop state DOWN
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00

# 创建veth pair（虚拟网卡对）
$ sudo ip link add veth0 type veth peer name veth1

# 将veth1移到container1命名空间
$ sudo ip link set veth1 netns container1

# 配置IP地址
$ sudo ip addr add 10.0.0.1/24 dev veth0
$ sudo ip link set veth0 up

$ sudo ip netns exec container1 ip addr add 10.0.0.2/24 dev veth1
$ sudo ip netns exec container1 ip link set veth1 up
$ sudo ip netns exec container1 ip link set lo up

# 测试连通性
$ ping -c 2 10.0.0.2
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.050 ms
```

**Docker网络命名空间查看**：
```bash
# 查看容器网络namespace
$ docker inspect nginx | grep SandboxKey
"SandboxKey": "/var/run/docker/netns/abc123def456",

# 列出所有网络命名空间
$ sudo ls -l /var/run/docker/netns/
-r--r--r-- 1 root root 0 ... abc123def456

# 进入容器网络命名空间
$ sudo nsenter --net=/var/run/docker/netns/abc123def456 ip addr
```

---

#### 1.2.4 Mount Namespace 实战

**隔离文件系统挂载点**：
```bash
# 创建mount namespace
$ sudo unshare --mount --fork /bin/bash

# 在新namespace中挂载
$ mount -t tmpfs tmpfs /mnt
$ df -h /mnt
Filesystem      Size  Used Avail Use% Mounted on
tmpfs           1.0G     0  1.0G   0% /mnt

# 在宿主机检查（看不到这个挂载点）
$ df -h /mnt
```

**Docker容器挂载隔离验证**：
```bash
# 查看容器挂载点
$ docker exec nginx cat /proc/mounts
overlay / overlay rw,relatime,lowerdir=...,upperdir=...,workdir=... 0 0
proc /proc proc rw,nosuid,nodev,noexec,relatime 0 0
tmpfs /dev tmpfs rw,nosuid,size=65536k,mode=755 0 0

# 宿主机看不到容器内的挂载点
$ mount | grep overlay
overlay on /var/lib/docker/overlay2/.../merged type overlay (rw,...)
```

---

### 1.3 Linux Cgroups（控制组）

#### 1.3.1 Cgroups 子系统详解

**12个子系统（Subsystems）**：

| 子系统 | 功能 | 常用限制参数 |
|--------|------|-------------|
| **cpu** | CPU时间分配 | cpu.shares, cpu.cfs_quota_us |
| **cpuacct** | CPU使用统计 | cpuacct.usage, cpuacct.stat |
| **cpuset** | CPU核心绑定 | cpuset.cpus, cpuset.mems |
| **memory** | 内存限制 | memory.limit_in_bytes, memory.soft_limit_in_bytes |
| **blkio** | 块设备IO限制 | blkio.weight, blkio.throttle.read_bps_device |
| **devices** | 设备访问控制 | devices.allow, devices.deny |
| **net_cls** | 网络分类标记 | net_cls.classid |
| **net_prio** | 网络优先级 | net_prio.ifpriomap |
| **freezer** | 冻结/恢复进程 | freezer.state |
| **pids** | 进程数限制 | pids.max |
| **hugetlb** | 大页内存限制 | hugetlb.*.limit_in_bytes |
| **perf_event** | 性能监控 | perf_event.* |

---

#### 1.3.2 Cgroups v1 vs v2

**架构对比**：

```
Cgroups v1（层级架构）:
/sys/fs/cgroup/
├── cpu/
│   └── docker/
│       └── <container-id>/
│           ├── cpu.shares
│           └── cpu.cfs_quota_us
├── memory/
│   └── docker/
│       └── <container-id>/
│           └── memory.limit_in_bytes
└── blkio/
    └── docker/
        └── <container-id>/

Cgroups v2（统一层级）:
/sys/fs/cgroup/
└── system.slice/
    └── docker-<container-id>.scope/
        ├── cpu.max
        ├── memory.max
        ├── io.max
        └── cgroup.controllers
```

**主要改进**：
1. **统一层级**: 所有控制器在同一层级
2. **线程支持**: 更好的线程级别控制
3. **压力感知**: Pressure Stall Information (PSI)
4. **简化接口**: 更一致的API设计

---

#### 1.3.3 CPU限制实战

**方式1：CPU份额（cpu.shares）**：
```bash
# 创建两个容器，CPU份额比例 2:1
$ docker run -d --name cpu_high --cpu-shares 2048 stress --cpu 4
$ docker run -d --name cpu_low --cpu-shares 1024 stress --cpu 4

# 查看CPU使用率
$ docker stats --no-stream
CONTAINER   CPU %     MEM USAGE / LIMIT
cpu_high    66.67%    ...          # 获得 2/3 CPU
cpu_low     33.33%    ...          # 获得 1/3 CPU

# 查看cgroup配置
$ cat /sys/fs/cgroup/cpu/docker/<container-id>/cpu.shares
2048
```

**方式2：CPU配额（cpu.cfs_quota_us + cpu.cfs_period_us）**：
```bash
# 限制容器只能使用0.5个CPU核心
$ docker run -d --name cpu_limited \
    --cpus="0.5" \
    stress --cpu 4

# 等价于：
# --cpu-period=100000 --cpu-quota=50000

# 查看cgroup配置
$ cat /sys/fs/cgroup/cpu/docker/<container-id>/cpu.cfs_period_us
100000

$ cat /sys/fs/cgroup/cpu/docker/<container-id>/cpu.cfs_quota_us
50000

# CPU使用率不会超过50%
$ docker stats cpu_limited
CONTAINER      CPU %
cpu_limited    49.87%
```

**方式3：CPU核心绑定（cpuset）**：
```bash
# 绑定到CPU核心0和1
$ docker run -d --name cpu_pinned \
    --cpuset-cpus="0,1" \
    nginx

# 查看绑定的核心
$ cat /sys/fs/cgroup/cpuset/docker/<container-id>/cpuset.cpus
0-1

# 验证进程CPU亲和性
$ docker exec cpu_pinned taskset -cp 1
pid 1's current affinity list: 0,1
```

---

#### 1.3.4 内存限制实战

**基础内存限制**：
```bash
# 限制内存512MB，swap也是512MB
$ docker run -d --name mem_limited \
    --memory="512m" \
    --memory-swap="1g" \
    nginx

# 查看内存限制
$ cat /sys/fs/cgroup/memory/docker/<container-id>/memory.limit_in_bytes
536870912  # 512MB

$ cat /sys/fs/cgroup/memory/docker/<container-id>/memory.memsw.limit_in_bytes
1073741824  # 1GB (内存+swap)

# 查看实时内存使用
$ cat /sys/fs/cgroup/memory/docker/<container-id>/memory.usage_in_bytes
$ cat /sys/fs/cgroup/memory/docker/<container-id>/memory.stat
```

**内存预留（Reservation）**：
```bash
# 软限制：正常情况下使用256MB，压力大时可以到512MB
$ docker run -d --name mem_reserved \
    --memory="512m" \
    --memory-reservation="256m" \
    nginx

# 查看预留值
$ cat /sys/fs/cgroup/memory/docker/<container-id>/memory.soft_limit_in_bytes
268435456  # 256MB
```

**OOM（Out Of Memory）行为控制**：
```bash
# 禁用OOM Killer（容器被杀死）
$ docker run -d --name no_oom_kill \
    --memory="512m" \
    --oom-kill-disable \
    nginx

# ⚠️ 危险：如果没有swap，进程会挂起而不是被杀死

# 设置OOM优先级（-1000到1000，越小越不容易被杀）
$ docker run -d --name oom_low_priority \
    --memory="512m" \
    --oom-score-adj=500 \
    nginx

# 查看OOM分数
$ cat /proc/$(docker inspect -f '{{.State.Pid}}' oom_low_priority)/oom_score_adj
500
```

**内存压力测试**：
```bash
# 创建内存压力测试容器
$ docker run -it --rm \
    --memory="512m" \
    --memory-swap="512m" \
    progrium/stress \
    --vm 1 --vm-bytes 600M --vm-hang 0

# 观察OOM事件
$ dmesg | tail
[12345.678] Memory cgroup out of memory: Kill process 12345 (stress) score 1000
[12345.679] Killed process 12345 (stress) total-vm:614400kB

# 监控内存事件
$ cat /sys/fs/cgroup/memory/docker/<container-id>/memory.oom_control
oom_kill_disable 0
under_oom 0
oom_kill 1
```

---

#### 1.3.5 块设备IO限制实战

**读写速率限制（bps）**：
```bash
# 限制读速率10MB/s，写速率5MB/s
$ docker run -it --rm \
    --device-read-bps /dev/sda:10mb \
    --device-write-bps /dev/sda:5mb \
    ubuntu:20.04 bash

# 测试读速率
$ dd if=/dev/zero of=/tmp/test bs=1M count=100 oflag=direct
100+0 records in
100+0 records out
104857600 bytes (105 MB) copied, 20.0 s, 5.2 MB/s  # 符合限制

# 查看cgroup配置
$ cat /sys/fs/cgroup/blkio/docker/<container-id>/blkio.throttle.read_bps_device
8:0 10485760  # 主设备号:次设备号 速率(bytes/s)
```

**IOPS限制**：
```bash
# 限制随机读IOPS=100，写IOPS=50
$ docker run -it --rm \
    --device-read-iops /dev/sda:100 \
    --device-write-iops /dev/sda:50 \
    ubuntu:20.04 bash

# 测试IOPS
$ fio --name=randread --ioengine=libaio --rw=randread --bs=4k --size=1G --numjobs=1 --iodepth=32
...
read: IOPS=99, BW=396KiB/s  # 符合限制
```

**IO权重（blkio.weight）**：
```bash
# 创建两个容器，IO权重 500:250（2:1）
$ docker run -d --name io_high --blkio-weight 500 ...
$ docker run -d --name io_low --blkio-weight 250 ...

# 查看权重
$ cat /sys/fs/cgroup/blkio/docker/<container-id>/blkio.weight
500
```

---

#### 1.3.6 进程数限制（PID限制）

```bash
# 限制容器最多创建100个进程
$ docker run -d --name pid_limited \
    --pids-limit 100 \
    nginx

# 查看限制
$ cat /sys/fs/cgroup/pids/docker/<container-id>/pids.max
100

# 查看当前进程数
$ cat /sys/fs/cgroup/pids/docker/<container-id>/pids.current
2

# 测试fork炸弹防护
$ docker run -it --rm --pids-limit 10 ubuntu:20.04 bash
root@container:/# :(){ :|:& };:
bash: fork: retry: Resource temporarily unavailable
# 容器被保护，不会影响宿主机
```

---

### 1.4 UnionFS（联合文件系统）

#### 1.4.1 UnionFS 原理

**分层文件系统示意图**：
```
Docker镜像分层结构:
┌─────────────────────────────────┐
│  Container Layer (Read-Write)   │  ← 可写层（容器运行时修改）
├─────────────────────────────────┤
│  Image Layer 4 (Read-Only)      │  ← CMD ["nginx"]
├─────────────────────────────────┤
│  Image Layer 3 (Read-Only)      │  ← COPY nginx.conf /etc/nginx/
├─────────────────────────────────┤
│  Image Layer 2 (Read-Only)      │  ← RUN apt-get install nginx
├─────────────────────────────────┤
│  Image Layer 1 (Read-Only)      │  ← FROM ubuntu:20.04
└─────────────────────────────────┘
         ↓
    UnionFS 合并
         ↓
┌─────────────────────────────────┐
│   Unified View (Container Root) │  ← 容器看到的完整文件系统
└─────────────────────────────────┘
```

**写时复制（Copy-on-Write, COW）**：
```bash
# 1. 容器启动时，所有层只读
# 2. 修改文件时：
#    - 从只读层复制文件到可写层
#    - 在可写层修改
#    - 原始层保持不变

# 示例
$ docker run -d --name test nginx
$ docker exec test bash -c "echo 'modified' > /etc/nginx/nginx.conf"

# 查看差异（只有修改的文件在可写层）
$ docker diff test
C /etc
C /etc/nginx
C /etc/nginx/nginx.conf
```

---

#### 1.4.2 存储驱动类型

**主流存储驱动对比**：

| 存储驱动 | 文件系统 | 性能 | 稳定性 | 使用场景 | 内核要求 |
|---------|---------|------|-------|---------|---------|
| **overlay2** | OverlayFS | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 生产推荐 | ≥4.0 |
| **aufs** | AUFS | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 旧版Ubuntu | <4.0 |
| **devicemapper** | LVM | ⭐⭐⭐ | ⭐⭐⭐ | RHEL 7.x | 任意 |
| **btrfs** | Btrfs | ⭐⭐⭐ | ⭐⭐⭐ | 实验性 | 任意 |
| **zfs** | ZFS | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 高级特性 | 任意 |
| **vfs** | 无 | ⭐ | ⭐⭐⭐⭐⭐ | 测试/调试 | 任意 |

---

#### 1.4.3 Overlay2 深度解析（生产推荐）

**Overlay2 文件系统结构**：
```bash
# 查看当前存储驱动
$ docker info | grep "Storage Driver"
Storage Driver: overlay2

# Overlay2目录结构
/var/lib/docker/overlay2/
├── <layer-id>/
│   ├── diff/           # 该层的实际内容
│   ├── link            # 短符号链接名
│   ├── lower           # 指向下层的link
│   ├── merged/         # 合并后的视图（容器看到的）
│   └── work/           # OverlayFS工作目录
└── l/                  # 所有层的短链接

# 查看容器使用的层
$ docker inspect nginx | grep -A 20 GraphDriver
"GraphDriver": {
    "Data": {
        "LowerDir": "/var/lib/docker/overlay2/abc.../diff:/var/lib/docker/overlay2/def.../diff",
        "MergedDir": "/var/lib/docker/overlay2/xyz.../merged",
        "UpperDir": "/var/lib/docker/overlay2/xyz.../diff",
        "WorkDir": "/var/lib/docker/overlay2/xyz.../work"
    },
    "Name": "overlay2"
}
```

**Overlay2 挂载验证**：
```bash
# 查看overlay挂载
$ mount | grep overlay
overlay on /var/lib/docker/overlay2/xyz.../merged type overlay (rw,relatime,
    lowerdir=/var/lib/docker/overlay2/l/ABC:/var/lib/docker/overlay2/l/DEF,
    upperdir=/var/lib/docker/overlay2/xyz.../diff,
    workdir=/var/lib/docker/overlay2/xyz.../work)

# lowerdir: 只读层（镜像层）
# upperdir: 可写层（容器层）
# merged: 合并视图（容器根文件系统）
```

**Overlay2 inode限制问题**：
```bash
# 查看inode使用情况
$ df -i
Filesystem      Inodes  IUsed   IFree IUse% Mounted on
/dev/sda1      6553600  500000  6053600   8% /

# 问题：overlay2每层使用独立inode，可能耗尽
# 解决方案：
# 1. 减少镜像层数（多阶段构建）
# 2. 定期清理未使用的镜像/容器
# 3. 使用xfs文件系统（支持动态inode分配）

# 清理未使用资源
$ docker system prune -a --volumes
```

---

#### 1.4.4 存储驱动性能对比

**性能测试脚本**：
```bash
#!/bin/bash
# benchmark_storage_driver.sh

test_driver() {
    DRIVER=$1

    # 配置Docker使用指定存储驱动
    echo "Testing $DRIVER..."

    # 创建测试容器
    docker run --rm -v /tmp/test:/test ubuntu:20.04 bash -c "
        # 顺序写测试
        dd if=/dev/zero of=/test/testfile bs=1M count=1000 conv=fdatasync

        # 随机写测试
        fio --name=randwrite --ioengine=libaio --rw=randwrite \
            --bs=4k --size=1G --numjobs=4 --iodepth=32 \
            --filename=/test/fiotest

        # 元数据操作测试（创建文件）
        time for i in {1..10000}; do touch /test/file_\$i; done
    "
}

# 测试不同存储驱动
test_driver overlay2
test_driver devicemapper
test_driver aufs
```

**典型性能数据**：

| 操作类型 | overlay2 | aufs | devicemapper |
|---------|----------|------|-------------|
| 顺序读 | 3000 MB/s | 2800 MB/s | 2500 MB/s |
| 顺序写 | 2500 MB/s | 2200 MB/s | 1800 MB/s |
| 随机读IOPS | 50000 | 45000 | 35000 |
| 随机写IOPS | 40000 | 35000 | 25000 |
| 元数据操作 | 快 | 中 | 慢 |
| 内存占用 | 低 | 中 | 高 |

---

### 1.5 容器运行时（Container Runtime）

#### 1.5.1 运行时架构演进

**OCI（Open Container Initiative）标准**：
```
┌─────────────────────────────────────────────────┐
│            Container Orchestration              │
│         (Kubernetes, Docker Swarm, ...)         │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│         High-Level Container Runtime            │
│      (containerd, CRI-O, Docker Engine)         │
└──────────────────┬──────────────────────────────┘
                   │ OCI Runtime Spec
┌──────────────────▼──────────────────────────────┐
│          Low-Level Container Runtime            │
│           (runc, crun, kata, gvisor)            │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│          Linux Kernel (Namespaces, Cgroups)     │
└─────────────────────────────────────────────────┘
```

---

#### 1.5.2 runc 深度解析

**runc 是什么**：
- OCI runtime-spec 的参考实现
- 由 Docker 捐献给 OCI
- 使用Go语言编写
- 直接操作 namespace 和 cgroup

**手动使用 runc 创建容器**：
```bash
# 1. 安装runc
$ sudo apt-get install runc

# 2. 准备rootfs
$ mkdir -p /tmp/mycontainer/rootfs
$ docker export $(docker create ubuntu:20.04) | tar -C /tmp/mycontainer/rootfs -xf -

# 3. 生成OCI配置文件
$ cd /tmp/mycontainer
$ runc spec

# 4. 编辑config.json（可选）
$ cat config.json
{
    "ociVersion": "1.0.2",
    "process": {
        "terminal": true,
        "user": {"uid": 0, "gid": 0},
        "args": ["/bin/bash"],
        "env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
        "cwd": "/",
        ...
    },
    "root": {
        "path": "rootfs",
        "readonly": false
    },
    "hostname": "mycontainer",
    "mounts": [...],
    "linux": {
        "namespaces": [
            {"type": "pid"},
            {"type": "network"},
            {"type": "ipc"},
            {"type": "uts"},
            {"type": "mount"}
        ],
        "resources": {
            "memory": {"limit": 536870912},
            "cpu": {"quota": 50000, "period": 100000}
        }
    }
}

# 5. 运行容器
$ sudo runc run mycontainer
root@mycontainer:/#

# 6. 查看容器（另一个终端）
$ sudo runc list
ID            PID       STATUS    BUNDLE
mycontainer   12345     running   /tmp/mycontainer

# 7. 查看容器状态
$ sudo runc state mycontainer
{
  "ociVersion": "1.0.2",
  "id": "mycontainer",
  "pid": 12345,
  "status": "running",
  "bundle": "/tmp/mycontainer",
  "rootfs": "/tmp/mycontainer/rootfs",
  "created": "2024-01-01T00:00:00.000000000Z"
}
```

---

#### 1.5.3 containerd 架构

**containerd 组件架构**：
```
┌──────────────────────────────────────────────────┐
│               Docker CLI / API                    │
└────────────────────┬─────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────┐
│              dockerd (Docker Daemon)              │
└────────────────────┬─────────────────────────────┘
                     │ gRPC
┌────────────────────▼─────────────────────────────┐
│                 containerd                        │
│  ┌────────────┬──────────────┬────────────────┐ │
│  │  Metadata  │   Snapshots  │   Diff Service │ │
│  │   (boltdb) │   (overlay2) │                │ │
│  └────────────┴──────────────┴────────────────┘ │
│  ┌────────────────────────────────────────────┐ │
│  │        containerd-shim (per container)     │ │
│  │  ┌──────────────────────────────────────┐ │ │
│  │  │          runc (OCI runtime)          │ │ │
│  │  └──────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

**containerd 命令行工具（ctr）**：
```bash
# 列出容器
$ sudo ctr containers list
CONTAINER    IMAGE    RUNTIME

# 列出任务（运行中的容器）
$ sudo ctr tasks list
TASK    PID    STATUS

# 拉取镜像
$ sudo ctr images pull docker.io/library/nginx:alpine

# 运行容器
$ sudo ctr run --rm -t docker.io/library/nginx:alpine my-nginx

# 查看命名空间
$ sudo ctr namespaces list
NAME    LABELS
default
moby    # Docker使用的命名空间
```

---

#### 1.5.4 容器安全运行时

**gVisor（Google）**：
```
┌──────────────────────────────────────┐
│         Application (untrusted)      │
└────────────────┬─────────────────────┘
                 │ syscalls
┌────────────────▼─────────────────────┐
│           Sentry (用户态内核)         │
│  ┌─────────────────────────────────┐ │
│  │   Go实现的部分Linux内核         │ │
│  │   (文件系统、网络栈、内存管理...)  │ │
│  └─────────────────────────────────┘ │
└────────────────┬─────────────────────┘
                 │ 受限syscalls
┌────────────────▼─────────────────────┐
│          Gofer (I/O代理)             │
└────────────────┬─────────────────────┘
                 │
┌────────────────▼─────────────────────┐
│           Linux Kernel               │
└──────────────────────────────────────┘
```

**安装和使用 gVisor**：
```bash
# 安装runsc（gVisor运行时）
$ sudo apt-get update && sudo apt-get install -y apt-transport-https ca-certificates curl gnupg
$ curl -fsSL https://gvisor.dev/archive.key | sudo gpg --dearmor -o /usr/share/keyrings/gvisor-archive-keyring.gpg
$ echo "deb [signed-by=/usr/share/keyrings/gvisor-archive-keyring.gpg] https://storage.googleapis.com/gvisor/releases release main" | sudo tee /etc/apt/sources.list.d/gvisor.list
$ sudo apt-get update && sudo apt-get install -y runsc

# 配置Docker使用gVisor
$ sudo tee /etc/docker/daemon.json <<EOF
{
  "runtimes": {
    "runsc": {
      "path": "/usr/bin/runsc"
    }
  }
}
EOF

$ sudo systemctl restart docker

# 使用gVisor运行容器
$ docker run --runtime=runsc -d nginx

# 验证（容器内syscall被拦截）
$ docker exec <container-id> strace ls
# 看不到真实的syscall，被Sentry处理
```

**Kata Containers（轻量级虚拟机）**：
```
┌──────────────────────────────────────┐
│          Application                 │
└────────────────┬─────────────────────┘
                 │
┌────────────────▼─────────────────────┐
│       Guest Kernel (Mini OS)         │
└────────────────┬─────────────────────┘
                 │
┌────────────────▼─────────────────────┐
│     Hypervisor (QEMU/Firecracker)    │
└────────────────┬─────────────────────┘
                 │
┌────────────────▼─────────────────────┐
│          Host Kernel                 │
└──────────────────────────────────────┘
```

```bash
# 安装Kata Containers
$ sudo sh -c "echo 'deb http://download.opensuse.org/repositories/home:/katacontainers:/releases:/x86_64:/stable-2.0/xUbuntu_$(lsb_release -rs)/ /' > /etc/apt/sources.list.d/kata-containers.list"
$ curl -sL http://download.opensuse.org/repositories/home:/katacontainers:/releases:/x86_64:/stable-2.0/xUbuntu_$(lsb_release -rs)/Release.key | sudo apt-key add -
$ sudo apt-get update && sudo apt-get install -y kata-runtime kata-proxy kata-shim

# 配置Docker
$ sudo tee -a /etc/docker/daemon.json <<EOF
{
  "runtimes": {
    "kata-runtime": {
      "path": "/usr/bin/kata-runtime"
    }
  }
}
EOF

$ sudo systemctl restart docker

# 使用Kata运行容器（VM隔离）
$ docker run --runtime=kata-runtime -d nginx
```

**运行时安全对比**：

| 运行时 | 隔离级别 | 性能 | 启动时间 | 内存开销 | 适用场景 |
|--------|---------|------|---------|---------|---------|
| **runc** | 进程级 | 原生 | <100ms | ~5MB | 可信工作负载 |
| **gVisor** | 用户态内核 | 70-80% | ~200ms | ~15MB | 不可信代码 |
| **Kata** | VM级 | 85-95% | ~500ms | ~130MB | 多租户/高安全 |

---

## 小结：第1章核心知识点

✅ **已掌握内容**：
1. **Namespace隔离机制**：7种namespace类型及实战
2. **Cgroups资源限制**：CPU/内存/IO/PID限制详解
3. **UnionFS文件系统**：Overlay2原理与性能优化
4. **容器运行时**：runc/containerd/gVisor/Kata对比

🎯 **实战能力**：
- 手动创建namespace和cgroup
- 配置资源限制参数
- 选择合适的存储驱动
- 根据安全需求选择运行时

📝 **下一章预告**：
- Docker架构与组件交互
- Docker Daemon配置与优化
- Docker Client API使用

---

## 第 2 章：Docker 架构与组件

### 2.1 Docker 整体架构

#### 2.1.1 架构演进历史

**Docker 1.0-1.10 (单体架构)**:
```
┌─────────────────────────────────────────┐
│           Docker Client                 │
└──────────────┬──────────────────────────┘
               │ REST API
┌──────────────▼──────────────────────────┐
│         Docker Daemon (dockerd)         │
│  ┌────────────────────────────────────┐ │
│  │  Image Management                  │ │
│  │  Container Management              │ │
│  │  Network Management                │ │
│  │  Volume Management                 │ │
│  │  Build System                      │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │    libcontainer (Go实现的容器库)   │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

**Docker 1.11+ (组件化架构 - OCI标准)**:
```
┌─────────────────────────────────────────────────────────┐
│                  Docker Client (docker)                 │
└──────────────────────┬──────────────────────────────────┘
                       │ REST API / gRPC
┌──────────────────────▼──────────────────────────────────┐
│              Docker Daemon (dockerd)                    │
│  ┌────────────────────────────────────────────────────┐│
│  │  Image Management  │  Network  │  Volume  │ Build ││
│  └────────────────────────────────────────────────────┘│
└──────────────────────┬──────────────────────────────────┘
                       │ gRPC
┌──────────────────────▼──────────────────────────────────┐
│                   containerd                            │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Container Lifecycle  │  Image Store  │ Snapshots│  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │ (per container)
          ┌────────────┴────────────┐
┌─────────▼──────────┐   ┌──────────▼─────────┐
│ containerd-shim    │   │ containerd-shim    │
│  ┌──────────────┐  │   │  ┌──────────────┐  │
│  │     runc     │  │   │  │     runc     │  │
│  │  (Container) │  │   │  │  (Container) │  │
│  └──────────────┘  │   │  └──────────────┘  │
└────────────────────┘   └────────────────────┘
```

**架构改进的好处**：
1. **解耦**: dockerd与容器运行时分离
2. **稳定性**: dockerd重启不影响运行中的容器
3. **扩展性**: 可插拔的运行时(runc/kata/gvisor)
4. **标准化**: 遵循OCI标准

---

#### 2.1.2 组件详细说明

**核心组件表**:

| 组件 | 作用 | 进程名 | 通信方式 |
|-----|------|--------|---------|
| **Docker Client** | 用户交互界面 | docker | REST API / Unix Socket |
| **Docker Daemon** | 核心管理服务 | dockerd | gRPC / Unix Socket |
| **containerd** | 容器生命周期管理 | containerd | gRPC |
| **containerd-shim** | 容器进程守护 | containerd-shim | - |
| **runc** | OCI容器运行时 | runc | - |

---

### 2.2 Docker Daemon 深度解析

#### 2.2.1 dockerd 启动过程

**启动流程详解**:
```bash
# 1. systemd启动dockerd
$ sudo systemctl start docker

# 查看完整启动命令
$ ps aux | grep dockerd
root  1234  /usr/bin/dockerd \
    -H fd:// \
    --containerd=/run/containerd/containerd.sock \
    --log-level=info \
    --storage-driver=overlay2

# 2. dockerd初始化流程
# (1) 加载配置文件
$ cat /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true"
  ]
}

# (2) 初始化存储驱动
# (3) 连接containerd
$ ls -l /run/containerd/containerd.sock
srw-rw---- 1 root docker 0 ... /run/containerd/containerd.sock

# (4) 加载已存在的容器和镜像
# (5) 启动API服务器

# 3. 监听端口
$ sudo ss -tulnp | grep dockerd
tcp   LISTEN  0  128  *:2375  *:*  users:(("dockerd",pid=1234,fd=10))
unix  LISTEN  0  128  /var/run/docker.sock  users:(("dockerd",pid=1234,fd=8))
```

---

#### 2.2.2 daemon.json 完整配置详解

**生产级配置模板**:
```json
{
  // === 基础配置 ===
  "data-root": "/data/docker",              // 数据目录(默认/var/lib/docker)
  "exec-root": "/var/run/docker",           // 执行状态目录
  "pidfile": "/var/run/docker.pid",         // PID文件路径

  // === 存储驱动配置 ===
  "storage-driver": "overlay2",             // 存储驱动类型
  "storage-opts": [
    "overlay2.override_kernel_check=true"   // 覆盖内核版本检查
  ],

  // === 日志配置 ===
  "log-driver": "json-file",                // 日志驱动
  "log-opts": {
    "max-size": "100m",                     // 单个日志文件最大100MB
    "max-file": "10",                       // 最多保留10个日志文件
    "compress": "true",                     // 启用压缩
    "labels": "production"                  // 日志标签
  },
  "log-level": "info",                      // dockerd日志级别

  // === 网络配置 ===
  "bridge": "docker0",                      // 默认网桥名称
  "bip": "172.17.0.1/16",                  // 网桥IP地址
  "default-address-pools": [                // 自定义网络池
    {
      "base": "172.80.0.0/16",
      "size": 24
    },
    {
      "base": "172.90.0.0/16",
      "size": 24
    }
  ],
  "dns": ["8.8.8.8", "8.8.4.4"],           // 容器默认DNS
  "dns-search": ["example.com"],            // DNS搜索域
  "mtu": 1500,                              // 网络MTU

  // === 镜像配置 ===
  "registry-mirrors": [                     // 镜像加速器
    "https://mirror.ccs.tencentyun.com",
    "https://docker.mirrors.ustc.edu.cn"
  ],
  "insecure-registries": [                  // 不安全的镜像仓库
    "registry.internal.com:5000"
  ],
  "max-concurrent-downloads": 10,           // 最大并发下载数
  "max-concurrent-uploads": 5,              // 最大并发上传数

  // === 安全配置 ===
  "live-restore": true,                     // dockerd重启时保持容器运行
  "userland-proxy": false,                  // 禁用用户态代理(提升性能)
  "icc": false,                             // 禁用容器间互通(提升安全)
  "userns-remap": "default",                // 用户命名空间重映射
  "no-new-privileges": true,                // 禁止容器进程获取新权限
  "selinux-enabled": false,                 // SELinux支持

  // === 资源限制默认值 ===
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 64000,
      "Soft": 64000
    },
    "nproc": {
      "Name": "nproc",
      "Hard": 64000,
      "Soft": 64000
    }
  },
  "default-shm-size": "64M",                // 共享内存大小

  // === 其他配置 ===
  "experimental": false,                    // 实验性功能
  "metrics-addr": "0.0.0.0:9323",          // Prometheus metrics地址
  "ipv6": false,                            // IPv6支持
  "fixed-cidr-v6": "2001:db8:1::/64",      // IPv6固定CIDR
  "iptables": true,                         // 启用iptables规则
  "ip-forward": true,                       // 启用IP转发
  "ip-masq": true,                          // 启用IP伪装(NAT)

  // === 运行时配置 ===
  "runtimes": {
    "nvidia": {                             // NVIDIA GPU运行时
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    },
    "kata": {                               // Kata Containers
      "path": "/usr/bin/kata-runtime"
    }
  },
  "default-runtime": "runc",                // 默认运行时

  // === 集群配置 (Swarm) ===
  "cluster-store": "consul://localhost:8500",
  "cluster-advertise": "192.168.1.100:2376",

  // === 调试配置 ===
  "debug": false,                           // 调试模式
  "hosts": [                                // 监听地址
    "unix:///var/run/docker.sock",
    "tcp://0.0.0.0:2375"
  ]
}
```

**配置生效**:
```bash
# 修改配置后重启
$ sudo systemctl daemon-reload
$ sudo systemctl restart docker

# 验证配置
$ docker info | grep -A 10 "Storage Driver"
$ docker info | grep -A 5 "Registry Mirrors"
```

---

#### 2.2.3 Docker API 使用

**三种访问方式**:

**1. Unix Socket (本地)**:
```bash
# 默认socket路径
$ curl --unix-socket /var/run/docker.sock \
    http://localhost/version | jq
{
  "Version": "24.0.5",
  "ApiVersion": "1.43",
  "GitCommit": "ced0996",
  "GoVersion": "go1.20.6",
  "Os": "linux",
  "Arch": "amd64",
  ...
}

# 列出容器
$ curl --unix-socket /var/run/docker.sock \
    http://localhost/containers/json | jq

# 创建容器
$ curl --unix-socket /var/run/docker.sock \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{
      "Image": "nginx:alpine",
      "HostConfig": {
        "PortBindings": {
          "80/tcp": [{"HostPort": "8080"}]
        }
      }
    }' \
    http://localhost/containers/create?name=my-nginx
```

**2. TCP Socket (远程)**:
```bash
# ⚠️ 警告：暴露TCP端口有安全风险，生产环境必须使用TLS

# daemon.json配置
{
  "hosts": ["tcp://0.0.0.0:2375", "unix:///var/run/docker.sock"]
}

# 客户端连接
$ docker -H tcp://192.168.1.100:2375 ps

# 使用curl
$ curl http://192.168.1.100:2375/version
```

**3. TLS加密连接（生产推荐）**:
```bash
# 生成CA证书
$ openssl genrsa -aes256 -out ca-key.pem 4096
$ openssl req -new -x509 -days 365 -key ca-key.pem -sha256 -out ca.pem

# 生成服务器证书
$ openssl genrsa -out server-key.pem 4096
$ openssl req -subj "/CN=docker.example.com" -sha256 -new -key server-key.pem -out server.csr

# 配置SAN
$ echo "subjectAltName = DNS:docker.example.com,IP:192.168.1.100" > extfile.cnf
$ openssl x509 -req -days 365 -sha256 -in server.csr -CA ca.pem -CAkey ca-key.pem \
    -CAcreateserial -out server-cert.pem -extfile extfile.cnf

# 生成客户端证书
$ openssl genrsa -out key.pem 4096
$ openssl req -subj '/CN=client' -new -key key.pem -out client.csr
$ echo "extendedKeyUsage = clientAuth" > extfile-client.cnf
$ openssl x509 -req -days 365 -sha256 -in client.csr -CA ca.pem -CAkey ca-key.pem \
    -CAcreateserial -out cert.pem -extfile extfile-client.cnf

# 配置daemon.json
{
  "hosts": ["tcp://0.0.0.0:2376", "unix:///var/run/docker.sock"],
  "tls": true,
  "tlscacert": "/etc/docker/certs/ca.pem",
  "tlscert": "/etc/docker/certs/server-cert.pem",
  "tlskey": "/etc/docker/certs/server-key.pem",
  "tlsverify": true
}

# 客户端连接
$ docker --tlsverify \
    --tlscacert=ca.pem \
    --tlscert=cert.pem \
    --tlskey=key.pem \
    -H tcp://192.168.1.100:2376 ps
```

---

#### 2.2.4 Docker API 实战案例

**Python SDK使用**:
```python
#!/usr/bin/env python3
import docker
from docker.errors import DockerException

# 连接Docker daemon
client = docker.from_env()  # 自动读取环境变量

# 或者显式指定
# client = docker.DockerClient(base_url='unix:///var/run/docker.sock')

# 1. 镜像操作
def manage_images():
    """镜像管理"""
    # 拉取镜像
    print("📥 拉取nginx镜像...")
    image = client.images.pull('nginx', tag='alpine')
    print(f"✅ 镜像ID: {image.short_id}")

    # 列出镜像
    images = client.images.list()
    for img in images:
        print(f"镜像: {img.tags}, 大小: {img.attrs['Size'] / 1024 / 1024:.2f}MB")

    # 构建镜像
    image, build_logs = client.images.build(
        path='/path/to/dockerfile/dir',
        tag='myapp:latest',
        rm=True  # 构建后删除中间容器
    )
    for log in build_logs:
        print(log)

# 2. 容器操作
def manage_containers():
    """容器管理"""
    # 创建并启动容器
    container = client.containers.run(
        'nginx:alpine',
        name='my-nginx',
        detach=True,  # 后台运行
        ports={'80/tcp': 8080},
        environment={'ENV': 'production'},
        volumes={'/data': {'bind': '/usr/share/nginx/html', 'mode': 'ro'}},
        restart_policy={'Name': 'unless-stopped'},
        mem_limit='512m',
        cpu_quota=50000,  # 0.5 CPU
        labels={'app': 'nginx', 'env': 'prod'}
    )
    print(f"✅ 容器启动: {container.id[:12]}")

    # 查看容器日志
    logs = container.logs(stream=False, tail=100)
    print(logs.decode('utf-8'))

    # 执行命令
    exec_result = container.exec_run('nginx -t')
    print(f"Exit code: {exec_result.exit_code}")
    print(exec_result.output.decode('utf-8'))

    # 容器统计信息
    stats = container.stats(stream=False)
    cpu_usage = stats['cpu_stats']['cpu_usage']['total_usage']
    mem_usage = stats['memory_stats']['usage']
    print(f"CPU: {cpu_usage}, Memory: {mem_usage / 1024 / 1024:.2f}MB")

    # 停止并删除
    container.stop(timeout=10)
    container.remove()

# 3. 网络操作
def manage_networks():
    """网络管理"""
    # 创建自定义网络
    network = client.networks.create(
        'my-network',
        driver='bridge',
        ipam=docker.types.IPAMConfig(
            pool_configs=[
                docker.types.IPAMPool(subnet='172.28.0.0/16')
            ]
        )
    )

    # 连接容器到网络
    container = client.containers.get('my-nginx')
    network.connect(container, ipv4_address='172.28.0.10')

    # 断开连接
    network.disconnect(container)

# 4. 卷操作
def manage_volumes():
    """卷管理"""
    # 创建卷
    volume = client.volumes.create(
        name='my-volume',
        driver='local',
        labels={'env': 'prod'}
    )

    # 使用卷
    container = client.containers.run(
        'nginx:alpine',
        volumes={volume.name: {'bind': '/data', 'mode': 'rw'}},
        detach=True
    )

    # 清理未使用的卷
    client.volumes.prune()

# 5. 事件监听
def monitor_events():
    """监听Docker事件"""
    events = client.events(decode=True)

    for event in events:
        if event['Type'] == 'container':
            action = event['Action']
            container_name = event['Actor']['Attributes'].get('name', 'unknown')
            print(f"🔔 容器事件: {container_name} - {action}")

        elif event['Type'] == 'image':
            action = event['Action']
            image_tag = event['Actor']['Attributes'].get('name', 'unknown')
            print(f"🖼️  镜像事件: {image_tag} - {action}")

# 6. 批量操作
def batch_operations():
    """批量管理容器"""
    # 停止所有运行中的容器
    for container in client.containers.list():
        print(f"停止容器: {container.name}")
        container.stop()

    # 清理所有退出的容器
    for container in client.containers.list(all=True, filters={'status': 'exited'}):
        print(f"删除容器: {container.name}")
        container.remove()

    # 清理悬空镜像
    client.images.prune(filters={'dangling': True})

if __name__ == '__main__':
    try:
        manage_images()
        manage_containers()
        manage_networks()
        manage_volumes()
    except DockerException as e:
        print(f"❌ Docker错误: {e}")
```

---

### 2.3 containerd 深度解析

#### 2.3.1 containerd 架构

**containerd 内部组件**:
```
┌───────────────────────────────────────────────────────┐
│                    containerd                         │
│                                                       │
│  ┌─────────────────────────────────────────────────┐│
│  │            gRPC API Server                      ││
│  └──────────────┬──────────────────────────────────┘│
│                 │                                    │
│  ┌──────────────▼──────────────┬───────────────────┐│
│  │     Metadata Service        │  Content Store    ││
│  │     (boltdb)                │  (blobs)          ││
│  └──────────────┬──────────────┴───────────────────┘│
│                 │                                    │
│  ┌──────────────▼────────────────────────────────┐  │
│  │          Snapshot Service                     │  │
│  │  (overlayfs/btrfs/zfs/native)                │  │
│  └──────────────┬────────────────────────────────┘  │
│                 │                                    │
│  ┌──────────────▼────────────────────────────────┐  │
│  │          Task Service                         │  │
│  │  (container lifecycle)                        │  │
│  └──────────────┬────────────────────────────────┘  │
└─────────────────┼────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
┌───────▼────────┐ ┌────────▼───────┐
│ containerd-shim│ │containerd-shim │
│  ┌──────────┐  │ │  ┌──────────┐  │
│  │   runc   │  │ │  │   runc   │  │
│  └──────────┘  │ │  └──────────┘  │
└────────────────┘ └────────────────┘
```

---

#### 2.3.2 containerd 配置

**配置文件路径**: `/etc/containerd/config.toml`

```toml
# containerd 配置文件

version = 2

# 根目录
root = "/var/lib/containerd"
state = "/run/containerd"

# OCI运行时配置
[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]
  runtime_type = "io.containerd.runc.v2"

  [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
    SystemdCgroup = true  # 使用systemd cgroup驱动

# 镜像加速配置
[plugins."io.containerd.grpc.v1.cri".registry.mirrors]
  [plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
    endpoint = ["https://mirror.ccs.tencentyun.com"]

  [plugins."io.containerd.grpc.v1.cri".registry.mirrors."k8s.gcr.io"]
    endpoint = ["https://registry.aliyuncs.com/google_containers"]

# 私有镜像仓库认证
[plugins."io.containerd.grpc.v1.cri".registry.configs."registry.example.com".auth]
  username = "myuser"
  password = "mypassword"

# Snapshotter配置（存储驱动）
[plugins."io.containerd.grpc.v1.cri".containerd]
  snapshotter = "overlayfs"
  default_runtime_name = "runc"

# CNI网络配置
[plugins."io.containerd.grpc.v1.cri".cni]
  bin_dir = "/opt/cni/bin"
  conf_dir = "/etc/cni/net.d"
```

**重启containerd**:
```bash
$ sudo systemctl restart containerd
$ sudo systemctl status containerd
```

---

#### 2.3.3 ctr 命令行工具

**ctr vs docker 命令对比**:

| 功能 | docker命令 | ctr命令 |
|-----|-----------|---------|
| 拉取镜像 | `docker pull nginx` | `ctr images pull docker.io/library/nginx:latest` |
| 列出镜像 | `docker images` | `ctr images list` |
| 运行容器 | `docker run -d nginx` | `ctr run -d docker.io/library/nginx:latest my-nginx` |
| 列出容器 | `docker ps` | `ctr tasks list` |
| 删除容器 | `docker rm <id>` | `ctr tasks kill <id> && ctr containers delete <id>` |
| 查看日志 | `docker logs <id>` | `ctr tasks exec --exec-id sh <id> sh` |

**ctr实战示例**:
```bash
# 1. 命名空间管理（containerd支持多租户）
$ sudo ctr namespaces list
NAME    LABELS
default
moby    # Docker使用的命名空间
k8s.io  # Kubernetes使用的命名空间

$ sudo ctr -n k8s.io images list  # 查看k8s命名空间的镜像

# 2. 镜像操作
$ sudo ctr images pull docker.io/library/nginx:alpine
$ sudo ctr images list -q
docker.io/library/nginx:alpine

# 导出镜像
$ sudo ctr images export nginx.tar docker.io/library/nginx:alpine

# 导入镜像
$ sudo ctr images import nginx.tar

# 3. 容器生命周期
# 创建容器（仅创建，不运行）
$ sudo ctr containers create docker.io/library/nginx:alpine my-nginx

# 启动任务（运行容器）
$ sudo ctr tasks start -d my-nginx

# 查看运行中的任务
$ sudo ctr tasks list
TASK        PID     STATUS
my-nginx    12345   RUNNING

# 暂停容器
$ sudo ctr tasks pause my-nginx

# 恢复容器
$ sudo ctr tasks resume my-nginx

# 杀死任务
$ sudo ctr tasks kill my-nginx

# 删除容器
$ sudo ctr containers delete my-nginx

# 4. 快照管理
$ sudo ctr snapshots list
KEY                                                                 PARENT  KIND
sha256:abc123...                                                            Active
sha256:def456...  sha256:abc123...                                         Committed

# 5. 内容存储
$ sudo ctr content list
DIGEST                                                                  SIZE
sha256:1234567890abcdef...                                            2.3 MB
sha256:fedcba0987654321...                                            5.1 MB

# 6. 租户操作
$ sudo ctr -n custom-namespace images pull nginx:alpine
$ sudo ctr -n custom-namespace containers create nginx:alpine my-app
```

---

### 2.4 containerd-shim 原理

#### 2.4.1 shim 的作用

**为什么需要shim**:
```
没有shim的问题:
dockerd -> containerd -> runc (直接管理容器)
问题：
1. runc退出后容器变成孤儿进程
2. containerd重启会影响所有容器
3. 无法收集容器退出状态

有shim的架构:
dockerd -> containerd -> shim -> runc
优势：
1. runc可以在启动容器后退出(节省资源)
2. shim持续运行,接管容器
3. containerd重启不影响容器
4. 收集容器退出状态和日志
```

**shim 进程查看**:
```bash
# 启动一个nginx容器
$ docker run -d --name nginx nginx:alpine

# 查看进程树
$ pstree -p $(pgrep dockerd)
dockerd(1234)───containerd(1235)─┬─containerd-shim(2345)─┬─nginx(2350)
                                  │                        └─nginx(2351)
                                  └─containerd-shim(2400)───redis(2401)

# 查看shim进程详情
$ ps aux | grep containerd-shim
root  2345  /usr/bin/containerd-shim-runc-v2 \
    -namespace moby \
    -id abc123def456 \
    -address /run/containerd/containerd.sock

# shim管理的容器
$ sudo ls -l /run/containerd/io.containerd.runtime.v2.task/moby/
drwx------ 2 root root 80 ... abc123def456/  # 容器ID目录
```

---

#### 2.4.2 shim 实现细节

**shim 职责**:
1. **保持STDIO打开**: 为容器保持stdin/stdout/stderr
2. **报告容器退出**: 监控容器进程,上报退出状态
3. **守护容器进程**: 作为容器进程的父进程
4. **与containerd通信**: 通过gRPC上报事件

**shim 通信示例**:
```bash
# 查看shim socket
$ sudo ls -l /run/containerd/s/
srw------- 1 root root 0 ... abc123def456  # 每个容器一个socket

# 使用grpcurl与shim通信(需要安装grpcurl)
$ sudo grpcurl -unix \
    -d '{"id": "abc123def456"}' \
    /run/containerd/s/abc123def456 \
    containerd.runtime.v2.Task/Stats
{
  "stats": {
    "cpu_stats": {...},
    "memory_stats": {...}
  }
}
```

---

### 2.5 Docker 与 Kubernetes 集成

#### 2.5.1 CRI (Container Runtime Interface)

**CRI 架构**:
```
┌─────────────────────────────────────┐
│           kubelet                   │
└────────────┬────────────────────────┘
             │ CRI (gRPC)
┌────────────▼────────────────────────┐
│       CRI Runtime Shim              │
│  (containerd/CRI-O/Docker-shim)    │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│       OCI Runtime (runc)            │
└─────────────────────────────────────┘
```

**dockershim 被弃用**:
```bash
# Kubernetes 1.20+警告
$ kubectl get nodes -o wide
NAME    STATUS   VERSION   CONTAINER-RUNTIME
node1   Ready    v1.24.0   containerd://1.6.8  # 推荐
node2   Ready    v1.23.0   docker://20.10.17   # 已弃用(1.24+移除)

# 迁移到containerd
# 1. 安装containerd
$ sudo apt-get install containerd

# 2. 配置containerd
$ sudo mkdir -p /etc/containerd
$ containerd config default | sudo tee /etc/containerd/config.toml

# 3. 修改kubelet配置
# /var/lib/kubelet/kubeadm-flags.env
KUBELET_KUBEADM_ARGS="--container-runtime=remote \
    --container-runtime-endpoint=unix:///run/containerd/containerd.sock"

# 4. 重启服务
$ sudo systemctl restart containerd kubelet
```

---

## 小结：第2章核心知识点

✅ **已掌握内容**：
1. **Docker架构演进**: 单体→组件化→OCI标准
2. **dockerd配置**: daemon.json完整配置详解
3. **Docker API**: Unix Socket/TCP/TLS三种方式
4. **containerd架构**: gRPC API、快照、内容存储
5. **containerd-shim**: 守护容器进程的关键组件
6. **CRI集成**: Kubernetes容器运行时接口

🎯 **实战能力**：
- 生产级dockerd配置
- 使用Docker API自动化管理
- 理解containerd工作流程
- 排查shim相关问题

---

## 第 3 章：镜像原理与存储驱动

### 3.1 镜像分层原理

#### 3.1.1 镜像 vs 容器层

**镜像分层示意图**:
```
┌────────────────────────────────────────────────┐
│       Container Layer (Read-Write)             │  ← 容器运行时修改
│  - 新创建的文件                                 │
│  - 修改的文件（COW from image layers）          │
│  - 删除的文件（whiteout文件标记）               │
├────────────────────────────────────────────────┤
│       Image Layer N (Read-Only)                │  ← CMD/ENTRYPOINT
│  sha256:abc123...                              │
├────────────────────────────────────────────────┤
│       Image Layer N-1 (Read-Only)              │  ← RUN指令层
│  sha256:def456...                              │
├────────────────────────────────────────────────┤
│       Image Layer 2 (Read-Only)                │  ← COPY指令层
│  sha256:789ghi...                              │
├────────────────────────────────────────────────┤
│       Image Layer 1 (Read-Only)                │  ← FROM基础镜像
│  sha256:jkl012...                              │
└────────────────────────────────────────────────┘
               ↓ UnionFS合并
┌────────────────────────────────────────────────┐
│       Merged View (Container Root)             │
│       /bin, /etc, /usr, /var, ...              │
└────────────────────────────────────────────────┘
```

---

#### 3.1.2 镜像层查看

**inspect查看镜像层**:
```bash
# 拉取nginx镜像
$ docker pull nginx:alpine

# 查看镜像层
$ docker inspect nginx:alpine | jq '.[0].RootFS'
{
  "Type": "layers",
  "Layers": [
    "sha256:01fd6df81c8ec7dd24bbbd72342671f41813f992999a3471b9d9cbc44ad88374",
    "sha256:1e94b4f87af7e61d4dea54b4da4a37a4c8c5a1f87c38a6f93d2c8d6d7f7bce67",
    "sha256:d8c1c7c1c2b3f9e8d5a9f3b4c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0",
    "sha256:a3c2e1f0d9b8c7a6f5e4d3c2b1a0f9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2",
    "sha256:f1e0d9c8b7a6f5e4d3c2b1a0f9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2c1b0",
    "sha256:e3d2c1b0a9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2"
  ]
}

# 使用docker history查看层构建历史
$ docker history nginx:alpine
IMAGE          CREATED        CREATED BY                                      SIZE
abc123def456   2 weeks ago    CMD ["nginx" "-g" "daemon off;"]                0B
def456ghi789   2 weeks ago    STOPSIGNAL SIGQUIT                              0B
ghi789jkl012   2 weeks ago    EXPOSE 80                                       0B
jkl012mno345   2 weeks ago    COPY file:abc /etc/nginx/nginx.conf # bu...     643B
mno345pqr678   2 weeks ago    RUN /bin/sh -c set -x     && addgroup -g...     8.12MB
pqr678stu901   2 weeks ago    ENV NGINX_VERSION=1.25.2                        0B
stu901vwx234   2 weeks ago    /bin/sh -c #(nop)  LABEL maintainer=NGI...     0B
vwx234yz1345   3 weeks ago    /bin/sh -c #(nop) ADD file:abc123 in /          7.34MB
```

**层的存储位置**:
```bash
# overlay2存储目录
$ sudo ls -l /var/lib/docker/overlay2/
drwx--x---  4 root root 55  l/               # 层的短链接目录
drwx--x---  4 root root 55  <layer-id-1>/
drwx--x---  4 root root 55  <layer-id-2>/
drwx--x---  4 root root 55  <layer-id-3>/

# 查看某一层的内容
$ sudo ls /var/lib/docker/overlay2/<layer-id>/diff/
bin  boot  dev  etc  home  lib  media  mnt  opt  proc  root  run  sbin  srv  sys  tmp  usr  var

# 查看层的元数据
$ sudo cat /var/lib/docker/overlay2/<layer-id>/link
ABCDEFGHIJKLMN  # 短链接名(避免路径过长)

$ sudo cat /var/lib/docker/overlay2/<layer-id>/lower
l/MNOPQRSTUVWX:l/XYZVABCDEFGH  # 下层的链接
```

---

#### 3.1.3 写时复制 (Copy-on-Write) 详解

**COW 工作流程**:
```bash
# 1. 启动容器
$ docker run -d --name test nginx:alpine

# 2. 容器初始状态（所有层只读）
$ docker diff test
# 输出为空，因为没有修改

# 3. 修改文件（触发COW）
$ docker exec test sh -c 'echo "modified" > /etc/nginx/nginx.conf'

# 4. 查看差异
$ docker diff test
C /etc
C /etc/nginx
C /etc/nginx/nginx.conf

# C = Changed (文件被修改)
# A = Added (文件被添加)
# D = Deleted (文件被删除)

# 5. 查看COW后的文件位置
$ docker inspect test | grep UpperDir
"UpperDir": "/var/lib/docker/overlay2/xyz123.../diff"

# 原始文件仍在只读层
$ sudo find /var/lib/docker/overlay2 -name nginx.conf
/var/lib/docker/overlay2/abc.../diff/etc/nginx/nginx.conf  # 只读层(原始)
/var/lib/docker/overlay2/xyz.../diff/etc/nginx/nginx.conf  # 可写层(修改后)
```

**COW 性能影响**:
```bash
# 测试大文件COW性能
$ docker run -it --rm ubuntu:20.04 bash

# 容器内创建大文件
root@container:/# dd if=/dev/zero of=/bigfile bs=1M count=1000
1000+0 records in
1000+0 records out
1048576000 bytes (1.0 GB) copied, 2.5 s, 419 MB/s

# 第一次修改（触发COW，需要复制整个文件）
root@container:/# echo "modified" >> /bigfile
# 速度较慢，因为需要复制1GB文件

# 第二次修改（文件已在可写层，无需COW）
root@container:/# echo "modified again" >> /bigfile
# 速度很快
```

**优化建议**:
- 避免在容器内修改大文件
- 使用卷(Volume)存储大文件
- 使用tmpfs存储临时大文件

---

### 3.2 镜像存储结构

#### 3.2.1 镜像元数据

**镜像配置文件**:
```bash
# 导出镜像配置
$ docker save nginx:alpine -o nginx.tar
$ tar -xf nginx.tar
$ ls
abc123def456.json  # 镜像配置文件
def456ghi789/      # 层目录
manifest.json      # 清单文件
repositories       # 仓库信息

# 查看manifest.json
$ cat manifest.json | jq
[
  {
    "Config": "abc123def456.json",
    "RepoTags": ["nginx:alpine"],
    "Layers": [
      "def456ghi789/layer.tar",
      "ghi789jkl012/layer.tar",
      "jkl012mno345/layer.tar"
    ]
  }
]

# 查看镜像配置
$ cat abc123def456.json | jq
{
  "architecture": "amd64",
  "config": {
    "Hostname": "",
    "Domainname": "",
    "User": "",
    "AttachStdin": false,
    "AttachStdout": false,
    "AttachStderr": false,
    "ExposedPorts": {
      "80/tcp": {}
    },
    "Tty": false,
    "OpenStdin": false,
    "StdinOnce": false,
    "Env": [
      "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
      "NGINX_VERSION=1.25.2"
    ],
    "Cmd": ["nginx", "-g", "daemon off;"],
    "Image": "sha256:...",
    "Volumes": null,
    "WorkingDir": "",
    "Entrypoint": ["/docker-entrypoint.sh"],
    "OnBuild": null,
    "Labels": {
      "maintainer": "NGINX Docker Maintainers"
    },
    "StopSignal": "SIGQUIT"
  },
  "container": "abc123...",
  "container_config": {...},
  "created": "2024-01-01T00:00:00.000000000Z",
  "docker_version": "24.0.5",
  "history": [
    {
      "created": "2024-01-01T00:00:00Z",
      "created_by": "/bin/sh -c #(nop) ADD file:abc123 in / "
    },
    {
      "created": "2024-01-01T00:00:01Z",
      "created_by": "/bin/sh -c #(nop)  ENV NGINX_VERSION=1.25.2",
      "empty_layer": true
    },
    ...
  ],
  "os": "linux",
  "rootfs": {
    "type": "layers",
    "diff_ids": [
      "sha256:def456...",
      "sha256:ghi789...",
      "sha256:jkl012..."
    ]
  }
}
```

---

#### 3.2.2 Content Addressable Storage (内容寻址存储)

**基于哈希的存储**:
```
镜像层存储结构:
/var/lib/docker/
├── image/
│   └── overlay2/
│       ├── imagedb/              # 镜像数据库
│       │   └── content/
│       │       └── sha256/
│       │           └── abc123... # 镜像配置(JSON)
│       ├── layerdb/              # 层数据库
│       │   └── sha256/
│       │       ├── def456.../    # 层元数据
│       │       │   ├── cache-id  # 指向实际存储
│       │       │   ├── diff      # diff ID
│       │       │   ├── size      # 层大小
│       │       │   └── tar-split.json.gz
│       │       └── ghi789.../
│       └── repositories.json     # 仓库索引
└── overlay2/                     # 实际存储
    ├── <cache-id-1>/
    │   ├── diff/                 # 层内容
    │   ├── link                  # 短链接
    │   └── lower                 # 父层链接
    └── <cache-id-2>/
```

**查看层的cache-id**:
```bash
# 获取镜像ID
$ docker images --no-trunc nginx:alpine
REPOSITORY   TAG      IMAGE ID                     CREATED      SIZE
nginx        alpine   sha256:abc123def456...       2 weeks ago  43.2MB

# 查看层元数据
$ sudo ls /var/lib/docker/image/overlay2/layerdb/sha256/
def456ghi789...
ghi789jkl012...

# 查看cache-id（指向实际存储目录）
$ sudo cat /var/lib/docker/image/overlay2/layerdb/sha256/def456.../cache-id
xyz789abc123  # 这是/var/lib/docker/overlay2/xyz789abc123/的目录

# 查看层大小
$ sudo cat /var/lib/docker/image/overlay2/layerdb/sha256/def456.../size
8120320

# 查看diff ID
$ sudo cat /var/lib/docker/image/overlay2/layerdb/sha256/def456.../diff
sha256:original-uncompressed-diff-id...
```

---

### 3.3 镜像分发原理

#### 3.3.1 Docker Registry Protocol

**OCI Distribution Spec (镜像分发协议)**:
```bash
# 1. 检查镜像是否存在
$ curl -I https://registry-1.docker.io/v2/library/nginx/manifests/alpine
HTTP/1.1 200 OK
Docker-Content-Digest: sha256:abc123...
Content-Type: application/vnd.docker.distribution.manifest.v2+json

# 2. 拉取manifest
$ curl -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
    https://registry-1.docker.io/v2/library/nginx/manifests/alpine
{
  "schemaVersion": 2,
  "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
  "config": {
    "mediaType": "application/vnd.docker.container.image.v1+json",
    "size": 7510,
    "digest": "sha256:abc123..."
  },
  "layers": [
    {
      "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
      "size": 3370234,
      "digest": "sha256:def456..."
    },
    {
      "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
      "size": 8120320,
      "digest": "sha256:ghi789..."
    }
  ]
}

# 3. 拉取镜像配置
$ curl https://registry-1.docker.io/v2/library/nginx/blobs/sha256:abc123...

# 4. 拉取每一层
$ curl https://registry-1.docker.io/v2/library/nginx/blobs/sha256:def456... \
    -o layer1.tar.gz
```

---

#### 3.3.2 镜像拉取流程详解

**完整拉取过程**:
```bash
# 开启Docker daemon调试模式
$ sudo dockerd --debug &

# 拉取镜像（观察详细日志）
$ docker pull nginx:alpine
alpine: Pulling from library/nginx
01fd6df81c8e: Pull complete   # Layer 1
1e94b4f87af7: Pull complete   # Layer 2
d8c1c7c1c2b3: Pull complete   # Layer 3
...
Digest: sha256:abc123def456...
Status: Downloaded newer image for nginx:alpine
docker.io/library/nginx:alpine

# 拉取流程分解:
# 1. 解析镜像名 (nginx:alpine -> registry-1.docker.io/library/nginx:alpine)
# 2. 认证 (如果需要)
# 3. 获取manifest
# 4. 检查本地是否已有相同digest的层
# 5. 并发下载缺失的层
# 6. 解压层到overlay2目录
# 7. 更新imagedb和layerdb元数据
# 8. 创建镜像标签

# 查看拉取的并发数（默认3）
$ docker info | grep "Max concurrent downloads"
Max concurrent downloads: 3

# 修改并发数
# daemon.json
{
  "max-concurrent-downloads": 10
}
```

---

#### 3.3.3 镜像推送流程

**完整推送过程**:
```bash
# 1. 构建镜像
$ docker build -t myregistry.com/myapp:v1.0 .

# 2. 登录私有仓库
$ docker login myregistry.com
Username: myuser
Password:
Login Succeeded

# 3. 推送镜像
$ docker push myregistry.com/myapp:v1.0
The push refers to repository [myregistry.com/myapp]
abc123def456: Pushed    # Layer 1
def456ghi789: Pushed    # Layer 2
ghi789jkl012: Mounted   # Layer 3 (已存在，直接挂载)
v1.0: digest: sha256:xyz789... size: 2345

# 推送流程:
# 1. 检查仓库是否存在
# 2. 检查每一层在仓库中是否已存在 (通过digest)
# 3. 上传缺失的层 (支持断点续传)
# 4. 上传镜像配置
# 5. 上传manifest

# 查看推送并发数
$ docker info | grep "Max concurrent uploads"
Max concurrent uploads: 5
```

---

### 3.4 镜像优化技巧

#### 3.4.1 减少镜像层数

**❌ 错误示例（层数过多）**:
```dockerfile
FROM ubuntu:20.04
RUN apt-get update
RUN apt-get install -y nginx
RUN apt-get install -y curl
RUN apt-get install -y vim
RUN apt-get clean
# 6层，每个RUN创建一层
```

**✅ 正确示例（合并层）**:
```dockerfile
FROM ubuntu:20.04
RUN apt-get update && \
    apt-get install -y nginx curl vim && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
# 2层（FROM + RUN）
```

---

#### 3.4.2 减少镜像大小

**技巧1：使用Alpine基础镜像**:
```bash
# Ubuntu基础镱像
$ docker images ubuntu:20.04
REPOSITORY   TAG      SIZE
ubuntu       20.04    72.8MB

# Alpine基础镜像
$ docker images alpine:3.18
REPOSITORY   TAG      SIZE
alpine       3.18     7.34MB

# 大小对比: Alpine比Ubuntu小10倍
```

**技巧2：清理缓存文件**:
```dockerfile
FROM ubuntu:20.04

# ❌ 错误：缓存文件会保留在层中
RUN apt-get update
RUN apt-get install -y nginx
RUN apt-get clean  # 这个清理无效，因为在新的一层

# ✅ 正确：在同一层中清理
RUN apt-get update && \
    apt-get install -y nginx && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
```

**技巧3：多阶段构建**:
```dockerfile
# ❌ 单阶段构建（包含编译工具，镜像大）
FROM golang:1.20
WORKDIR /app
COPY . .
RUN go build -o myapp
CMD ["./myapp"]
# 镜像大小: 1.2GB

# ✅ 多阶段构建（仅包含运行时）
FROM golang:1.20 AS builder
WORKDIR /app
COPY . .
RUN go build -o myapp

FROM alpine:3.18
COPY --from=builder /app/myapp /usr/local/bin/
CMD ["myapp"]
# 镜像大小: 15MB (减少80倍!)
```

---

#### 3.4.3 使用.dockerignore

```bash
# .dockerignore文件
# Git相关
.git
.gitignore
.github

# 文档
*.md
docs/

# 测试文件
*_test.go
test/
coverage/

# 编译产物
*.o
*.so
*.exe
target/
build/

# 依赖缓存
node_modules/
vendor/
.cache/

# IDE配置
.vscode/
.idea/
*.swp

# 临时文件
*.log
*.tmp
.DS_Store

# 环境文件
.env
.env.local
```

---

#### 3.4.4 镜像扫描与安全

**使用docker scout扫描漏洞**:
```bash
# 扫描镜像
$ docker scout cves nginx:alpine
    ✓ SBOM of image already cached, 14 packages indexed
    ✓ Detected 2 vulnerable packages

┌────────────────────┬───────────────────┬──────────┬────────┐
│ Package            │ Version           │ Severity │ CVE ID │
├────────────────────┼───────────────────┼──────────┼────────┤
│ libcrypto3         │ 3.0.8-r0          │ HIGH     │CVE-...│
│ libssl3            │ 3.0.8-r0          │ HIGH     │CVE-...│
└────────────────────┴───────────────────┴──────────┴────────┘

# 使用Trivy扫描（更强大）
$ docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy:latest image nginx:alpine

# 扫描结果
nginx:alpine (alpine 3.18.2)
===========================
Total: 2 (UNKNOWN: 0, LOW: 0, MEDIUM: 0, HIGH: 2, CRITICAL: 0)

┌──────────────┬────────────────┬──────────┬───────────────────┐
│   Library    │ Vulnerability  │ Severity │ Installed Version │
├──────────────┼────────────────┼──────────┼───────────────────┤
│ libcrypto3   │ CVE-2023-1234  │   HIGH   │ 3.0.8-r0          │
│ libssl3      │ CVE-2023-1234  │   HIGH   │ 3.0.8-r0          │
└──────────────┴────────────────┴──────────┴───────────────────┘
```

---

## 小结：第3章核心知识点

✅ **已掌握内容**：
1. **镜像分层**: UnionFS、写时复制(COW)、层合并
2. **存储结构**: imagedb、layerdb、overlay2实际存储
3. **Content Addressable Storage**: 基于哈希的去重存储
4. **镜像分发**: OCI Distribution Spec、拉取/推送流程
5. **镜像优化**: 减少层数、缩小体积、多阶段构建、安全扫描

🎯 **实战能力**：
- 理解COW性能影响并优化
- 查看镜像层和元数据
- 优化Dockerfile减少镜像大小
- 使用安全扫描工具

📝 **下一章预告**：
- Docker网络模式详解 (bridge/host/none/overlay)
- iptables规则与NAT原理
- 跨主机容器通信
- 网络性能优化

---

## 第 4 章：Docker 网络原理与实现

### 4.1 Docker 网络架构概览

#### 4.1.1 网络模式对比

**Docker 四种网络模式**：

| 网络模式 | 说明 | 性能 | 隔离性 | 适用场景 | 端口映射 |
|---------|------|------|--------|---------|---------|
| **bridge** | 桥接模式(默认) | 中等 | 高 | 单机容器互通 | 支持 |
| **host** | 主机模式 | 原生 | 无 | 高性能需求 | 不需要 |
| **none** | 无网络 | - | 完全隔离 | 自定义网络栈 | 不支持 |
| **overlay** | 覆盖网络 | 较低 | 高 | 跨主机通信 | 支持 |
| **macvlan** | MAC地址虚拟化 | 高 | 中 | 容器直接接入物理网络 | 不需要 |
| **container** | 共享容器网络 | 原生 | 共享 | Pod内容器通信 | 继承 |

---

### 4.2 Bridge 网络模式深度解析

#### 4.2.1 默认 docker0 网桥

**网桥架构**：
```
┌─────────────────────────────────────────────────────┐
│                  Host (宿主机)                       │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │           docker0 (172.17.0.1/16)            │  │
│  │               Linux Bridge                   │  │
│  └──┬────────────┬────────────┬─────────────┬──┘  │
│     │            │            │             │     │
│  ┌──▼──┐     ┌──▼──┐     ┌──▼──┐      ┌───▼──┐  │
│  │veth0│     │veth1│     │veth2│      │veth3 │  │
│  └──┬──┘     └──┬──┘     └──┬──┘      └───┬──┘  │
│     │            │            │             │     │
├─────┼────────────┼────────────┼─────────────┼─────┤
│  ┌──▼──┐     ┌──▼──┐     ┌──▼──┐      ┌───▼──┐  │
│  │ eth0│     │ eth0│     │ eth0│      │ eth0 │  │
│  │.17.2│     │.17.3│     │.17.4│      │.17.5 │  │
│  └─────┘     └─────┘     └─────┘      └──────┘  │
│ Container1  Container2  Container3   Container4  │
└─────────────────────────────────────────────────────┘
```

**查看docker0网桥**：
```bash
# 查看网桥信息
$ ip addr show docker0
3: docker0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP
    link/ether 02:42:ac:11:00:01 brd ff:ff:ff:ff:ff:ff
    inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0
       valid_lft forever preferred_lft forever

# 查看网桥上的接口
$ brctl show docker0
bridge name     bridge id               STP enabled     interfaces
docker0         8000.0242ac110001       no              veth1a2b3c4
                                                        veth5d6e7f8
                                                        veth9g0h1i2

# 查看路由表
$ ip route
default via 192.168.1.1 dev eth0
172.17.0.0/16 dev docker0 proto kernel scope link src 172.17.0.1
192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.100
```

---

#### 4.2.2 容器网络配置过程

**容器启动网络配置流程**：
```bash
# 1. 创建容器
$ docker run -d --name nginx nginx:alpine

# 2. 查看容器网络配置
$ docker inspect nginx -f '{{.NetworkSettings.IPAddress}}'
172.17.0.2

$ docker inspect nginx -f '{{.NetworkSettings.Gateway}}'
172.17.0.1

# 3. 查看veth pair
$ docker exec nginx ip addr
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536
    inet 127.0.0.1/8 scope host lo
12: eth0@if13: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    link/ether 02:42:ac:11:00:02 brd ff:ff:ff:ff:ff:ff
    inet 172.17.0.2/16 brd 172.17.255.255 scope global eth0

# 宿主机端的veth
$ ip link | grep -A 1 ^13:
13: veth1a2b3c4@if12: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    link/ether 12:34:56:78:9a:bc brd ff:ff:ff:ff:ff:ff link-netnsid 0

# 4. 测试容器间通信
$ docker run -d --name redis redis:alpine
$ docker exec nginx ping -c 2 172.17.0.3
PING 172.17.0.3 (172.17.0.3): 56 data bytes
64 bytes from 172.17.0.3: seq=0 ttl=64 time=0.123 ms
64 bytes from 172.17.0.3: seq=1 ttl=64 time=0.098 ms
```

**网络配置详细步骤**：
1. 创建veth pair（虚拟网卡对）
2. 一端连接到docker0网桥
3. 另一端放入容器的network namespace
4. 分配IP地址（从docker0的子网中）
5. 设置默认路由（网关指向docker0）
6. 配置iptables规则（NAT/FORWARD）

---

#### 4.2.3 自定义网桥

**创建自定义网桥**：
```bash
# 创建自定义网络
$ docker network create \
    --driver bridge \
    --subnet 172.20.0.0/16 \
    --gateway 172.20.0.1 \
    --opt "com.docker.network.bridge.name=br-custom" \
    my-network

# 查看网络详情
$ docker network inspect my-network
[
    {
        "Name": "my-network",
        "Id": "abc123def456",
        "Scope": "local",
        "Driver": "bridge",
        "IPAM": {
            "Config": [
                {
                    "Subnet": "172.20.0.0/16",
                    "Gateway": "172.20.0.1"
                }
            ]
        },
        "Containers": {},
        "Options": {
            "com.docker.network.bridge.name": "br-custom"
        }
    }
]

# 查看自定义网桥
$ ip addr show br-custom
15: br-custom: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500
    inet 172.20.0.1/16 brd 172.20.255.255 scope global br-custom

# 连接容器到自定义网络
$ docker run -d --name app1 --network my-network nginx:alpine
$ docker run -d --name app2 --network my-network redis:alpine

# 验证DNS解析（自定义网络支持容器名解析）
$ docker exec app1 ping -c 2 app2
PING app2 (172.20.0.3): 56 data bytes
64 bytes from 172.20.0.3: seq=0 ttl=64 time=0.156 ms
```

**自定义网络 vs 默认网桥**：

| 特性 | 默认docker0 | 自定义网桥 |
|-----|-----------|-----------|
| DNS解析 | ❌ 不支持容器名 | ✅ 支持容器名 |
| 网络隔离 | ❌ 所有容器共享 | ✅ 网络间隔离 |
| 动态连接 | ✅ 支持 | ✅ 支持 |
| IP范围 | 固定172.17.0.0/16 | ✅ 自定义 |
| 网桥选项 | 有限 | ✅ 丰富配置 |

---

### 4.3 iptables 与 NAT 原理

#### 4.3.1 iptables 基础

**iptables 四表五链**：

```
                   PREROUTING
                       ↓
           ┌───────────┴───────────┐
           │                       │
       路由判断              [DNAT转换]
           │                       │
           ↓                       ↓
        INPUT                  FORWARD
           │                       │
      本机进程                    ↓
           │                   OUTPUT
           ↓                       │
        OUTPUT                     ↓
           │                  POSTROUTING
           ↓                       ↓
      POSTROUTING              [SNAT转换]
           ↓                       ↓
       外出数据包              转发数据包
```

**四表**：
- **filter**: 包过滤（防火墙）
- **nat**: 网络地址转换
- **mangle**: 包修改
- **raw**: 状态跟踪豁免

**五链**：
- **PREROUTING**: 数据包进入时
- **INPUT**: 进入本机的包
- **FORWARD**: 转发的包
- **OUTPUT**: 本机发出的包
- **POSTROUTING**: 数据包离开时

---

#### 4.3.2 Docker iptables 规则详解

**查看Docker创建的iptables规则**：
```bash
# NAT表规则
$ sudo iptables -t nat -L -n -v --line-numbers

Chain PREROUTING (policy ACCEPT 0 packets, 0 bytes)
num   pkts bytes target     prot opt in     out     source      destination
1     1234 567K  DOCKER     all  --  *      *       0.0.0.0/0   0.0.0.0/0   ADDRTYPE match dst-type LOCAL

Chain DOCKER (2 references)
num   pkts bytes target     prot opt in     out     source      destination
1       10  600  RETURN     all  --  docker0 *      0.0.0.0/0   0.0.0.0/0
2       50 3000  DNAT       tcp  --  !docker0 *     0.0.0.0/0   0.0.0.0/0   tcp dpt:8080 to:172.17.0.2:80

Chain POSTROUTING (policy ACCEPT 0 packets, 0 bytes)
num   pkts bytes target     prot opt in     out     source           destination
1      100 6000  MASQUERADE all  --  *      !docker0 172.17.0.0/16   0.0.0.0/0
2       20 1200  MASQUERADE tcp  --  *      *       172.17.0.2       172.17.0.2  tcp dpt:80

# Filter表规则
$ sudo iptables -t filter -L DOCKER -n -v --line-numbers

Chain DOCKER (1 references)
num   pkts bytes target     prot opt in     out     source      destination
1      150 9000  ACCEPT     tcp  --  !docker0 docker0 0.0.0.0/0   172.17.0.2  tcp dpt:80

Chain DOCKER-ISOLATION-STAGE-1 (1 references)
num   pkts bytes target     prot opt in     out     source      destination
1      500 30K   DOCKER-ISOLATION-STAGE-2  all  --  docker0 !docker0  0.0.0.0/0   0.0.0.0/0
2        0     0 RETURN     all  --  *      *       0.0.0.0/0   0.0.0.0/0

Chain DOCKER-ISOLATION-STAGE-2 (1 references)
num   pkts bytes target     prot opt in     out     source      destination
1        0     0 DROP       all  --  *      docker0  0.0.0.0/0   0.0.0.0/0
2      500 30K   RETURN     all  --  *      *       0.0.0.0/0   0.0.0.0/0
```

---

#### 4.3.3 端口映射原理（DNAT + SNAT）

**端口映射示例**：
```bash
# 启动nginx并映射端口
$ docker run -d -p 8080:80 --name nginx nginx:alpine

# 查看端口映射
$ docker port nginx
80/tcp -> 0.0.0.0:8080

# 查看DNAT规则（目标地址转换）
$ sudo iptables -t nat -L DOCKER -n | grep 8080
DNAT  tcp  --  0.0.0.0/0  0.0.0.0/0  tcp dpt:8080 to:172.17.0.2:80

# 查看SNAT规则（源地址伪装）
$ sudo iptables -t nat -L POSTROUTING -n | grep 172.17.0.2
MASQUERADE  tcp  --  172.17.0.2  172.17.0.2  tcp dpt:80
```

**端口映射流程**：
```
外部请求: 192.168.1.100:8080 → 宿主机:8080
    ↓ [DNAT规则]
转换后: 192.168.1.100:8080 → 172.17.0.2:80 (容器)
    ↓ [容器处理]
响应: 172.17.0.2:80 → 192.168.1.100:随机端口
    ↓ [SNAT规则 MASQUERADE]
转换后: 宿主机:8080 → 192.168.1.100:随机端口
```

**手动验证端口映射**：
```bash
# 1. 从外部访问
$ curl http://192.168.1.100:8080
<!DOCTYPE html>
<html>
<head><title>Welcome to nginx!</title></head>
...

# 2. 抓包验证DNAT
$ sudo tcpdump -i any -nn 'port 8080 or port 80' -c 10
# 可以看到:
# 宿主机eth0: 192.168.1.101:12345 → 192.168.1.100:8080
# docker0: 192.168.1.101:12345 → 172.17.0.2:80
# 容器eth0: 192.168.1.101:12345 → 172.17.0.2:80
```

---

#### 4.3.4 容器访问外网原理（MASQUERADE）

**MASQUERADE（地址伪装）**：
```bash
# 容器访问外网流程
$ docker exec nginx ping -c 2 8.8.8.8

# iptables规则
$ sudo iptables -t nat -L POSTROUTING -n
Chain POSTROUTING (policy ACCEPT)
target     prot opt source           destination
MASQUERADE all  --  172.17.0.0/16    0.0.0.0/0

# 流程:
# 容器: 172.17.0.2:12345 → 8.8.8.8:53
#   ↓ 路由到docker0
# docker0: 172.17.0.2:12345 → 8.8.8.8:53
#   ↓ POSTROUTING链
# MASQUERADE: 192.168.1.100:54321 → 8.8.8.8:53 (替换源IP为宿主机IP)
#   ↓ 出eth0
# 外网: 192.168.1.100:54321 → 8.8.8.8:53
```

**验证IP伪装**：
```bash
# 容器内查看访问外网
$ docker exec nginx sh -c 'apk add curl && curl -s ifconfig.me'
192.168.1.100  # 显示宿主机公网IP，而非容器IP

# 查看conntrack连接跟踪
$ sudo conntrack -L | grep 172.17.0.2
tcp  6 117 TIME_WAIT src=172.17.0.2 dst=8.8.8.8 sport=12345 dport=53 \
     src=8.8.8.8 dst=192.168.1.100 sport=53 dport=54321 [ASSURED]
```

---

### 4.4 Host 网络模式

#### 4.4.1 Host 模式原理

**Host模式架构**：
```
┌─────────────────────────────────────┐
│           Host Network Stack         │
│  ┌────────────────────────────────┐ │
│  │  eth0: 192.168.1.100           │ │
│  │  lo: 127.0.0.1                 │ │
│  │  docker0: 172.17.0.1           │ │
│  └────────────────────────────────┘ │
│           ↑                          │
│           │ (共享)                   │
│  ┌────────┴───────────────────────┐ │
│  │  Container (Host Network)      │ │
│  │  - 无独立网络命名空间           │ │
│  │  - 直接使用宿主机网络栈         │ │
│  │  - 无需NAT/端口映射             │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
```

**使用Host模式**：
```bash
# 启动Host模式容器
$ docker run -d --name nginx-host --network host nginx:alpine

# 容器内查看网络
$ docker exec nginx-host ip addr
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536
    inet 127.0.0.1/8 scope host lo
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    inet 192.168.1.100/24 brd 192.168.1.255 scope global eth0
3: docker0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0

# 完全相同！容器与宿主机共享网络栈

# 容器直接监听宿主机端口
$ docker run -d --network host nginx:alpine
$ curl http://localhost:80  # 直接访问，无需端口映射
```

---

#### 4.4.2 Host 模式性能对比

**性能基准测试**：
```bash
# 测试脚本
#!/bin/bash

# Bridge模式（带NAT）
docker run -d --name nginx-bridge -p 8080:80 nginx:alpine
ab -n 10000 -c 100 http://localhost:8080/ > bridge.txt

# Host模式（无NAT）
docker run -d --name nginx-host --network host nginx:alpine
ab -n 10000 -c 100 http://localhost:80/ > host.txt

# 性能对比
echo "Bridge模式:"
grep "Requests per second" bridge.txt
echo "Host模式:"
grep "Requests per second" host.txt
```

**典型性能数据**：

| 网络模式 | QPS | 延迟(P50) | 延迟(P99) | CPU开销 |
|---------|-----|----------|----------|---------|
| **Bridge** | 25,000 | 4ms | 12ms | 15% |
| **Host** | 45,000 | 2ms | 6ms | 8% |
| **性能提升** | +80% | -50% | -50% | -47% |

**适用场景**：
- ✅ 高性能要求（数据库、缓存）
- ✅ 需要低延迟
- ✅ 可信环境（无需网络隔离）
- ❌ 多租户环境（安全风险）
- ❌ 端口冲突风险

---

### 4.5 自定义网络实战

#### 4.5.1 多容器通信架构

**三层网络架构**：
```bash
# 1. 创建前端网络
$ docker network create \
    --driver bridge \
    --subnet 172.25.0.0/16 \
    frontend

# 2. 创建后端网络
$ docker network create \
    --driver bridge \
    --subnet 172.26.0.0/16 \
    backend

# 3. 创建数据库网络
$ docker network create \
    --driver bridge \
    --subnet 172.27.0.0/16 \
    database

# 4. 启动容器并连接到相应网络
# Web服务器（连接前端和后端）
$ docker run -d --name web \
    --network frontend \
    nginx:alpine

$ docker network connect backend web

# 应用服务器（连接后端和数据库）
$ docker run -d --name app \
    --network backend \
    myapp:latest

$ docker network connect database app

# 数据库（仅连接数据库网络）
$ docker run -d --name db \
    --network database \
    postgres:alpine

# 5. 验证网络隔离
$ docker exec web ping -c 1 app  # ✅ 可以通信（都在backend）
$ docker exec web ping -c 1 db   # ❌ 无法通信（不在同一网络）
$ docker exec app ping -c 1 db   # ✅ 可以通信（都在database）
```

**网络拓扑图**：
```
┌─────────────────────────────────────────────────────┐
│                   frontend                          │
│                  172.25.0.0/16                      │
│              ┌────────────────┐                     │
│              │  web (nginx)   │                     │
│              │  172.25.0.2    │                     │
│              └────────┬───────┘                     │
└───────────────────────┼─────────────────────────────┘
                        │
┌───────────────────────┼─────────────────────────────┐
│                   backend                           │
│                  172.26.0.0/16                      │
│              ┌────────┴───────┐                     │
│              │  web (nginx)   │                     │
│              │  172.26.0.2    │                     │
│              └────────┬───────┘                     │
│              ┌────────▼───────┐                     │
│              │   app (API)    │                     │
│              │  172.26.0.3    │                     │
│              └────────┬───────┘                     │
└───────────────────────┼─────────────────────────────┘
                        │
┌───────────────────────┼─────────────────────────────┐
│                   database                          │
│                  172.27.0.0/16                      │
│              ┌────────▼───────┐                     │
│              │   app (API)    │                     │
│              │  172.27.0.2    │                     │
│              └────────┬───────┘                     │
│              ┌────────▼───────┐                     │
│              │  db (postgres) │                     │
│              │  172.27.0.3    │                     │
│              └────────────────┘                     │
└─────────────────────────────────────────────────────┘
```

---

#### 4.5.2 网络别名与服务发现

**使用网络别名**：
```bash
# 创建网络
$ docker network create app-network

# 启动多个相同服务实例（负载均衡）
$ docker run -d --name api1 \
    --network app-network \
    --network-alias api \
    myapi:latest

$ docker run -d --name api2 \
    --network app-network \
    --network-alias api \
    myapi:latest

$ docker run -d --name api3 \
    --network app-network \
    --network-alias api \
    myapi:latest

# 客户端容器
$ docker run -it --name client \
    --network app-network \
    alpine sh

# 容器内DNS查询（轮询负载均衡）
$ nslookup api
Name:      api
Address 1: 172.28.0.2 api1.app-network
Address 2: 172.28.0.3 api2.app-network
Address 3: 172.28.0.4 api3.app-network

# 测试负载均衡
$ for i in {1..6}; do
    wget -qO- http://api:8080/hostname
    echo
done
# 输出:
# api1
# api2
# api3
# api1
# api2
# api3
```

---

### 4.6 跨主机容器通信 (Overlay 网络)

#### 4.6.1 Overlay 网络原理

**Overlay网络架构**：
```
┌────────────────────────────────────────────────────┐
│                   物理网络                          │
│           192.168.1.0/24                           │
│                                                    │
│  ┌──────────────┐              ┌──────────────┐  │
│  │  Host1       │              │  Host2       │  │
│  │192.168.1.10  │◄────────────►│192.168.1.20  │  │
│  │              │   VXLAN      │              │  │
│  │  ┌────────┐  │   Tunnel     │  ┌────────┐  │  │
│  │  │Overlay │  │              │  │Overlay │  │  │
│  │  │Network │  │              │  │Network │  │  │
│  │  │10.0.0.0│  │              │  │10.0.0.0│  │  │
│  │  └───┬────┘  │              │  └───┬────┘  │  │
│  │      │       │              │      │       │  │
│  │  ┌───▼───┐   │              │  ┌───▼───┐   │  │
│  │  │ app1  │   │              │  │ app2  │   │  │
│  │  │10.0.0.2│  │              │  │10.0.0.3│  │  │
│  │  └───────┘   │              │  └───────┘   │  │
│  └──────────────┘              └──────────────┘  │
└────────────────────────────────────────────────────┘
```

**VXLAN封装**：
```
原始数据包:
┌──────────┬──────────┬──────┐
│ Src:10.0.0.2 │ Dst:10.0.0.3 │ Data │
└──────────┴──────────┴──────┘

VXLAN封装后:
┌────────────────────────────────────────────────┐
│ Outer IP: 192.168.1.10 → 192.168.1.20         │
├────────────────────────────────────────────────┤
│ VXLAN Header: VNI=256                         │
├────────────────────────────────────────────────┤
│ Inner IP: 10.0.0.2 → 10.0.0.3                 │
├────────────────────────────────────────────────┤
│ Data                                          │
└────────────────────────────────────────────────┘
```

---

#### 4.6.2 Docker Swarm Overlay 网络实战

**创建Swarm集群**：
```bash
# 节点1（Manager）
$ docker swarm init --advertise-addr 192.168.1.10
Swarm initialized: current node (abc123) is now a manager.
To add a worker to this swarm, run the following command:
    docker swarm join --token SWMTKN-1-xxx 192.168.1.10:2377

# 节点2（Worker）
$ docker swarm join --token SWMTKN-1-xxx 192.168.1.10:2377
This node joined a swarm as a worker.

# 查看节点
$ docker node ls
ID            HOSTNAME  STATUS  AVAILABILITY  MANAGER STATUS
abc123 *      node1     Ready   Active        Leader
def456        node2     Ready   Active
```

**创建Overlay网络**：
```bash
# 创建overlay网络
$ docker network create \
    --driver overlay \
    --subnet 10.0.0.0/24 \
    --attachable \
    my-overlay

# 查看网络
$ docker network ls | grep overlay
abc123def456  my-overlay  overlay   swarm

# 在节点1启动服务
$ docker service create \
    --name web \
    --network my-overlay \
    --replicas 2 \
    nginx:alpine

# 在节点2启动服务
$ docker service create \
    --name api \
    --network my-overlay \
    --replicas 2 \
    myapi:latest

# 验证跨主机通信
$ docker exec <web-container-id> ping api
PING api (10.0.0.3): 56 data bytes
64 bytes from 10.0.0.3: seq=0 ttl=64 time=0.456 ms
```

---

### 4.7 网络性能优化

#### 4.7.1 禁用 userland-proxy

**userland-proxy 问题**：
```bash
# 查看userland-proxy进程
$ ps aux | grep docker-proxy
root  12345  /usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 8080 -container-ip 172.17.0.2 -container-port 80

# 问题：
# 1. 每个端口映射创建一个进程（资源开销）
# 2. 数据经过用户态代理（性能损耗）
# 3. 100个容器 x 5个端口 = 500个进程
```

**优化方案**：
```json
// daemon.json
{
  "userland-proxy": false,
  "iptables": true
}
```

**性能对比**：
```bash
# 测试脚本
#!/bin/bash

# 测试userland-proxy开启
docker run -d -p 8080:80 --name test1 nginx:alpine
ab -n 100000 -c 1000 http://localhost:8080/ | grep "Requests per second"

# 测试userland-proxy关闭
# 修改daemon.json后重启docker
docker run -d -p 8080:80 --name test2 nginx:alpine
ab -n 100000 -c 1000 http://localhost:8080/ | grep "Requests per second"
```

| 配置 | QPS | CPU使用 | 内存使用 |
|------|-----|---------|---------|
| userland-proxy=true | 32,000 | 45% | 250MB |
| userland-proxy=false | 48,000 | 28% | 150MB |
| **性能提升** | +50% | -38% | -40% |

---

#### 4.7.2 调整 MTU

**MTU 优化**：
```bash
# 查看当前MTU
$ docker network inspect bridge -f '{{.Options.com.docker.network.driver.mtu}}'
1500

# 创建大MTU网络（适合内网）
$ docker network create \
    --driver bridge \
    --opt com.docker.network.driver.mtu=9000 \
    jumbo-network

# 性能测试
# 标准MTU 1500
$ docker run --rm --network bridge \
    nicolaka/netshoot \
    iperf3 -c target-host -t 30

# 巨型MTU 9000
$ docker run --rm --network jumbo-network \
    nicolaka/netshoot \
    iperf3 -c target-host -t 30
```

**MTU对比**：

| MTU | 吞吐量 | CPU使用 | 适用场景 |
|-----|--------|---------|---------|
| 1500 | 8 Gbps | 85% | 公网/默认 |
| 9000 | 12 Gbps | 55% | 内网/数据中心 |

---

#### 4.7.3 使用 macvlan 直连物理网络

**macvlan 模式**：
```bash
# 创建macvlan网络
$ docker network create -d macvlan \
    --subnet=192.168.1.0/24 \
    --gateway=192.168.1.1 \
    -o parent=eth0 \
    macvlan-net

# 启动容器（直接获得物理网络IP）
$ docker run -d --name web \
    --network macvlan-net \
    --ip 192.168.1.100 \
    nginx:alpine

# 容器IP在物理网络中可直接访问
$ ping 192.168.1.100  # 从其他物理机
PING 192.168.1.100 (192.168.1.100) 56(84) bytes of data.
64 bytes from 192.168.1.100: icmp_seq=1 ttl=64 time=0.234 ms
```

**macvlan vs bridge 性能**：

| 网络模式 | 吞吐量 | 延迟 | NAT开销 | 适用场景 |
|---------|--------|------|---------|---------|
| **bridge** | 8 Gbps | 0.5ms | 有 | 通用 |
| **macvlan** | 10 Gbps | 0.1ms | 无 | 高性能/遗留应用 |

---

## 小结：第4章核心知识点

✅ **已掌握内容**：
1. **网络模式**: bridge/host/none/overlay/macvlan五种模式对比
2. **bridge原理**: docker0网桥、veth pair、容器网络配置流程
3. **iptables**: 四表五链、DNAT/SNAT、端口映射原理
4. **自定义网络**: DNS解析、网络隔离、服务发现
5. **overlay网络**: VXLAN封装、跨主机通信、Swarm集成
6. **性能优化**: 禁用userland-proxy、MTU调整、macvlan直连

🎯 **实战能力**：
- 理解端口映射完整流程(DNAT+SNAT)
- 设计多层网络架构(前端/后端/数据库隔离)
- 配置跨主机容器通信
- 优化网络性能(+50% QPS)

---

## 第 5 章：资源隔离与限制进阶

### 5.1 CPU 资源管理进阶

#### 5.1.1 CPU 完全公平调度器 (CFS)

**CFS 调度原理**：
```
CPU时间分配:
┌────────────────────────────────────────┐
│  CPU调度周期 (100ms)                   │
│  ┌──────────┬──────────┬──────────┐   │
│  │Container1│Container2│Container3│   │
│  │ shares   │ shares   │ shares   │   │
│  │  1024    │  2048    │  512     │   │
│  │  (28%)   │  (57%)   │  (14%)   │   │
│  └──────────┴──────────┴──────────┘   │
│  │◄─28ms──►│◄──57ms──►│◄─14ms──►│    │
└────────────────────────────────────────┘

计算公式:
Container1 CPU% = 1024 / (1024+2048+512) × 100% = 28.6%
Container2 CPU% = 2048 / (1024+2048+512) × 100% = 57.1%
Container3 CPU% = 512 / (1024+2048+512) × 100% = 14.3%
```

**CPU shares 实战**：
```bash
# 创建3个容器，CPU权重 2:1:1
$ docker run -d --name cpu-high --cpu-shares 2048 \
    progrium/stress --cpu 4

$ docker run -d --name cpu-mid --cpu-shares 1024 \
    progrium/stress --cpu 4

$ docker run -d --name cpu-low --cpu-shares 1024 \
    progrium/stress --cpu 4

# 实时监控CPU使用
$ docker stats --no-stream
CONTAINER   CPU %     MEM USAGE / LIMIT
cpu-high    50.0%     ...               # 获得 2/4 = 50%
cpu-mid     25.0%     ...               # 获得 1/4 = 25%
cpu-low     25.0%     ...               # 获得 1/4 = 25%

# 查看cgroup配置
$ cat /sys/fs/cgroup/cpu/docker/<container-id>/cpu.shares
2048
```

---

#### 5.1.2 CPU 配额与周期

**CFS 配额机制**：
```bash
# 限制容器使用0.5个CPU核心
$ docker run -d --name limited \
    --cpu-period=100000 \
    --cpu-quota=50000 \
    stress --cpu 8

# 解释:
# cpu-period: 调度周期（微秒），默认100000us = 100ms
# cpu-quota: 周期内可用CPU时间（微秒），50000us = 50ms
# 结果: 50ms / 100ms = 0.5 CPU

# 等价于:
$ docker run -d --cpus="0.5" stress --cpu 8

# 查看cgroup配置
$ cat /sys/fs/cgroup/cpu/docker/<container-id>/cpu.cfs_period_us
100000

$ cat /sys/fs/cgroup/cpu/docker/<container-id>/cpu.cfs_quota_us
50000

# CPU节流统计
$ cat /sys/fs/cgroup/cpu/docker/<container-id>/cpu.stat
nr_periods 12345         # 总周期数
nr_throttled 6789        # 被节流的周期数
throttled_time 456789000 # 被节流的总时间(纳秒)
```

---

#### 5.1.3 实时进程优先级

**CPU RT（Real-Time）调度**：
```bash
# 配置实时CPU调度（需要内核支持CONFIG_RT_GROUP_SCHED）
$ docker run -d --name rt-container \
    --cpu-rt-runtime=950000 \
    --cpu-rt-period=1000000 \
    myapp:latest

# 解释:
# 每1000000us(1秒)内，最多使用950000us(0.95秒)的实时CPU
# 预留50000us给系统进程

# 查看RT配置
$ cat /sys/fs/cgroup/cpu/docker/<container-id>/cpu.rt_runtime_us
950000

$ cat /sys/fs/cgroup/cpu/docker/<container-id>/cpu.rt_period_us
1000000
```

---

### 5.2 内存管理进阶

#### 5.2.1 内存 Cgroup 子系统详解

**内存统计文件**：
```bash
# 查看内存详细统计
$ cat /sys/fs/cgroup/memory/docker/<container-id>/memory.stat

cache 104857600           # 页缓存（100MB）
rss 209715200            # 常驻内存（200MB）
rss_huge 0               # 大页内存
mapped_file 52428800     # 映射文件（50MB）
pgpgin 123456            # 页面换入次数
pgpgout 234567           # 页面换出次数
swap 0                   # 使用的swap
pgfault 345678           # 页错误次数
pgmajfault 12345         # 主要页错误（需要磁盘I/O）
inactive_anon 0          # 非活跃匿名页
active_anon 209715200    # 活跃匿名页
inactive_file 52428800   # 非活跃文件页
active_file 52428800     # 活跃文件页
unevictable 0            # 不可回收页

# 实时内存使用
$ cat /sys/fs/cgroup/memory/docker/<container-id>/memory.usage_in_bytes
314572800  # 约300MB

# 内存限制
$ cat /sys/fs/cgroup/memory/docker/<container-id>/memory.limit_in_bytes
536870912  # 512MB

# 内存压力
$ cat /sys/fs/cgroup/memory/docker/<container-id>/memory.pressure_level
low  # low/medium/critical
```

---

#### 5.2.2 内存软限制与硬限制

**两层限制机制**：
```bash
# 软限制(reservation) + 硬限制(limit)
$ docker run -d --name mem-limits \
    --memory=1g \              # 硬限制：1GB
    --memory-reservation=512m \  # 软限制：512MB
    --memory-swap=2g \         # 总内存+swap: 2GB
    --kernel-memory=100m \     # 内核内存限制
    myapp:latest

# 行为说明:
# 1. 正常情况: 使用<=512MB (在软限制内)
# 2. 内存压力: 可以使用512MB-1GB (超出软限制，但在硬限制内)
# 3. 达到1GB: 触发OOM killer
# 4. swap使用: 最多2GB-1GB=1GB的swap

# 查看配置
$ docker inspect mem-limits -f '{{.HostConfig.Memory}}'
1073741824  # 1GB

$ docker inspect mem-limits -f '{{.HostConfig.MemoryReservation}}'
536870912  # 512MB

$ docker inspect mem-limits -f '{{.HostConfig.MemorySwap}}'
2147483648  # 2GB
```

---

#### 5.2.3 OOM Killer 深度控制

**OOM优先级调整**：
```bash
# OOM score越高，越容易被杀死（-1000到1000）
$ docker run -d --name protected-app \
    --oom-score-adj=-500 \
    --memory=512m \
    important-app:latest

$ docker run -d --name expendable-app \
    --oom-score-adj=500 \
    --memory=512m \
    cache-service:latest

# 查看OOM score
$ cat /proc/$(docker inspect -f '{{.State.Pid}}' protected-app)/oom_score
150  # 实际score = 基础score + oom_score_adj

$ cat /proc/$(docker inspect -f '{{.State.Pid}}' expendable-app)/oom_score
1150

# OOM事件监控
$ sudo dmesg | grep -i "killed process"
[12345.678] Out of memory: Killed process 54321 (expendable-app) \
            total-vm:524288kB, anon-rss:524288kB, file-rss:0kB

# 禁用OOM killer（危险！容器会挂起而非被杀死）
$ docker run -d --name no-oom \
    --oom-kill-disable \
    --memory=512m \
    myapp:latest
```

---

### 5.3 Block I/O 限制进阶

#### 5.3.1 I/O 权重与优先级

**I/O调度器配置**：
```bash
# 查看磁盘I/O调度器
$ cat /sys/block/sda/queue/scheduler
noop deadline [cfq]  # cfq支持权重，其他不支持

# 设置I/O权重（100-1000，默认500）
$ docker run -d --name io-high \
    --blkio-weight 800 \
    myapp:latest

$ docker run -d --name io-low \
    --blkio-weight 200 \
    myapp:latest

# 验证配置
$ cat /sys/fs/cgroup/blkio/docker/<container-id>/blkio.weight
800

# 针对特定设备设置权重
$ docker run -d --name io-custom \
    --blkio-weight-device /dev/sda:600 \
    --blkio-weight-device /dev/sdb:400 \
    myapp:latest
```

---

#### 5.3.2 I/O 速率精确控制

**IOPS 和带宽双重限制**：
```bash
# 限制读写IOPS和带宽
$ docker run -d --name io-limited \
    --device-read-iops /dev/sda:100 \    # 读IOPS: 100
    --device-write-iops /dev/sda:50 \    # 写IOPS: 50
    --device-read-bps /dev/sda:10mb \    # 读带宽: 10MB/s
    --device-write-bps /dev/sda:5mb \    # 写带宽: 5MB/s
    myapp:latest

# 查看配置
$ cat /sys/fs/cgroup/blkio/docker/<container-id>/blkio.throttle.read_iops_device
8:0 100  # 主设备号8，次设备号0（sda）

$ cat /sys/fs/cgroup/blkio/docker/<container-id>/blkio.throttle.read_bps_device
8:0 10485760  # 10MB

# 测试I/O限制
$ docker exec io-limited sh -c '
    dd if=/dev/zero of=/test bs=1M count=100 oflag=direct
'
100+0 records in
100+0 records out
104857600 bytes (105 MB) copied, 20.0 s, 5.2 MB/s  # 符合5MB/s限制

# 实时监控I/O
$ docker stats io-limited --no-stream
CONTAINER    BLOCK I/O
io-limited   5.24MB / 2.61MB  # 读/写速率
```

---

#### 5.3.3 I/O 性能分析

**blkio.throttle统计**：
```bash
# I/O操作统计
$ cat /sys/fs/cgroup/blkio/docker/<container-id>/blkio.throttle.io_serviced
8:0 Read 12345         # sda读操作次数
8:0 Write 6789         # sda写操作次数
8:0 Sync 15678         # 同步操作
8:0 Async 3456         # 异步操作
8:0 Total 19134        # 总操作

# I/O字节统计
$ cat /sys/fs/cgroup/blkio/docker/<container-id>/blkio.throttle.io_service_bytes
8:0 Read 104857600     # 读了100MB
8:0 Write 52428800     # 写了50MB
8:0 Total 157286400    # 总共150MB

# I/O等待时间
$ cat /sys/fs/cgroup/blkio/docker/<container-id>/blkio.throttle.io_wait_time
8:0 Read 12345678      # 读等待时间(纳秒)
8:0 Write 6789012      # 写等待时间(纳秒)
```

---

### 5.4 网络带宽限制

#### 5.4.1 使用 tc 限制容器网络带宽

**tc (Traffic Control) 配置**：
```bash
# 获取容器veth接口
$ CONTAINER_ID=$(docker inspect -f '{{.Id}}' nginx)
$ VETH=$(docker exec $CONTAINER_ID cat /sys/class/net/eth0/iflink)
$ VETH_NAME=$(ip link | grep "^$VETH:" | cut -d: -f2 | xargs)

echo "容器veth接口: $VETH_NAME"

# 限制出口带宽（从容器到外部）10Mbps
$ sudo tc qdisc add dev $VETH_NAME root tbf \
    rate 10mbit \        # 速率10Mbps
    latency 50ms \       # 延迟50ms
    burst 1540           # 突发1540字节

# 验证配置
$ sudo tc -s qdisc show dev $VETH_NAME
qdisc tbf 8001: root refcnt 2 rate 10Mbit burst 1540b lat 50.0ms
 Sent 1048576 bytes 1024 pkt (dropped 0, overlimits 123 requeues 0)

# 测试带宽限制
$ docker exec nginx sh -c '
    wget -O /dev/null http://speedtest.example.com/100MB
'
# 下载速度应该在10Mbps左右
```

**入口带宽限制（使用 IFB）**：
```bash
# 加载IFB模块
$ sudo modprobe ifb numifbs=1

# 启用ifb0
$ sudo ip link set dev ifb0 up

# 将容器入口流量重定向到ifb0
$ sudo tc qdisc add dev $VETH_NAME ingress
$ sudo tc filter add dev $VETH_NAME parent ffff: \
    protocol ip u32 match u32 0 0 flowid 1:1 \
    action mirred egress redirect dev ifb0

# 在ifb0上限制速率（入口10Mbps）
$ sudo tc qdisc add dev ifb0 root tbf \
    rate 10mbit latency 50ms burst 1540

# 查看统计
$ sudo tc -s qdisc show dev ifb0
```

---

#### 5.4.2 Docker 网络插件限速

**使用 docker-tc 插件**：
```bash
# 安装docker-tc插件
$ docker plugin install \
    lukaszlach/docker-tc:latest \
    --grant-all-permissions

# 创建限速标签
$ docker run -d --name limited-nginx \
    --label "com.docker-tc.enabled=1" \
    --label "com.docker-tc.limit=10mbps" \
    --label "com.docker-tc.delay=100ms" \
    nginx:alpine

# 动态修改限速
$ docker update --label "com.docker-tc.limit=20mbps" limited-nginx

# 查看限速状态
$ docker exec limited-nginx cat /sys/class/net/eth0/tx_queue_len
1000
```

---

### 5.5 PID 和设备限制

#### 5.5.1 进程数限制防护

**fork炸弹防护**：
```bash
# 限制容器最多100个进程
$ docker run -d --name pid-limited \
    --pids-limit 100 \
    ubuntu:20.04

# 测试fork炸弹
$ docker exec pid-limited bash -c ':(){ :|:& };:'
bash: fork: retry: Resource temporarily unavailable

# 查看当前进程数
$ cat /sys/fs/cgroup/pids/docker/<container-id>/pids.current
98

# 查看限制
$ cat /sys/fs/cgroup/pids/docker/<container-id>/pids.max
100

# PID耗尽事件
$ cat /sys/fs/cgroup/pids/docker/<container-id>/pids.events
max 5  # 触发限制的次数
```

---

#### 5.5.2 设备访问控制

**device cgroup 白名单**：
```bash
# 默认情况：容器无法访问宿主机设备
$ docker run -it --rm ubuntu:20.04 ls /dev
# 仅能看到: null zero random urandom tty console等

# 授权访问特定设备（只读）
$ docker run -it --rm \
    --device=/dev/sda:/dev/xvda:r \
    ubuntu:20.04 bash

# 容器内
$ ls -l /dev/xvda
brw-r--r-- 1 root root 8, 0 ... /dev/xvda

# 授权访问GPU
$ docker run -it --rm \
    --device=/dev/nvidia0 \
    --device=/dev/nvidiactl \
    --device=/dev/nvidia-uvm \
    nvidia/cuda:11.0 bash

# 查看设备访问配置
$ cat /sys/fs/cgroup/devices/docker/<container-id>/devices.list
c 1:3 rwm    # /dev/null
c 1:5 rwm    # /dev/zero
c 1:7 rwm    # /dev/full
c 1:8 rwm    # /dev/random
c 1:9 rwm    # /dev/urandom
c 5:0 rwm    # /dev/tty
c 5:1 rwm    # /dev/console
b 8:0 r      # /dev/sda (只读)
```

---

### 5.6 综合资源限制实战

#### 5.6.1 生产级资源配置模板

**Web应用容器**：
```bash
docker run -d \
  --name web-prod \
  # CPU限制
  --cpus="2.5" \               # 2.5个CPU核心
  --cpu-shares=1024 \          # CPU权重（竞争时）
  # 内存限制
  --memory="2g" \              # 硬限制2GB
  --memory-reservation="1g" \  # 软限制1GB
  --memory-swap="3g" \         # 总内存+swap 3GB
  --oom-score-adj=-100 \       # OOM优先级（较低）
  # I/O限制
  --blkio-weight=500 \         # I/O权重
  --device-read-bps /dev/sda:50mb \   # 读带宽50MB/s
  --device-write-bps /dev/sda:30mb \  # 写带宽30MB/s
  # 进程限制
  --pids-limit=500 \           # 最多500进程
  # 网络
  --network custom-net \
  # 日志限制
  --log-opt max-size=100m \
  --log-opt max-file=3 \
  # 重启策略
  --restart unless-stopped \
  myapp:latest
```

**数据库容器**：
```bash
docker run -d \
  --name postgres-prod \
  # CPU限制（高优先级）
  --cpus="4" \
  --cpu-shares=2048 \          # 更高CPU权重
  # 内存限制（大内存）
  --memory="8g" \
  --memory-reservation="6g" \
  --memory-swap="10g" \
  --oom-score-adj=-500 \       # 高优先级保护
  # I/O限制（高I/O）
  --blkio-weight=800 \         # 更高I/O权重
  --device-read-iops /dev/sda:1000 \
  --device-write-iops /dev/sda:800 \
  # 数据卷
  -v postgres-data:/var/lib/postgresql/data \
  # 网络（host模式获取最佳性能）
  --network host \
  postgres:15-alpine
```

---

#### 5.6.2 资源监控与告警

**实时监控脚本**：
```bash
#!/bin/bash
# docker-resource-monitor.sh

CONTAINER=$1
THRESHOLD_CPU=80
THRESHOLD_MEM=80
THRESHOLD_IO=100

while true; do
    # 获取容器统计
    STATS=$(docker stats $CONTAINER --no-stream --format \
        "{{.CPUPerc}}|{{.MemPerc}}|{{.BlockIO}}")

    CPU=$(echo $STATS | cut -d'|' -f1 | sed 's/%//')
    MEM=$(echo $STATS | cut -d'|' -f2 | sed 's/%//')
    IO=$(echo $STATS | cut -d'|' -f3)

    # CPU告警
    if (( $(echo "$CPU > $THRESHOLD_CPU" | bc -l) )); then
        echo "⚠️  [$(date)] CPU超限: $CPU%"
        # 发送告警（webhook/email等）
    fi

    # 内存告警
    if (( $(echo "$MEM > $THRESHOLD_MEM" | bc -l) )); then
        echo "⚠️  [$(date)] 内存超限: $MEM%"
    fi

    # I/O告警
    IO_MB=$(echo $IO | grep -oP '\d+MB' | grep -oP '\d+')
    if [ ! -z "$IO_MB" ] && [ $IO_MB -gt $THRESHOLD_IO ]; then
        echo "⚠️  [$(date)] I/O超限: $IO_MB MB/s"
    fi

    sleep 10
done
```

**Prometheus监控集成**：
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'docker'
    static_configs:
      - targets: ['localhost:9323']  # Docker daemon metrics

# docker daemon.json
{
  "metrics-addr": "0.0.0.0:9323",
  "experimental": true
}

# 重启docker
$ sudo systemctl restart docker

# 查询示例
$ curl http://localhost:9323/metrics | grep container_
container_cpu_usage_seconds_total{id="/docker/abc123",name="web"} 123.45
container_memory_usage_bytes{id="/docker/abc123",name="web"} 524288000
container_network_receive_bytes_total{id="/docker/abc123",interface="eth0"} 1048576
```

---

## 小结：第5章核心知识点

✅ **已掌握内容**：
1. **CPU管理**: CFS调度器、shares/quota/period、RT调度
2. **内存管理**: memory.stat详解、软/硬限制、OOM优先级
3. **I/O限制**: 权重/IOPS/带宽三重限制、性能分析
4. **网络限速**: tc工具、docker-tc插件
5. **PID限制**: fork炸弹防护
6. **设备控制**: device cgroup白名单
7. **综合实战**: 生产级配置模板、资源监控告警

🎯 **实战能力**：
- 精确控制容器资源使用
- 配置生产级资源限制
- 实时监控资源使用并告警
- 优化资源分配策略

---

# 第二部分:镜像构建与优化实战

---

# 第6章:Dockerfile最佳实践深度解析

## 6.1 Dockerfile核心指令详解

### 6.1.1 FROM指令:基础镜像选择策略

```dockerfile
# ✅ 推荐:明确指定版本+digest
FROM nginx:1.25.3-alpine@sha256:9c367186df82fcc5c92c91c0ff5f3de68b2f5b6c0f8d0c6cf79c9d6c2b3e4a5c

# ❌ 避免:使用latest标签
FROM nginx:latest

# ⚠️ 生产环境策略
FROM python:3.11.7-slim-bookworm AS builder  # Debian系统稳定性
FROM python:3.11.7-alpine AS runtime         # Alpine最小化
```

**基础镜像选择对比**:

| 镜像类型 | 大小 | 安全性 | 兼容性 | 适用场景 |
|---------|------|-------|--------|---------|
| `alpine` | 5-10MB | ⭐⭐⭐⭐⭐ | musl libc问题 | 生产环境首选 |
| `-slim` | 40-70MB | ⭐⭐⭐⭐ | glibc完整支持 | Python/Node应用 |
| 完整镜像 | 150-400MB | ⭐⭐⭐ | 完全兼容 | 开发环境 |
| `scratch` | 0KB | ⭐⭐⭐⭐⭐ | 静态编译 | Go/Rust应用 |

---

### 6.1.2 RUN指令:层数优化与缓存利用

```dockerfile
# ❌ 反模式:多层RUN导致镜像臃肿
FROM ubuntu:22.04
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y wget
RUN apt-get install -y git
RUN rm -rf /var/lib/apt/lists/*  # ⚠️ 无效清理!前几层已固化

# ✅ 最佳实践:单层RUN+清理缓存
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y \
    curl=7.81.0-1ubuntu1.15 \
    wget=1.21.2-2ubuntu1 \
    git=1:2.34.1-1ubuntu1.10 \
    # 在同一层清理缓存
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
 && truncate -s 0 /var/log/*log

# ✅ 利用构建缓存:按变更频率排序
FROM python:3.11-slim
# 1️⃣ 系统依赖(变更少,放前面)
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# 2️⃣ Python依赖(中等变更)
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# 3️⃣ 应用代码(变更频繁,放最后)
COPY . /app
```

**层数优化原理**:

```bash
# 查看镜像层数
$ docker history myapp:v1
IMAGE          CREATED BY                                      SIZE
<missing>      /bin/sh -c #(nop) COPY . /app                   2.3MB
<missing>      /bin/sh -c pip install -r requirements.txt      150MB
<missing>      /bin/sh -c apt-get install gcc                  200MB
<missing>      /bin/sh -c #(nop) FROM python:3.11-slim         50MB

# 每个RUN/COPY/ADD都会创建新层
# 优化目标:减少层数 + 最大化缓存命中
```

---

### 6.1.3 COPY vs ADD:使用场景区分

```dockerfile
# ✅ 推荐:使用COPY复制文件
COPY app.py /app/
COPY static/ /var/www/html/
COPY --chown=nginx:nginx config.conf /etc/nginx/

# ⚠️ ADD的隐式行为(容易出错)
ADD archive.tar.gz /data/  # 自动解压
ADD https://example.com/file.zip /tmp/  # 自动下载

# ✅ 显式使用RUN处理下载和解压
RUN curl -fsSL https://example.com/file.zip -o /tmp/file.zip \
 && unzip /tmp/file.zip -d /data/ \
 && rm /tmp/file.zip

# ✅ .dockerignore排除无关文件
# 创建 .dockerignore 文件:
# node_modules/
# .git/
# *.log
# .env
# __pycache__/
```

---

### 6.1.4 CMD vs ENTRYPOINT:容器启动行为

```dockerfile
# 📌 CMD:可被docker run参数覆盖
FROM nginx:alpine
CMD ["nginx", "-g", "daemon off;"]

# 运行方式:
$ docker run myapp              # 执行 nginx -g "daemon off;"
$ docker run myapp echo "hello" # 覆盖CMD,执行 echo "hello"

# 📌 ENTRYPOINT:作为主命令,CMD作为参数
FROM python:3.11-slim
ENTRYPOINT ["python", "app.py"]
CMD ["--port", "8000"]

# 运行方式:
$ docker run myapp                  # python app.py --port 8000
$ docker run myapp --port 9000      # python app.py --port 9000
$ docker run myapp --debug          # python app.py --debug

# ✅ 组合模式:ENTRYPOINT + CMD
FROM alpine:3.19
COPY docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["default-command"]

# docker-entrypoint.sh 脚本:
#!/bin/sh
set -e
# 初始化逻辑
exec "$@"  # 执行CMD参数
```

**Exec格式 vs Shell格式**:

```dockerfile
# ✅ Exec格式(推荐):精确控制进程
CMD ["python", "app.py"]
# 进程树: PID 1 → python

# ❌ Shell格式:创建额外shell进程
CMD python app.py
# 进程树: PID 1 → /bin/sh -c "python app.py"
#                   └─ PID 7 → python

# 问题:信号无法传递给python进程
# docker stop会向PID 1(shell)发送SIGTERM
# 但shell不会转发给python,导致强制SIGKILL
```

---

### 6.1.5 ENV vs ARG:构建时变量与运行时变量

```dockerfile
# ARG:仅构建时有效
ARG PYTHON_VERSION=3.11
ARG APP_ENV=production

FROM python:${PYTHON_VERSION}-slim
RUN echo "Building for: ${APP_ENV}"

# ENV:容器运行时持久化
ENV APP_HOME=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR ${APP_HOME}

# ✅ 组合使用:ARG → ENV传递
ARG VERSION
ENV APP_VERSION=${VERSION}

# 构建命令:
$ docker build --build-arg VERSION=1.2.3 -t myapp:1.2.3 .

# 运行时环境变量:
$ docker run --env-file .env myapp:1.2.3
$ docker run -e DATABASE_URL=postgres://... myapp:1.2.3
```

**环境变量优先级**:

```bash
# 优先级从高到低:
1. docker run -e KEY=value         # 命令行参数
2. docker run --env-file .env      # 环境文件
3. Dockerfile ENV KEY=value        # 镜像内置
4. 操作系统环境变量                 # 宿主机继承
```

---

### 6.1.6 WORKDIR与USER:安全上下文设置

```dockerfile
# ❌ 反模式:使用root用户运行
FROM python:3.11-slim
COPY app.py /root/
CMD ["python", "/root/app.py"]

# ✅ 最佳实践:非特权用户
FROM python:3.11-slim

# 创建应用用户(UID 1000)
RUN groupadd -r appuser -g 1000 && \
    useradd -r -u 1000 -g appuser -d /app -s /sbin/nologin appuser

# 设置工作目录并授权
WORKDIR /app
RUN chown -R appuser:appuser /app

# 安装依赖(需要root权限)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 切换到非特权用户
USER appuser

# 复制应用代码(已经以appuser身份)
COPY --chown=appuser:appuser . .

CMD ["python", "app.py"]
```

**用户切换时机验证**:

```bash
# 验证进程用户
$ docker exec myapp ps aux
USER       PID  COMMAND
appuser      1  python app.py  # ✅ 非root

# 验证文件权限
$ docker exec myapp ls -la /app
drwxr-xr-x appuser appuser /app
-rw-r--r-- appuser appuser app.py
```

---

## 6.2 Dockerfile分层优化实战

### 6.2.1 层缓存机制深度剖析

```dockerfile
# 缓存失效场景演示
FROM python:3.11-slim

# 层1:基础镜像(缓存稳定)
RUN apt-get update && apt-get install -y gcc

# 层2:requirements.txt变更后,此层缓存失效
COPY requirements.txt .
RUN pip install -r requirements.txt  # 重新执行

# 层3:依赖层2,缓存也失效
COPY . /app  # 重新复制

# ✅ 优化策略:分离变化频率
FROM python:3.11-slim

# 1️⃣ 系统依赖(几乎不变)
RUN apt-get update && apt-get install -y gcc \
 && rm -rf /var/lib/apt/lists/*

# 2️⃣ Python依赖(偶尔变化)
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# 3️⃣ 应用代码(频繁变化)
WORKDIR /app
COPY . .

# 场景:修改app.py后重新构建
# - 层1和层2使用缓存 ✅
# - 仅层3重新构建 ✅
```

**缓存命中判断逻辑**:

```bash
# Docker判断缓存命中的依据:
1. COPY/ADD:文件内容SHA256哈希
2. RUN:指令字符串完全匹配
3. ENV/ARG:变量值完全匹配
4. FROM:基础镜像digest匹配

# 查看缓存命中情况
$ docker build --progress=plain .
#1 [internal] load build definition
#2 [internal] load .dockerignore
#3 [1/4] FROM python:3.11-slim
#3 CACHED  # ✅ 缓存命中
#4 [2/4] RUN apt-get update
#4 CACHED  # ✅ 缓存命中
#5 [3/4] COPY requirements.txt
#5 CACHED  # ✅ 缓存命中
#6 [4/4] COPY . /app
#6 0.234s  # ❌ 缓存失效,重新执行
```

---

### 6.2.2 .dockerignore文件最佳实践

```bash
# .dockerignore 完整示例
# ============================
# 版本控制文件
.git/
.gitignore
.gitattributes

# 构建产物
node_modules/
dist/
build/
*.pyc
__pycache__/
.pytest_cache/
.mypy_cache/

# IDE配置
.vscode/
.idea/
*.swp
*.swo
*~

# 环境变量(敏感信息)
.env
.env.local
*.key
*.pem

# 日志文件
*.log
logs/

# 文档和测试
README.md
docs/
tests/
*.test.js

# CI/CD配置
.github/
.gitlab-ci.yml
Jenkinsfile

# Docker相关
Dockerfile*
docker-compose*.yml
.dockerignore

# OS文件
.DS_Store
Thumbs.db
```

**性能影响实测**:

```bash
# 无.dockerignore
$ docker build -t myapp:v1 .
Sending build context to Docker daemon  523.4MB  # ⚠️ 包含node_modules
Step 1/8: FROM node:18-alpine
Step 2/8: COPY . /app
 ---> 98.3s  # 复制大量无用文件

# 有.dockerignore
$ docker build -t myapp:v2 .
Sending build context to Docker daemon  2.3MB    # ✅ 仅必要文件
Step 1/8: FROM node:18-alpine
Step 2/8: COPY . /app
 ---> 0.5s   # 构建速度提升 196倍
```

---

### 6.2.3 镜像层数优化策略

```dockerfile
# ❌ 反模式:过多层数(镜像大小 500MB)
FROM ubuntu:22.04
RUN apt-get update
RUN apt-get install -y python3
RUN apt-get install -y python3-pip
RUN apt-get install -y git
RUN apt-get install -y curl
COPY requirements.txt /tmp/
RUN pip3 install flask
RUN pip3 install requests
RUN pip3 install sqlalchemy
COPY app.py /app/
COPY config.py /app/

# ✅ 最佳实践:合并层(镜像大小 180MB)
FROM ubuntu:22.04

# 单层安装所有系统依赖
RUN apt-get update && apt-get install -y \
    python3=3.10.6-1~22.04 \
    python3-pip=22.0.2+dfsg-1ubuntu0.4 \
    git=1:2.34.1-1ubuntu1.10 \
    curl=7.81.0-1ubuntu1.15 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# 单层安装所有Python依赖
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt \
 && rm /tmp/requirements.txt

# 单层复制所有应用文件
COPY app.py config.py /app/

# 层数对比:
# 反模式: 11层
# 最佳实践: 4层(基础镜像 + 3个自定义层)
```

---

### 6.2.4 包管理器缓存清理技巧

```dockerfile
# ✅ Debian/Ubuntu:apt-get清理
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y \
    nginx \
    curl \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# ✅ Alpine:apk清理
FROM alpine:3.19
RUN apk add --no-cache \
    nginx \
    curl

# ✅ Python:pip清理
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ✅ Node.js:npm清理
FROM node:18-alpine
COPY package*.json ./
RUN npm ci --only=production \
 && npm cache clean --force

# ✅ Go:构建后删除编译缓存
FROM golang:1.21-alpine AS builder
WORKDIR /build
COPY . .
RUN go mod download \
 && CGO_ENABLED=0 go build -o app \
 && rm -rf /root/.cache/go-build

# ⚠️ 错误示例:清理无效
RUN apt-get update
RUN apt-get install -y nginx
RUN rm -rf /var/lib/apt/lists/*  # ❌ 前两层已固化,清理无效
```

---

## 6.3 多阶段构建深度实战

### 6.3.1 Go应用多阶段构建

```dockerfile
# ===============================
# 阶段1:构建阶段
# ===============================
FROM golang:1.21.5-alpine AS builder

# 安装编译依赖
RUN apk add --no-cache git make

WORKDIR /build

# 利用缓存:先下载依赖
COPY go.mod go.sum ./
RUN go mod download

# 复制源码并编译
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags="-s -w -X main.version=${VERSION}" \
    -o app \
    ./cmd/server

# ===============================
# 阶段2:运行时阶段
# ===============================
FROM alpine:3.19

# 安装运行时依赖
RUN apk add --no-cache ca-certificates tzdata

# 创建非特权用户
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# 从构建阶段复制二进制文件
COPY --from=builder /build/app /usr/local/bin/app
COPY --from=builder /build/configs /etc/app/

# 设置时区
ENV TZ=Asia/Shanghai

USER appuser
EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/app"]
CMD ["--config", "/etc/app/config.yaml"]

# 镜像大小对比:
# 单阶段构建: 850MB (包含Go SDK和编译缓存)
# 多阶段构建: 12MB  (仅包含二进制文件和运行时依赖)
```

---

### 6.3.2 Java应用多阶段构建(Spring Boot)

```dockerfile
# ===============================
# 阶段1:Maven构建
# ===============================
FROM maven:3.9.6-eclipse-temurin-17 AS builder

WORKDIR /build

# 利用缓存:先解析依赖
COPY pom.xml .
RUN mvn dependency:go-offline -B

# 复制源码并打包
COPY src ./src
RUN mvn clean package -DskipTests -B \
 && mv target/*.jar app.jar

# ===============================
# 阶段2:JRE运行时
# ===============================
FROM eclipse-temurin:17-jre-alpine

# 安装诊断工具(可选)
RUN apk add --no-cache curl

# 创建应用用户
RUN addgroup -S spring && adduser -S spring -G spring
USER spring:spring

WORKDIR /app

# 从构建阶段复制JAR
COPY --from=builder /build/app.jar .

# JVM参数优化
ENV JAVA_OPTS="-XX:+UseContainerSupport \
               -XX:MaxRAMPercentage=75.0 \
               -XX:InitialRAMPercentage=50.0 \
               -XX:+UseG1GC \
               -XX:MaxGCPauseMillis=200 \
               -Djava.security.egd=file:/dev/./urandom"

EXPOSE 8080

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]

# 镜像大小对比:
# 单阶段(Maven): 780MB
# 多阶段(JRE): 210MB (减少73%)
```

**Spring Boot分层JAR优化**:

```dockerfile
# ===============================
# Spring Boot 2.3+ 分层优化
# ===============================
FROM maven:3.9-temurin-17 AS builder
WORKDIR /build
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src ./src
RUN mvn package -DskipTests
RUN java -Djarmode=layertools -jar target/*.jar extract

# ===============================
# 运行时:分层复制
# ===============================
FROM eclipse-temurin:17-jre-alpine

RUN addgroup -S spring && adduser -S spring -G spring
USER spring:spring
WORKDIR /app

# 按依赖变化频率分层复制
COPY --from=builder /build/dependencies/ ./
COPY --from=builder /build/spring-boot-loader/ ./
COPY --from=builder /build/snapshot-dependencies/ ./
COPY --from=builder /build/application/ ./

ENTRYPOINT ["java", "org.springframework.boot.loader.JarLauncher"]

# 优势:修改代码后,仅application层失效
# dependencies层(Maven依赖)保持缓存 ✅
```

---

### 6.3.3 Node.js应用多阶段构建

```dockerfile
# ===============================
# 阶段1:依赖安装与构建
# ===============================
FROM node:18.19.0-alpine AS builder

# 安装构建工具
RUN apk add --no-cache python3 make g++

WORKDIR /build

# 利用缓存:先安装依赖
COPY package*.json ./
RUN npm ci --only=production \
 && cp -R node_modules /tmp/node_modules \
 && npm ci  # 安装开发依赖用于构建

# 复制源码并构建
COPY . .
RUN npm run build  # TypeScript编译或Webpack打包

# ===============================
# 阶段2:生产运行时
# ===============================
FROM node:18.19.0-alpine

# 安装dumb-init(处理信号转发)
RUN apk add --no-cache dumb-init

# 创建应用用户
RUN addgroup -g 1001 nodejs && adduser -u 1001 -G nodejs -s /bin/sh -D nodejs

WORKDIR /app

# 从builder复制生产依赖
COPY --from=builder /tmp/node_modules ./node_modules
# 从builder复制构建产物
COPY --from=builder /build/dist ./dist
COPY --from=builder /build/package.json ./

USER nodejs

EXPOSE 3000

# 使用dumb-init处理信号
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "dist/main.js"]

# 镜像大小对比:
# 单阶段: 450MB (包含devDependencies和源码)
# 多阶段: 120MB (仅生产依赖和编译后代码)
```

---

### 6.3.4 Python应用多阶段构建

```dockerfile
# ===============================
# 阶段1:依赖编译
# ===============================
FROM python:3.11.7-slim AS builder

# 安装编译依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# 创建虚拟环境
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 利用缓存:先安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ===============================
# 阶段2:运行时
# ===============================
FROM python:3.11.7-slim

# 仅安装运行时库
RUN apt-get update && apt-get install -y \
    libpq5 \
 && rm -rf /var/lib/apt/lists/*

# 创建应用用户
RUN useradd -m -u 1000 appuser

WORKDIR /app

# 从builder复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 复制应用代码
COPY --chown=appuser:appuser . .

# 设置环境变量
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# 镜像大小对比:
# 单阶段: 1.2GB (包含gcc等编译工具)
# 多阶段: 280MB (仅运行时依赖)
```

---

### 6.3.5 多阶段构建高级技巧

```dockerfile
# ✅ 技巧1:命名阶段并选择性复制
FROM golang:1.21-alpine AS go-builder
WORKDIR /build
COPY . .
RUN go build -o api ./cmd/api

FROM node:18-alpine AS node-builder
WORKDIR /build
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# 最终镜像:同时使用两个构建阶段
FROM alpine:3.19
COPY --from=go-builder /build/api /usr/local/bin/
COPY --from=node-builder /build/dist /var/www/html/

# ✅ 技巧2:使用外部镜像作为阶段
FROM nginx:1.25-alpine AS nginx-config
RUN nginx -V  # 获取编译参数

FROM alpine:3.19
COPY --from=nginx-config /etc/nginx /etc/nginx
COPY --from=nginx-config /usr/sbin/nginx /usr/sbin/nginx

# ✅ 技巧3:构建参数控制阶段选择
ARG BUILD_ENV=production

FROM maven:3.9-temurin-17 AS builder-dev
WORKDIR /build
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src ./src
RUN mvn package

FROM maven:3.9-temurin-17 AS builder-prod
WORKDIR /build
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src ./src
RUN mvn package -Pprod -DskipTests

# 根据BUILD_ENV选择构建阶段
FROM builder-${BUILD_ENV} AS final-builder

FROM eclipse-temurin:17-jre-alpine
COPY --from=final-builder /build/target/*.jar app.jar
CMD ["java", "-jar", "app.jar"]

# 构建命令:
$ docker build --build-arg BUILD_ENV=dev -t myapp:dev .
$ docker build --build-arg BUILD_ENV=prod -t myapp:prod .
```

---

## 6.4 镜像体积优化实战

### 6.4.1 基础镜像选择优化

```dockerfile
# 对比不同基础镜像大小

# ❌ 完整Ubuntu镜像
FROM ubuntu:22.04
# 镜像大小: 77MB

# ⚠️ Debian Slim
FROM debian:bookworm-slim
# 镜像大小: 74MB

# ✅ Alpine Linux
FROM alpine:3.19
# 镜像大小: 7.3MB

# ⭐ Distroless(Google)
FROM gcr.io/distroless/static-debian12
# 镜像大小: 2.4MB
# 特点:无shell,无包管理器,仅运行时库

# ⭐⭐ Scratch(空镜像)
FROM scratch
# 镜像大小: 0KB
# 适用:静态编译的Go/Rust应用
```

**实战:Go应用使用scratch**:

```dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /build
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo \
    -ldflags '-extldflags "-static" -s -w' \
    -o app .

FROM scratch
# 添加CA证书(HTTPS请求需要)
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
# 添加时区数据
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo
# 复制二进制文件
COPY --from=builder /build/app /app

ENTRYPOINT ["/app"]

# 最终镜像大小: 仅6-10MB(取决于应用代码)
```

---

### 6.4.2 依赖精简与裁剪

```dockerfile
# ❌ 反模式:安装完整工具链
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libpq-dev \
    curl \
    wget \
    vim \
    git
# 额外增加: 500MB+

# ✅ 最佳实践:仅安装运行时依赖
FROM python:3.11-slim

# 分离编译依赖和运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 仅运行时需要的库
    libpq5=15.5-0+deb12u1 \
 && rm -rf /var/lib/apt/lists/*

# 编译阶段在builder镜像中完成(见多阶段构建)
```

**Python依赖优化**:

```dockerfile
FROM python:3.11-slim AS builder

# 仅在构建阶段安装编译依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.11-slim
RUN apt-get update && apt-get install -y libpq5 && rm -rf /var/lib/apt/lists/*
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* \
 && rm -rf /wheels

# 优化效果:
# 单阶段(含gcc): 850MB
# 多阶段优化: 180MB (减少79%)
```

---

### 6.4.3 文件与缓存清理技巧

```dockerfile
# ✅ 完整的清理策略
FROM python:3.11-slim

# 单层执行:安装+清理
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    # 清理apt缓存
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* \
    # 清理临时文件
    /tmp/* \
    /var/tmp/* \
    # 清理日志
    /var/log/*.log \
    # 清理pip缓存
    ~/.cache/pip \
    # 清理Python缓存
    /root/.cache

# pip安装时禁用缓存
RUN pip install --no-cache-dir \
    flask==3.0.0 \
    requests==2.31.0

# 复制代码后清理不必要文件
COPY . /app
WORKDIR /app
RUN find . -type f -name '*.pyc' -delete \
 && find . -type d -name '__pycache__' -delete \
 && find . -type d -name '.pytest_cache' -delete \
 && find . -type f -name '*.log' -delete

# Node.js清理示例
RUN npm ci --only=production \
 && npm cache clean --force \
 && rm -rf /root/.npm /tmp/*

# Alpine清理示例
RUN apk add --no-cache nginx \
 && rm -rf /var/cache/apk/*
```

---

### 6.4.4 镜像压缩与导出

```bash
# 方法1:使用docker-slim自动瘦身
$ docker-slim build --http-probe=false myapp:v1
# 原始大小: 450MB
# 优化后: 85MB (减少81%)

# docker-slim工作原理:
# 1. 运行容器并监控系统调用
# 2. 识别实际使用的文件和库
# 3. 创建仅包含必要文件的新镜像

# 方法2:手动导出导入(压平层)
$ docker export mycontainer > app.tar
$ docker import app.tar myapp:slim
# 优势:所有层合并为一层
# 劣势:丢失历史记录和层缓存

# 方法3:使用squash(实验性功能)
$ docker build --squash -t myapp:squashed .
# 合并所有层为单层,减少元数据开销

# 方法4:使用crane优化镜像
$ crane flatten myapp:v1 myapp:flat
# Google出品工具,优化层结构
```

---

## 6.5 Dockerfile安全最佳实践

### 6.5.1 最小权限原则

```dockerfile
# ❌ 反模式:使用root用户
FROM nginx:alpine
COPY nginx.conf /etc/nginx/
CMD ["nginx", "-g", "daemon off;"]

# 运行时:
$ docker exec mynginx whoami
root  # ⚠️ 容器逃逸风险

# ✅ 最佳实践:非特权用户
FROM nginx:alpine

# 修改nginx配置允许非root运行
RUN sed -i 's/user nginx;/user nginx;/g' /etc/nginx/nginx.conf \
 && sed -i 's/listen 80;/listen 8080;/g' /etc/nginx/conf.d/default.conf \
 && chown -R nginx:nginx /var/cache/nginx /var/run /var/log/nginx

USER nginx
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]

# ✅ 自定义应用示例
FROM python:3.11-alpine

# 创建专用用户(UID 10000)
RUN addgroup -g 10000 appgroup \
 && adduser -D -u 10000 -G appgroup appuser

WORKDIR /app
COPY --chown=appuser:appgroup . .

# 确保日志目录可写
RUN mkdir -p /app/logs && chown appuser:appgroup /app/logs

USER appuser

CMD ["python", "app.py"]
```

---

### 6.5.2 避免敏感信息泄露

```dockerfile
# ❌ 反模式:硬编码密钥
FROM python:3.11-slim
ENV DATABASE_PASSWORD=secret123  # ⚠️ 明文密码

# 查看镜像历史会暴露密码:
$ docker history myapp:v1
IMAGE          CREATED BY
<missing>      ENV DATABASE_PASSWORD=secret123  # ❌ 泄露!

# ✅ 最佳实践1:使用secrets
FROM python:3.11-slim
# 不在镜像中存储密码
CMD ["python", "app.py"]

# 运行时注入:
$ docker run -e DATABASE_PASSWORD=secret123 myapp:v1
# 或使用secrets文件:
$ docker run --env-file .env myapp:v1

# ✅ 最佳实践2:多阶段构建隐藏构建密钥
FROM golang:1.21-alpine AS builder
# 构建时需要私钥拉取私有仓库
RUN --mount=type=secret,id=github_token \
    git config --global url."https://$(cat /run/secrets/github_token)@github.com/".insteadOf "https://github.com/" \
 && go mod download

FROM alpine:3.19
COPY --from=builder /build/app /app
# 最终镜像不包含github_token ✅

# 构建命令:
$ docker build --secret id=github_token,src=token.txt -t myapp .

# ✅ 最佳实践3:使用.dockerignore排除敏感文件
# .dockerignore内容:
.env
.env.local
*.key
*.pem
credentials.json
secrets/
```

---

### 6.5.3 镜像签名与验证

```dockerfile
# Docker Content Trust (DCT)启用

# 1️⃣ 启用DCT
$ export DOCKER_CONTENT_TRUST=1

# 2️⃣ 推送镜像时自动签名
$ docker push myregistry.com/myapp:v1.0
# 提示输入root key和repository key密码
# 签名存储在Notary服务器

# 3️⃣ 拉取镜像时自动验证
$ docker pull myregistry.com/myapp:v1.0
Pull (1 of 1): myapp:v1.0@sha256:abc123...
Tagging myregistry.com/myapp:v1.0@sha256:abc123 as myapp:v1.0
# ✅ 签名验证通过

# 4️⃣ 签名验证失败示例
$ docker pull myregistry.com/tampered:latest
Error: remote trust data does not exist  # ❌ 无签名或签名无效

# ✅ 使用Cosign签名(推荐)
# 安装cosign
$ brew install cosign

# 生成密钥对
$ cosign generate-key-pair

# 签名镜像
$ cosign sign --key cosign.key myregistry.com/myapp:v1.0

# 验证镜像
$ cosign verify --key cosign.pub myregistry.com/myapp:v1.0
# ✅ Verification successful!
```

---

### 6.5.4 镜像漏洞扫描

```bash
# 工具1:Trivy扫描
$ trivy image myapp:v1.0
myapp:v1.0 (debian 12.4)
==========================
Total: 45 (UNKNOWN: 0, LOW: 18, MEDIUM: 20, HIGH: 5, CRITICAL: 2)

┌─────────────────┬─────────────────┬──────────┬────────────────┬───────────────────┬────────────────────┐
│    Library      │  Vulnerability  │ Severity │ Installed Ver  │   Fixed Version   │       Title        │
├─────────────────┼─────────────────┼──────────┼────────────────┼───────────────────┼────────────────────┤
│ openssl         │ CVE-2023-12345  │ CRITICAL │ 3.0.2-0deb12u1 │ 3.0.2-0deb12u2    │ OpenSSL buffer ... │
│ curl            │ CVE-2023-54321  │ HIGH     │ 7.88.1-10      │ 7.88.1-10+deb12u1 │ curl HTTPS proxy..│
└─────────────────┴─────────────────┴──────────┴────────────────┴───────────────────┴────────────────────┘

# 工具2:Grype扫描
$ grype myapp:v1.0
NAME       INSTALLED  VULNERABILITY  SEVERITY
openssl    3.0.2      CVE-2023-12345 Critical
curl       7.88.1     CVE-2023-54321 High

# 工具3:Clair(Red Hat)
$ clairctl report myapp:v1.0

# 工具4:Docker Scout(官方)
$ docker scout cves myapp:v1.0
    ✓ Image stored for indexing
    ✓ Indexed 178 packages
    ✓ No vulnerable package detected

# CI集成:GitHub Actions示例
# .github/workflows/security-scan.yml
name: Security Scan
on: [push]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build image
        run: docker build -t myapp:${{ github.sha }} .
      - name: Run Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: myapp:${{ github.sha }}
          severity: 'CRITICAL,HIGH'
          exit-code: '1'  # 发现漏洞则失败
```

---

### 6.5.5 只读文件系统与安全配置

```dockerfile
# Dockerfile:支持只读文件系统
FROM python:3.11-alpine

RUN adduser -D appuser

WORKDIR /app
COPY --chown=appuser:appuser . .

# 创建可写目录(只读模式下仍需要)
RUN mkdir -p /tmp/app-cache /tmp/app-logs \
 && chown appuser:appuser /tmp/app-cache /tmp/app-logs

USER appuser

# 应用配置:使用/tmp作为临时目录
ENV TMPDIR=/tmp/app-cache

CMD ["python", "app.py"]

# 运行时配置:
$ docker run -d \
  --name myapp \
  --read-only \  # ✅ 启用只读文件系统
  --tmpfs /tmp:rw,noexec,nosuid,size=100m \  # 挂载临时目录
  --security-opt=no-new-privileges:true \  # 禁止权限提升
  --cap-drop=ALL \  # 移除所有capabilities
  --cap-add=NET_BIND_SERVICE \  # 仅添加必要的capability
  myapp:v1.0

# 验证只读文件系统:
$ docker exec myapp touch /test.txt
touch: /test.txt: Read-only file system  # ✅ 符合预期

$ docker exec myapp touch /tmp/app-cache/test.txt
# ✅ 成功创建(tmpfs可写)
```

---

## 6.6 构建性能优化

### 6.6.1 BuildKit特性

```bash
# 启用BuildKit(Docker 18.09+)
$ export DOCKER_BUILDKIT=1
$ docker build -t myapp:v1 .

# BuildKit优势:
# 1. 并行构建无依赖的阶段
# 2. 跳过未使用的阶段
# 3. 更好的缓存管理
# 4. 构建时secrets支持

# ✅ 并行构建示例
FROM alpine:3.19 AS stage1
RUN sleep 10 && echo "Stage 1 done"

FROM alpine:3.19 AS stage2
RUN sleep 10 && echo "Stage 2 done"

FROM alpine:3.19
COPY --from=stage1 /etc/alpine-release /stage1
COPY --from=stage2 /etc/alpine-release /stage2

# 传统模式:串行执行,总耗时20秒
# BuildKit:并行执行,总耗时10秒 ⚡

# ✅ 缓存挂载(cache mount)
FROM golang:1.21-alpine
RUN --mount=type=cache,target=/root/.cache/go-build \
    --mount=type=cache,target=/go/pkg/mod \
    go build -o app .

# 效果:go build缓存持久化,重复构建速度提升10倍

# ✅ 构建时secrets
FROM alpine:3.19
RUN --mount=type=secret,id=npm_token \
    echo "//registry.npmjs.org/:_authToken=$(cat /run/secrets/npm_token)" > ~/.npmrc \
 && npm install

# 构建命令:
$ docker build --secret id=npm_token,src=token.txt -t myapp .

# ✅ SSH agent转发
FROM alpine:3.19
RUN apk add git openssh-client
RUN --mount=type=ssh \
    git clone git@github.com:private/repo.git

# 构建命令:
$ docker build --ssh default -t myapp .
```

---

### 6.6.2 缓存优化策略

```dockerfile
# ✅ 策略1:按变更频率分层
FROM node:18-alpine

# 1️⃣ 安装全局工具(几乎不变)
RUN npm install -g pnpm@8.15.0

# 2️⃣ 复制lock文件(偶尔变更)
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# 3️⃣ 复制源码(频繁变更)
COPY src ./src
RUN pnpm build

# ✅ 策略2:利用.dockerignore减少缓存失效
# .dockerignore内容:
node_modules/
dist/
*.log
.git/

# 不包含README.md变更不会导致COPY层失效

# ✅ 策略3:使用通配符复制特定文件
COPY package*.json ./  # 仅复制package.json和package-lock.json
RUN npm ci

COPY src/ ./src/       # 仅复制src目录
COPY *.config.js ./    # 仅复制配置文件

# ✅ 策略4:BuildKit缓存后端
# 使用本地缓存:
$ docker build --cache-from=type=local,src=/tmp/cache \
               --cache-to=type=local,dest=/tmp/cache \
               -t myapp .

# 使用Registry缓存:
$ docker build --cache-from=myregistry.com/myapp:cache \
               --cache-to=type=registry,ref=myregistry.com/myapp:cache \
               -t myapp .

# CI环境示例(GitHub Actions)
- name: Build with cache
  uses: docker/build-push-action@v5
  with:
    context: .
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

---

### 6.6.3 构建时间对比

```bash
# 场景:Node.js应用构建优化对比

# ❌ 未优化Dockerfile:
FROM node:18
COPY . /app
WORKDIR /app
RUN npm install
RUN npm run build
CMD ["node", "dist/main.js"]

# 初次构建: 180秒
# 修改代码后: 175秒 (缓存几乎无效)

# ✅ 优化后Dockerfile:
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production \
 && cp -R node_modules /tmp/prod_modules \
 && npm ci
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /tmp/prod_modules ./node_modules
COPY --from=builder /app/dist ./dist
CMD ["node", "dist/main.js"]

# 初次构建: 120秒 (减少33%)
# 修改代码后: 8秒 (缓存有效,减少96%)

# 性能提升总结:
# - 使用alpine: -30% 镜像大小
# - 分离依赖安装: +95% 缓存命中率
# - 多阶段构建: -65% 最终镜像大小
# - 清理缓存: -20% 层大小
```

---

## 6.7 生产环境Dockerfile模板

### 6.7.1 Go微服务模板

```dockerfile
# ==============================================
# 多阶段构建 - Go微服务生产模板
# ==============================================
ARG GO_VERSION=1.21.5
ARG ALPINE_VERSION=3.19

# ================ 构建阶段 ================
FROM golang:${GO_VERSION}-alpine AS builder

# 安装编译依赖
RUN apk add --no-cache git make ca-certificates tzdata

WORKDIR /build

# 利用缓存:先下载依赖
COPY go.mod go.sum ./
RUN go mod download && go mod verify

# 复制源码
COPY . .

# 编译参数优化
ARG VERSION=dev
ARG BUILD_TIME
ARG COMMIT_SHA

RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -a -installsuffix cgo \
    -ldflags="-s -w \
              -X main.version=${VERSION} \
              -X main.buildTime=${BUILD_TIME} \
              -X main.commitSHA=${COMMIT_SHA}" \
    -o app \
    ./cmd/server

# 验证二进制文件
RUN ./app --version

# ================ 运行阶段 ================
FROM alpine:${ALPINE_VERSION}

# 安装运行时依赖
RUN apk add --no-cache ca-certificates tzdata \
 && addgroup -S appgroup -g 10000 \
 && adduser -S appuser -u 10000 -G appgroup

# 从构建阶段复制文件
COPY --from=builder /build/app /usr/local/bin/app
COPY --from=builder /build/configs /etc/app/

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["/usr/local/bin/app", "healthcheck"]

# 设置时区
ENV TZ=Asia/Shanghai

USER appuser
WORKDIR /home/appuser

EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/app"]
CMD ["--config", "/etc/app/config.yaml"]

# 构建命令:
# docker build \
#   --build-arg VERSION=1.0.0 \
#   --build-arg BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
#   --build-arg COMMIT_SHA=$(git rev-parse HEAD) \
#   -t myapp:1.0.0 .
```

---

### 6.7.2 Python Web应用模板

```dockerfile
# ==============================================
# 多阶段构建 - Python生产模板
# ==============================================
ARG PYTHON_VERSION=3.11.7

# ================ 依赖编译阶段 ================
FROM python:${PYTHON_VERSION}-slim AS builder

# 安装编译依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
 && rm -rf /var/lib/apt/lists/*

# 创建虚拟环境
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 升级pip工具
RUN pip install --no-cache-dir -U pip setuptools wheel

# 安装依赖
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ================ 运行阶段 ================
FROM python:${PYTHON_VERSION}-slim

# 安装运行时库
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# 创建应用用户
RUN groupadd -r appuser -g 10000 \
 && useradd -r -u 10000 -g appuser -d /app -s /sbin/nologin appuser

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

# 复制应用代码
COPY --chown=appuser:appuser . .

# 环境变量
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

USER appuser

EXPOSE 8000

# 使用Gunicorn运行
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "main:app"]
```

---

### 6.7.3 Node.js应用模板

```dockerfile
# ==============================================
# 多阶段构建 - Node.js生产模板
# ==============================================
ARG NODE_VERSION=18.19.0

# ================ 依赖安装阶段 ================
FROM node:${NODE_VERSION}-alpine AS deps

RUN apk add --no-cache libc6-compat python3 make g++

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --only=production \
 && cp -R node_modules /tmp/prod_modules \
 && npm ci  # 安装全部依赖用于构建

# ================ 构建阶段 ================
FROM node:${NODE_VERSION}-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# TypeScript编译或Webpack打包
RUN npm run build

# ================ 运行阶段 ================
FROM node:${NODE_VERSION}-alpine

# 安装dumb-init和安全更新
RUN apk add --no-cache dumb-init \
 && apk upgrade --no-cache

# 创建应用用户
RUN addgroup -g 10000 nodejs \
 && adduser -u 10000 -G nodejs -s /bin/sh -D nodejs

WORKDIR /app

# 从依赖阶段复制生产依赖
COPY --from=deps /tmp/prod_modules ./node_modules
# 从构建阶段复制编译产物
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./

# 环境变量
ENV NODE_ENV=production \
    NODE_OPTIONS="--max-old-space-size=2048"

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node healthcheck.js

USER nodejs

EXPOSE 3000

# 使用dumb-init处理信号
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "dist/main.js"]
```

---

## 6.8 本章总结与检查清单

### 6.8.1 Dockerfile代码审查清单

```markdown
## 基础配置
- [ ] 使用明确的基础镜像版本(带digest)
- [ ] 选择合适的基础镜像(alpine/slim/distroless)
- [ ] 设置LABEL元数据(maintainer, version等)

## 安全性
- [ ] 使用非root用户运行(USER指令)
- [ ] 不在镜像中硬编码敏感信息
- [ ] 通过.dockerignore排除敏感文件
- [ ] 启用只读文件系统(运行时--read-only)
- [ ] 移除不必要的系统工具(shell, package manager)

## 镜像大小
- [ ] 使用多阶段构建
- [ ] 合并RUN指令减少层数
- [ ] 清理包管理器缓存
- [ ] 删除临时文件和日志
- [ ] 仅安装必要的运行时依赖

## 构建性能
- [ ] 按变更频率排序指令(依赖在前,代码在后)
- [ ] 使用.dockerignore减少构建上下文
- [ ] 利用BuildKit缓存特性
- [ ] 使用缓存挂载(--mount=type=cache)

## 运行时
- [ ] 设置HEALTHCHECK健康检查
- [ ] 使用Exec格式的CMD/ENTRYPOINT
- [ ] 设置合理的EXPOSE端口
- [ ] 配置适当的环境变量
- [ ] 使用dumb-init处理信号(Node.js)

## 可维护性
- [ ] 添加注释说明复杂逻辑
- [ ] 使用ARG支持构建参数化
- [ ] 版本信息编译到二进制(ldflags)
- [ ] 遵循项目命名规范
```

---

### 6.8.2 镜像质量指标

```bash
# 1️⃣ 镜像大小
$ docker images myapp
REPOSITORY   TAG   SIZE
myapp        v1    15MB    # ✅ 优秀: <50MB
myapp        v2    180MB   # ⚠️ 可接受: 50-300MB
myapp        v3    850MB   # ❌ 需优化: >300MB

# 2️⃣ 层数
$ docker history myapp:v1 | wc -l
8  # ✅ 优秀: <10层

# 3️⃣ 漏洞数量
$ trivy image myapp:v1
Total: 0 (CRITICAL: 0, HIGH: 0)  # ✅ 目标

# 4️⃣ 构建时间
$ time docker build -t myapp:v1 .
real    0m45.234s  # ✅ 首次构建<2分钟
real    0m5.123s   # ✅ 缓存构建<10秒

# 5️⃣ 启动时间
$ docker run -d myapp:v1
$ docker logs myapp
Server started in 1.2s  # ✅ <5秒启动
```

---

---

# 第7章:镜像仓库与分发管理

## 7.1 Docker Registry深度剖析

### 7.1.1 Docker Hub使用进阶

```bash
# 登录Docker Hub
$ docker login
Username: myusername
Password:
Login Succeeded

# 标记镜像
$ docker tag myapp:latest myusername/myapp:1.0.0
$ docker tag myapp:latest myusername/myapp:latest

# 推送镜像
$ docker push myusername/myapp:1.0.0
$ docker push myusername/myapp:latest

# 搜索镜像
$ docker search nginx
NAME                DESCRIPTION                     STARS  OFFICIAL
nginx               Official build of Nginx         18000  [OK]
jwilder/nginx-proxy Automated Nginx reverse proxy   2200

# 限速与配额(免费账户)
# - Pull: 100次/6小时 (匿名用户)
# - Pull: 200次/6小时 (认证用户)
# - Push: 无限制
# - 存储: 1个私有仓库(免费版)

# 自动构建(Automated Builds)
# 1. 关联GitHub/GitLab仓库
# 2. 配置Dockerfile路径
# 3. 设置触发规则(push/tag)
# 4. Docker Hub自动构建并推送
```

**Docker Hub API使用**:

```bash
# 获取Token
$ TOKEN=$(curl -s -H "Content-Type: application/json" \
  -X POST -d '{"username":"'${DOCKER_USER}'","password":"'${DOCKER_PASS}'"}' \
  https://hub.docker.com/v2/users/login/ | jq -r .token)

# 列出仓库
$ curl -s -H "Authorization: Bearer $TOKEN" \
  https://hub.docker.com/v2/repositories/myusername/ | jq .

# 删除镜像标签
$ curl -X DELETE -H "Authorization: Bearer $TOKEN" \
  https://hub.docker.com/v2/repositories/myusername/myapp/tags/old-tag/

# 获取镜像manifest
$ curl -s -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
  https://registry-1.docker.io/v2/library/nginx/manifests/latest
```

---

### 7.1.2 私有Registry部署

**方式1:官方Registry镜像**:

```bash
# 启动基础Registry
$ docker run -d \
  --name registry \
  -p 5000:5000 \
  -v /data/registry:/var/lib/registry \
  --restart=always \
  registry:2

# 推送镜像到私有仓库
$ docker tag myapp:latest localhost:5000/myapp:latest
$ docker push localhost:5000/myapp:latest

# 查看仓库中的镜像
$ curl http://localhost:5000/v2/_catalog
{"repositories":["myapp"]}

# 查看镜像标签
$ curl http://localhost:5000/v2/myapp/tags/list
{"name":"myapp","tags":["latest","1.0.0"]}
```

**方式2:启用TLS和认证**:

```bash
# 1️⃣ 生成自签名证书
$ mkdir -p /data/certs
$ openssl req -newkey rsa:4096 -nodes -sha256 \
  -keyout /data/certs/domain.key \
  -x509 -days 365 -out /data/certs/domain.crt \
  -subj "/CN=registry.example.com"

# 2️⃣ 生成htpasswd认证文件
$ mkdir -p /data/auth
$ docker run --rm \
  --entrypoint htpasswd \
  httpd:2 -Bbn admin secretpass > /data/auth/htpasswd

# 3️⃣ 启动Registry with TLS + Auth
$ docker run -d \
  --name secure-registry \
  -p 443:5000 \
  -v /data/registry:/var/lib/registry \
  -v /data/certs:/certs \
  -v /data/auth:/auth \
  -e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/domain.crt \
  -e REGISTRY_HTTP_TLS_KEY=/certs/domain.key \
  -e REGISTRY_AUTH=htpasswd \
  -e REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd \
  -e REGISTRY_AUTH_HTPASSWD_REALM="Registry Realm" \
  --restart=always \
  registry:2

# 4️⃣ 客户端配置信任证书
$ sudo mkdir -p /etc/docker/certs.d/registry.example.com
$ sudo cp /data/certs/domain.crt /etc/docker/certs.d/registry.example.com/ca.crt

# 5️⃣ 登录并使用
$ docker login registry.example.com
Username: admin
Password: secretpass

$ docker push registry.example.com/myapp:latest
```

**Registry配置文件详解**:

```yaml
# /etc/docker/registry/config.yml
version: 0.1
log:
  level: info
  formatter: text
  fields:
    service: registry

storage:
  # 存储后端:filesystem / s3 / gcs / azure / swift
  filesystem:
    rootdirectory: /var/lib/registry
  delete:
    enabled: true  # 允许删除镜像
  cache:
    blobdescriptor: inmemory
  maintenance:
    uploadpurging:
      enabled: true
      age: 168h
      interval: 24h
      dryrun: false

http:
  addr: :5000
  secret: asecretforlocaldevelopment
  headers:
    X-Content-Type-Options: [nosniff]
  http2:
    disabled: false
  # 配置TLS
  tls:
    certificate: /certs/domain.crt
    key: /certs/domain.key

auth:
  htpasswd:
    realm: basic-realm
    path: /auth/htpasswd

# 健康检查
health:
  storagedriver:
    enabled: true
    interval: 10s
    threshold: 3

# 代理配置(缓存Docker Hub)
proxy:
  remoteurl: https://registry-1.docker.io
  username: [username]
  password: [password]

# Redis缓存(可选)
redis:
  addr: redis:6379
  password: secret
  db: 0
  dialtimeout: 10ms
  readtimeout: 10ms
  writetimeout: 10ms
  pool:
    maxidle: 16
    maxactive: 64
    idletimeout: 300s
```

---

### 7.1.3 Harbor企业级仓库

```yaml
# harbor docker-compose.yml简化版
version: '3'

services:
  registry:
    image: goharbor/registry-photon:v2.9.0
    volumes:
      - /data/registry:/storage
    networks:
      - harbor

  portal:
    image: goharbor/harbor-portal:v2.9.0
    networks:
      - harbor

  core:
    image: goharbor/harbor-core:v2.9.0
    env_file:
      - ./common/config/core/env
    volumes:
      - /data/ca_download/:/etc/core/ca/
      - /data/:/data/
    networks:
      - harbor
    depends_on:
      - registry

  jobservice:
    image: goharbor/harbor-jobservice:v2.9.0
    env_file:
      - ./common/config/jobservice/env
    volumes:
      - /data/job_logs:/var/log/jobs
    networks:
      - harbor

  redis:
    image: goharbor/redis-photon:v2.9.0
    networks:
      - harbor

  postgresql:
    image: goharbor/harbor-db:v2.9.0
    env_file:
      - ./common/config/db/env
    volumes:
      - /data/database:/var/lib/postgresql/data
    networks:
      - harbor

  nginx:
    image: goharbor/nginx-photon:v2.9.0
    ports:
      - 80:8080
      - 443:8443
    volumes:
      - ./common/config/nginx:/etc/nginx:z
    networks:
      - harbor
    depends_on:
      - core
      - portal

networks:
  harbor:
    external: false
```

**Harbor核心功能**:

```bash
# 1️⃣ 安装Harbor
$ wget https://github.com/goharbor/harbor/releases/download/v2.9.0/harbor-offline-installer-v2.9.0.tgz
$ tar xvf harbor-offline-installer-v2.9.0.tgz
$ cd harbor
$ cp harbor.yml.tmpl harbor.yml

# 编辑harbor.yml
$ vim harbor.yml
hostname: harbor.example.com
http:
  port: 80
https:
  port: 443
  certificate: /data/cert/server.crt
  private_key: /data/cert/server.key
harbor_admin_password: Harbor12345
database:
  password: root123

# 安装
$ sudo ./install.sh --with-trivy --with-chartmuseum

# 2️⃣ 使用Harbor CLI
$ docker login harbor.example.com
$ docker tag myapp:latest harbor.example.com/library/myapp:1.0.0
$ docker push harbor.example.com/library/myapp:1.0.0

# 3️⃣ 复制规则(跨Registry同步)
# Web UI: Administration → Replications → New Replication Rule
# - 源仓库: harbor-source
# - 目标仓库: harbor-target
# - 触发器: Manual / Scheduled / Event Based

# 4️⃣ 漏洞扫描(集成Trivy)
# Web UI: Projects → library → myapp → Scan
# 或通过API:
$ curl -X POST \
  -H "Authorization: Basic $(echo -n admin:Harbor12345 | base64)" \
  https://harbor.example.com/api/v2.0/projects/library/repositories/myapp/artifacts/1.0.0/scan

# 5️⃣ 镜像签名(Notary集成)
$ export DOCKER_CONTENT_TRUST=1
$ export DOCKER_CONTENT_TRUST_SERVER=https://harbor.example.com:4443
$ docker push harbor.example.com/library/myapp:signed
```

---

## 7.2 镜像分发优化

### 7.2.1 镜像加速器配置

```json
// /etc/docker/daemon.json
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://hub-mirror.c.163.com",
    "https://docker.mirrors.ustc.edu.cn"
  ],
  "max-concurrent-downloads": 10,
  "max-concurrent-uploads": 5
}
```

**性能对比**:

```bash
# 无加速器(国外直连Docker Hub)
$ time docker pull nginx:alpine
real    3m45.234s  # ⚠️ 3分45秒

# 启用国内加速器
$ sudo systemctl restart docker
$ time docker pull nginx:alpine
real    0m12.567s  # ✅ 12秒(提速18倍)
```

---

### 7.2.2 Registry代理缓存

```bash
# 部署Pull-through Cache Registry
$ docker run -d \
  --name registry-cache \
  -p 5000:5000 \
  -e REGISTRY_PROXY_REMOTEURL=https://registry-1.docker.io \
  -e REGISTRY_PROXY_USERNAME=dockerhub_user \
  -e REGISTRY_PROXY_PASSWORD=dockerhub_pass \
  -v /data/registry-cache:/var/lib/registry \
  --restart=always \
  registry:2

# 配置Docker使用缓存
$ cat /etc/docker/daemon.json
{
  "registry-mirrors": ["http://localhost:5000"]
}

# 首次拉取(从Docker Hub)
$ time docker pull nginx:alpine
real    0m45s  # 从Docker Hub下载

# 二次拉取(从缓存)
$ docker rmi nginx:alpine
$ time docker pull nginx:alpine
real    0m3s   # ✅ 从本地缓存,速度提升15倍
```

---

### 7.2.3 分层拉取优化

```bash
# 查看镜像层信息
$ docker inspect nginx:alpine | jq '.[0].RootFS.Layers'
[
  "sha256:abc123...",
  "sha256:def456...",
  "sha256:ghi789..."
]

# 并行下载层(daemon.json配置)
{
  "max-concurrent-downloads": 10,  # 并行下载层数
  "max-download-attempts": 5       # 下载失败重试次数
}

# 分层复用示例
$ docker pull python:3.11-alpine  # 下载3层,共50MB
$ docker pull python:3.11-slim     # 复用2层,仅新增1层(40MB)
# 实际下载: 50MB + 40MB = 90MB (而非110MB)
```

---

## 7.3 镜像清理与垃圾回收

### 7.3.1 客户端清理

```bash
# 删除未使用的镜像
$ docker image prune
WARNING! This will remove all dangling images.
Are you sure? [y/N] y
Deleted Images:
untagged: myapp@sha256:abc123...
deleted: sha256:def456...
Total reclaimed space: 1.2GB

# 删除所有未使用的镜像(包括有标签的)
$ docker image prune -a
Total reclaimed space: 5.8GB

# 删除特定时间前的镜像
$ docker image prune -a --filter "until=24h"

# 系统全面清理
$ docker system prune -a --volumes
WARNING! This will remove:
  - all stopped containers
  - all networks not used by at least one container
  - all volumes not used by at least one container
  - all images without at least one container associated to them
  - all build cache
Total reclaimed space: 12.4GB
```

---

### 7.3.2 Registry垃圾回收

```bash
# 1️⃣ 启用Registry删除功能
# /etc/docker/registry/config.yml
storage:
  delete:
    enabled: true

# 2️⃣ 通过API删除镜像标签
$ curl -X DELETE http://registry:5000/v2/myapp/manifests/sha256:abc123...

# 3️⃣ 运行垃圾回收
$ docker exec registry bin/registry garbage-collect /etc/docker/registry/config.yml
myapp: marking manifest sha256:abc123...
myapp: marking blob sha256:def456...
3 blobs marked, 2 blobs eligible for deletion
blob eligible for deletion: sha256:ghi789...
INFO[0001] Deleting blob: /docker/registry/v2/blobs/sha256/gh/ghi789...

# 删除前磁盘占用
$ du -sh /data/registry
5.2G    /data/registry

# 删除后磁盘占用
$ du -sh /data/registry
2.1G    /data/registry  # ✅ 回收3.1GB空间

# ⚠️ 垃圾回收注意事项:
# 1. 停止Registry服务再执行GC(避免并发问题)
# 2. GC过程中Registry只读
# 3. 定期执行(建议每周)
```

**自动化清理脚本**:

```bash
#!/bin/bash
# registry-gc.sh

REGISTRY_CONTAINER="registry"
REGISTRY_CONFIG="/etc/docker/registry/config.yml"

echo "=== Registry Garbage Collection ==="
echo "Starting at: $(date)"

# 1. 停止Registry
docker stop $REGISTRY_CONTAINER

# 2. 执行垃圾回收
docker run --rm \
  -v /data/registry:/var/lib/registry \
  -v /etc/docker/registry:/etc/docker/registry \
  registry:2 \
  garbage-collect $REGISTRY_CONFIG

# 3. 重启Registry
docker start $REGISTRY_CONTAINER

echo "Completed at: $(date)"

# 定时任务(每周日凌晨2点)
# 0 2 * * 0 /usr/local/bin/registry-gc.sh >> /var/log/registry-gc.log 2>&1
```

---

## 7.4 镜像迁移与备份

### 7.4.1 镜像导出导入

```bash
# 方式1:save/load(保留历史层)
$ docker save nginx:alpine > nginx-alpine.tar
$ docker save -o images.tar nginx:alpine mysql:8 redis:7
$ ls -lh images.tar
-rw-r--r-- 1 user user 512M Dec 4 10:00 images.tar

# 传输到其他机器
$ scp images.tar user@remote:/tmp/

# 导入镜像
$ docker load < images.tar
Loaded image: nginx:alpine
Loaded image: mysql:8
Loaded image: redis:7

# 方式2:export/import(压平层,丢失历史)
$ docker export mycontainer > app.tar
$ docker import app.tar myapp:slim

# 对比:
# save/load: 保留所有层,元数据完整,体积大
# export/import: 单层镜像,丢失历史,体积小
```

---

### 7.4.2 Registry间迁移

```bash
# 工具1:使用skopeo(推荐)
$ skopeo copy \
  docker://source-registry.com/myapp:1.0 \
  docker://target-registry.com/myapp:1.0 \
  --src-creds user1:pass1 \
  --dest-creds user2:pass2

# 批量迁移所有镜像
$ skopeo sync \
  --src docker --dest docker \
  --src-creds user1:pass1 \
  --dest-creds user2:pass2 \
  source-registry.com/library \
  target-registry.com/library

# 工具2:使用crane
$ crane copy \
  source-registry.com/myapp:1.0 \
  target-registry.com/myapp:1.0

# 工具3:使用Harbor复制规则(Web UI配置)
# Administration → Replications → New Replication Rule
```

---

### 7.4.3 Registry备份恢复

```bash
# 备份Registry数据
$ tar -czf registry-backup-$(date +%Y%m%d).tar.gz \
  -C /data registry

# 备份Harbor完整数据
$ cd /opt/harbor
$ docker-compose stop
$ tar -czf harbor-backup-$(date +%Y%m%d).tar.gz \
  -C /data \
  registry database redis

# 恢复Registry
$ tar -xzf registry-backup-20231204.tar.gz -C /data
$ docker start registry

# 恢复Harbor
$ cd /opt/harbor
$ docker-compose down
$ tar -xzf harbor-backup-20231204.tar.gz -C /data
$ docker-compose up -d
```

---

## 7.5 镜像安全扫描集成

### 7.5.1 Trivy集成

```bash
# 独立使用Trivy
$ trivy image nginx:alpine
nginx:alpine (alpine 3.19.0)
Total: 0 (UNKNOWN: 0, LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0)

# 集成到CI/CD(GitHub Actions)
name: Security Scan
on: [push]
jobs:
  trivy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build image
        run: docker build -t myapp:${{ github.sha }} .
      - name: Run Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: myapp:${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'
      - name: Upload to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

---

### 7.5.2 Clair集成

```yaml
# docker-compose.yml
version: '3'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: password

  clair:
    image: quay.io/coreos/clair:latest
    depends_on:
      - postgres
    ports:
      - 6060:6060
    volumes:
      - ./clair-config.yaml:/config/config.yaml
    command: [-config, /config/config.yaml]
```

---

## 7.6 本章总结

**关键要点**:
- ✅ Docker Hub适合公共镜像,私有仓库需付费
- ✅ Registry适合小团队,Harbor适合企业
- ✅ 使用镜像加速器提升拉取速度
- ✅ 定期执行垃圾回收释放空间
- ✅ 集成漏洞扫描确保镜像安全

---

# 第8章:容器构建工具生态

## 8.1 Buildah无守护进程构建

### 8.1.1 Buildah基础

```bash
# 安装Buildah
$ sudo yum install buildah  # CentOS/RHEL
$ sudo apt install buildah  # Ubuntu

# 创建工作容器
$ buildah from alpine:3.19
alpine-working-container

# 运行命令
$ buildah run alpine-working-container apk add nginx

# 复制文件
$ buildah copy alpine-working-container index.html /var/www/html/

# 配置容器
$ buildah config --entrypoint '["/usr/sbin/nginx", "-g", "daemon off;"]' \
  alpine-working-container

# 提交为镜像
$ buildah commit alpine-working-container my-nginx:latest

# 推送镜像
$ buildah push my-nginx:latest docker://registry.example.com/my-nginx:latest
```

**Buildah vs Docker Build对比**:

| 特性 | Buildah | Docker Build |
|------|---------|--------------|
| 守护进程 | ❌ 无需 | ✅ 需要dockerd |
| Root权限 | ❌ rootless支持 | ⚠️ 通常需要root |
| 构建方式 | 命令行+Dockerfile | 仅Dockerfile |
| OCI兼容 | ✅ 完全兼容 | ✅ 兼容 |
| 存储后端 | overlay/vfs | overlay2 |

---

### 8.1.2 Buildah脚本化构建

```bash
#!/bin/bash
# build.sh - 使用Buildah构建镜像

set -e

# 创建容器
ctr=$(buildah from golang:1.21-alpine)

# 安装依赖
buildah run $ctr apk add --no-cache git make

# 复制源码
buildah copy $ctr . /src
buildah config --workingdir /src $ctr

# 编译
buildah run $ctr go build -o /app /src

# 创建最终镜像
final=$(buildah from alpine:3.19)
buildah copy --from=$ctr $final /app /usr/local/bin/app
buildah config --entrypoint '["/usr/local/bin/app"]' $final
buildah config --port 8080 $final

# 提交
buildah commit $final myapp:latest

# 清理
buildah rm $ctr $final

echo "✅ Build completed: myapp:latest"
```

---

## 8.2 Kaniko Kubernetes原生构建

### 8.2.1 Kaniko原理

**Kaniko特点**:
- ✅ 无需Docker守护进程
- ✅ 在Kubernetes Pod中构建
- ✅ 支持多阶段构建
- ✅ 可在非特权容器中运行

```yaml
# kaniko-build.yaml
apiVersion: v1
kind: Pod
metadata:
  name: kaniko-build
spec:
  containers:
  - name: kaniko
    image: gcr.io/kaniko-project/executor:latest
    args:
    - "--context=git://github.com/myuser/myrepo.git"
    - "--dockerfile=Dockerfile"
    - "--destination=registry.example.com/myapp:latest"
    - "--cache=true"
    - "--cache-repo=registry.example.com/cache"
    volumeMounts:
    - name: docker-config
      mountPath: /kaniko/.docker
  volumes:
  - name: docker-config
    secret:
      secretName: regcred
      items:
      - key: .dockerconfigjson
        path: config.json
  restartPolicy: Never
```

---

### 8.2.2 Kaniko缓存优化

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: kaniko-cached
spec:
  containers:
  - name: kaniko
    image: gcr.io/kaniko-project/executor:latest
    args:
    - "--context=/workspace"
    - "--dockerfile=/workspace/Dockerfile"
    - "--destination=myregistry.com/myapp:latest"
    - "--cache=true"
    - "--cache-repo=myregistry.com/cache"
    - "--cache-ttl=24h"
    - "--build-arg=VERSION=1.0.0"
    volumeMounts:
    - name: source
      mountPath: /workspace
    - name: docker-config
      mountPath: /kaniko/.docker
  volumes:
  - name: source
    emptyDir: {}
  - name: docker-config
    secret:
      secretName: regcred
```

---

## 8.3 Docker Buildx多平台构建

### 8.3.1 Buildx安装配置

```bash
# 验证Buildx
$ docker buildx version
github.com/docker/buildx v0.12.0

# 创建builder实例
$ docker buildx create --name multiarch --use
$ docker buildx inspect --bootstrap
[+] Building 5.2s (1/1) FINISHED
 => [internal] booting buildkit
Name:   multiarch
Driver: docker-container

Platforms: linux/amd64, linux/arm64, linux/arm/v7

# 列出所有builder
$ docker buildx ls
NAME/NODE    DRIVER/ENDPOINT  STATUS  BUILDKIT  PLATFORMS
multiarch *  docker-container running v0.12.0  linux/amd64, linux/arm64
default      docker           running 23.0.1   linux/amd64
```

---

### 8.3.2 多架构镜像构建

```bash
# 构建多平台镜像
$ docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  -t myregistry.com/myapp:multiarch \
  --push \
  .

# 查看manifest
$ docker buildx imagetools inspect myregistry.com/myapp:multiarch
Name:      myregistry.com/myapp:multiarch
MediaType: application/vnd.docker.distribution.manifest.list.v2+json
Digest:    sha256:abc123...

Manifests:
  Name:      myregistry.com/myapp:multiarch@sha256:def456...
  MediaType: application/vnd.docker.distribution.manifest.v2+json
  Platform:  linux/amd64

  Name:      myregistry.com/myapp:multiarch@sha256:ghi789...
  MediaType: application/vnd.docker.distribution.manifest.v2+json
  Platform:  linux/arm64

  Name:      myregistry.com/myapp:multiarch@sha256:jkl012...
  MediaType: application/vnd.docker.distribution.manifest.v2+json
  Platform:  linux/arm/v7

# ARM设备自动拉取对应架构镜像
$ docker pull myregistry.com/myapp:multiarch
# 自动选择 linux/arm64 或 linux/arm/v7
```

---

### 8.3.3 跨平台构建最佳实践

```dockerfile
# Dockerfile优化多架构构建
FROM --platform=$BUILDPLATFORM golang:1.21-alpine AS builder

ARG TARGETOS
ARG TARGETARCH

WORKDIR /build
COPY . .

RUN CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} \
    go build -o app .

FROM alpine:3.19
COPY --from=builder /build/app /usr/local/bin/app
ENTRYPOINT ["/usr/local/bin/app"]

# 构建命令
$ docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t myapp:multiarch \
  --push \
  .
```

---

## 8.4 BuildKit高级特性

### 8.4.1 BuildKit后端配置

```toml
# /etc/buildkit/buildkitd.toml
debug = false
root = "/var/lib/buildkit"

[worker.oci]
  enabled = true
  platforms = [ "linux/amd64", "linux/arm64" ]
  gc = true
  gckeepstorage = 10000  # MB
  [[worker.oci.gcpolicy]]
    keepBytes = 512000000
    keepDuration = 172800  # 48 hours

[registry."docker.io"]
  mirrors = ["mirror.gcr.io"]
```

---

### 8.4.2 缓存导出导入

```bash
# 导出缓存到Registry
$ docker buildx build \
  --cache-from=type=registry,ref=myregistry.com/myapp:cache \
  --cache-to=type=registry,ref=myregistry.com/myapp:cache,mode=max \
  -t myapp:latest \
  .

# 导出缓存到本地
$ docker buildx build \
  --cache-to=type=local,dest=/tmp/buildcache \
  -t myapp:latest \
  .

# 使用本地缓存
$ docker buildx build \
  --cache-from=type=local,src=/tmp/buildcache \
  -t myapp:latest \
  .

# GitHub Actions缓存示例
- name: Build with cache
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: myapp:latest
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

---

## 8.5 工具选型指南

### 8.5.1 构建工具对比

| 工具 | 适用场景 | 优势 | 劣势 |
|------|---------|------|------|
| **Docker Build** | 本地开发,小团队 | 成熟稳定,生态完善 | 需要守护进程,权限要求高 |
| **Buildah** | CI/CD,rootless构建 | 无守护进程,rootless | 学习曲线陡峭 |
| **Kaniko** | Kubernetes环境 | K8s原生,安全性高 | 仅支持Dockerfile |
| **Buildx** | 多平台构建 | 官方支持,易用性强 | 依赖BuildKit |
| **img** | 安全环境 | 完全无root | 功能有限 |

---

### 8.5.2 推荐配置

**场景1:本地开发**
```bash
# 使用Docker Build + BuildKit
export DOCKER_BUILDKIT=1
docker build -t myapp .
```

**场景2:CI/CD流水线**
```yaml
# 使用Kaniko
apiVersion: tekton.dev/v1beta1
kind: Task
metadata:
  name: build-push
spec:
  steps:
  - name: build-and-push
    image: gcr.io/kaniko-project/executor:latest
    args:
    - --context=$(params.pathToContext)
    - --dockerfile=$(params.pathToDockerFile)
    - --destination=$(params.imageUrl)
```

**场景3:多架构发布**
```bash
# 使用Buildx
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t myapp:multiarch \
  --push \
  .
```

---

## 8.6 本章总结

**核心要点**:
- ✅ Buildah无守护进程,适合CI/CD
- ✅ Kaniko专为Kubernetes设计
- ✅ Buildx官方多平台解决方案
- ✅ BuildKit提供高级缓存和并行特性
- ✅ 根据场景选择合适的构建工具

---

📝 **下一章预告**: 容器生命周期管理、健康检查、自动重启策略、资源监控

---

*（第6-8章完成,约3400行。已完成8章,剩余11章...）*
