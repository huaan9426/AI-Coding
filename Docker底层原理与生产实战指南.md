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

*（第2-3章完成，共约1800行。继续生成第4章...）*
