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

---

# 第三部分:容器运行时与编排

---

# 第9章:容器生命周期管理

## 9.1 容器状态与生命周期

### 9.1.1 容器状态机

```bash
# Docker容器状态转换图
Created → Running → Paused → Running → Stopped → Removed
   ↓         ↓        ↓         ↓         ↓
   └────────→ Stopped ←─────────┘         ↓
                ↓                         ↓
                └────────→ Removed ←──────┘

# 查看容器状态
$ docker ps -a
CONTAINER ID  IMAGE         STATUS
abc123        nginx:alpine  Up 2 hours               # Running
def456        redis:7       Exited (0) 5 minutes ago # Stopped
ghi789        mysql:8       Paused                   # Paused
```

**状态详解**:

| 状态 | 说明 | 进程状态 | 资源占用 |
|------|------|---------|---------|
| **Created** | 已创建未启动 | 不存在 | 磁盘空间 |
| **Running** | 正常运行 | 存在 | CPU+内存+磁盘+网络 |
| **Paused** | 暂停(冻结) | 暂停 | 内存+磁盘 |
| **Restarting** | 重启中 | 短暂不存在 | 过渡状态 |
| **Exited** | 已停止 | 不存在 | 磁盘空间 |
| **Dead** | 异常终止 | 不存在 | 磁盘空间 |

---

### 9.1.2 容器启动流程深度解析

```bash
# 完整启动流程示例
$ docker run -d \
  --name myapp \
  --restart unless-stopped \
  --health-cmd "curl -f http://localhost:8080/health || exit 1" \
  --health-interval 30s \
  --health-timeout 3s \
  --health-retries 3 \
  -p 8080:8080 \
  myapp:latest

# 启动流程(底层调用链):
# 1️⃣ Docker Client → Docker API
# 2️⃣ dockerd → containerd (gRPC)
# 3️⃣ containerd → containerd-shim
# 4️⃣ containerd-shim → runc (创建容器)
# 5️⃣ runc → Linux Kernel (namespace/cgroups)
# 6️⃣ 容器进程启动(PID 1)
# 7️⃣ 健康检查启动(定时探测)
```

**启动过程详细步骤**:

```bash
# 监控启动过程
$ docker events --filter container=myapp &

# 启动容器
$ docker start myapp
2023-12-04T10:00:00.123 container start abc123 (image=myapp:latest)
2023-12-04T10:00:00.456 container attach abc123
2023-12-04T10:00:01.234 network connect bridge abc123
2023-12-04T10:00:01.567 container health_status: starting → healthy

# 验证容器进程树
$ docker top myapp
UID    PID   PPID  CMD
1000   1234  1200  /usr/local/bin/app --config /etc/app/config.yaml
1000   1235  1234   \_ worker-thread-1
1000   1236  1234   \_ worker-thread-2

# 查看容器详细信息
$ docker inspect myapp | jq '.[0].State'
{
  "Status": "running",
  "Running": true,
  "Paused": false,
  "Restarting": false,
  "OOMKilled": false,
  "Dead": false,
  "Pid": 1234,
  "ExitCode": 0,
  "StartedAt": "2023-12-04T10:00:01.234Z",
  "FinishedAt": "0001-01-01T00:00:00Z",
  "Health": {
    "Status": "healthy",
    "FailingStreak": 0,
    "Log": [...]
  }
}
```

---

### 9.1.3 容器停止与清理流程

```bash
# 优雅停止(SIGTERM → SIGKILL)
$ docker stop myapp
# 流程:
# 1️⃣ 发送 SIGTERM 信号给PID 1
# 2️⃣ 等待 10秒 (默认stopTimeout)
# 3️⃣ 如果未退出,发送 SIGKILL 强制终止

# 自定义停止超时
$ docker stop -t 30 myapp  # 等待30秒

# 立即强制终止(SIGKILL)
$ docker kill myapp
$ docker kill -s SIGUSR1 myapp  # 自定义信号

# 删除容器
$ docker rm myapp
Error: You cannot remove a running container. Stop first.

$ docker rm -f myapp  # 强制删除(先stop再remove)

# 删除所有已停止容器
$ docker container prune
WARNING! This will remove all stopped containers.
Total reclaimed space: 2.3GB
```

**应用优雅退出示例**:

```python
# Python应用优雅退出
import signal
import sys

def signal_handler(sig, frame):
    print('Received SIGTERM, shutting down gracefully...')
    # 1. 停止接受新请求
    server.stop_accepting_connections()
    # 2. 等待当前请求完成
    server.wait_for_current_requests(timeout=20)
    # 3. 关闭数据库连接
    db.close()
    # 4. 清理资源
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C

# 启动服务器
server.start()
```

---

## 9.2 重启策略深度配置

### 9.2.1 重启策略类型

```bash
# no: 不自动重启(默认)
$ docker run -d --restart no myapp:latest

# on-failure[:max-retries]: 仅异常退出时重启
$ docker run -d --restart on-failure:3 myapp:latest
# 仅当退出码非0时重启,最多3次

# always: 总是重启
$ docker run -d --restart always myapp:latest
# dockerd重启后也会自动启动容器

# unless-stopped: 除非手动停止,否则总是重启
$ docker run -d --restart unless-stopped myapp:latest
# dockerd重启后自动启动,但手动stop的不启动
```

**重启策略对比**:

| 策略 | 容器异常退出 | 手动stop | dockerd重启 | 适用场景 |
|------|------------|---------|------------|---------|
| **no** | ❌ 不重启 | - | ❌ 不启动 | 临时任务 |
| **on-failure** | ✅ 重启 | - | ❌ 不启动 | 批处理任务 |
| **always** | ✅ 重启 | ✅ 重启 | ✅ 启动 | 核心服务(需谨慎) |
| **unless-stopped** | ✅ 重启 | ❌ 不重启 | ✅ 启动 | 生产服务(推荐) |

---

### 9.2.2 重启策略实战案例

```bash
# 场景1: Web应用(推荐unless-stopped)
$ docker run -d \
  --name web \
  --restart unless-stopped \
  -p 80:80 \
  nginx:alpine

# 场景2: 数据库(推荐unless-stopped + 健康检查)
$ docker run -d \
  --name postgres \
  --restart unless-stopped \
  --health-cmd "pg_isready -U postgres" \
  --health-interval 10s \
  -e POSTGRES_PASSWORD=secret \
  -v /data/postgres:/var/lib/postgresql/data \
  postgres:15

# 场景3: 定时任务(on-failure:3)
$ docker run -d \
  --name backup-job \
  --restart on-failure:3 \
  mybackup:latest

# 场景4: 一次性任务(no)
$ docker run --rm \
  --name migration \
  --restart no \
  myapp:latest migrate
```

**重启行为验证**:

```bash
# 测试1: 异常退出
$ docker run -d --name test1 --restart on-failure:3 alpine sh -c "exit 1"
$ docker ps -a --filter name=test1
# 观察RestartCount字段

$ docker inspect test1 | jq '.[0].RestartCount'
3  # 重启3次后停止

# 测试2: dockerd重启后行为
$ docker run -d --name test2 --restart unless-stopped nginx:alpine
$ docker stop test2
$ sudo systemctl restart docker
$ docker ps --filter name=test2
# test2不会自动启动(因为手动stop过)

$ docker run -d --name test3 --restart always nginx:alpine
$ docker stop test3
$ sudo systemctl restart docker
$ docker ps --filter name=test3
# test3会自动启动(always策略)
```

---

## 9.3 健康检查机制

### 9.3.1 HEALTHCHECK指令详解

```dockerfile
# Dockerfile中定义健康检查
FROM nginx:alpine

# 方式1: 使用CMD
HEALTHCHECK --interval=30s \
            --timeout=3s \
            --start-period=5s \
            --retries=3 \
  CMD curl -f http://localhost/ || exit 1

# 方式2: 使用脚本
COPY healthcheck.sh /usr/local/bin/
HEALTHCHECK --interval=10s --timeout=5s \
  CMD /usr/local/bin/healthcheck.sh

# 禁用继承的健康检查
HEALTHCHECK NONE
```

**healthcheck.sh脚本示例**:

```bash
#!/bin/sh
# healthcheck.sh - 综合健康检查脚本

set -e

# 1️⃣ 检查HTTP端点
if ! curl -f http://localhost:8080/health >/dev/null 2>&1; then
  echo "HTTP health check failed"
  exit 1
fi

# 2️⃣ 检查数据库连接(可选)
if ! psql -U app -c "SELECT 1" >/dev/null 2>&1; then
  echo "Database connection failed"
  exit 1
fi

# 3️⃣ 检查磁盘空间
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
  echo "Disk usage > 90%: ${DISK_USAGE}%"
  exit 1
fi

# 4️⃣ 检查内存使用
MEM_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
if [ "$MEM_USAGE" -gt 95 ]; then
  echo "Memory usage > 95%: ${MEM_USAGE}%"
  exit 1
fi

echo "All health checks passed"
exit 0
```

---

### 9.3.2 运行时健康检查配置

```bash
# 启动时配置健康检查
$ docker run -d \
  --name myapp \
  --health-cmd "curl -f http://localhost:8080/health || exit 1" \
  --health-interval 30s \
  --health-timeout 3s \
  --health-retries 3 \
  --health-start-period 40s \
  myapp:latest

# 查看健康状态
$ docker ps
CONTAINER ID  STATUS
abc123        Up 5 minutes (healthy)

$ docker inspect --format='{{.State.Health.Status}}' myapp
healthy

# 查看健康检查历史
$ docker inspect myapp | jq '.[0].State.Health.Log'
[
  {
    "Start": "2023-12-04T10:00:30.123Z",
    "End": "2023-12-04T10:00:30.456Z",
    "ExitCode": 0,
    "Output": "All health checks passed\n"
  },
  {
    "Start": "2023-12-04T10:01:00.123Z",
    "End": "2023-12-04T10:01:00.456Z",
    "ExitCode": 0,
    "Output": "All health checks passed\n"
  }
]
```

**健康检查参数详解**:

| 参数 | 默认值 | 说明 |
|------|-------|------|
| `--interval` | 30s | 检查间隔 |
| `--timeout` | 30s | 单次检查超时 |
| `--retries` | 3 | 连续失败次数判定为unhealthy |
| `--start-period` | 0s | 启动宽限期(此期间失败不计入retries) |

---

### 9.3.3 健康检查与负载均衡集成

```yaml
# docker-compose.yml - 健康检查集成
version: '3.8'

services:
  web:
    image: nginx:alpine
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 5s
    deploy:
      replicas: 3
      update_config:
        order: start-first  # 新容器healthy后才停旧容器
        failure_action: rollback

  app:
    image: myapp:latest
    healthcheck:
      test: ["CMD", "/app/healthcheck"]
      interval: 30s
      timeout: 5s
      retries: 3
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:15
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    environment:
      POSTGRES_PASSWORD: secret
```

**Nginx负载均衡集成**:

```nginx
# nginx.conf - 基于Docker健康检查的负载均衡
upstream backend {
  least_conn;

  # 后端服务器(通过Docker DNS)
  server app1:8080 max_fails=3 fail_timeout=30s;
  server app2:8080 max_fails=3 fail_timeout=30s;
  server app3:8080 max_fails=3 fail_timeout=30s;

  keepalive 32;
}

server {
  listen 80;

  location / {
    proxy_pass http://backend;
    proxy_next_upstream error timeout http_500 http_502 http_503;
    proxy_connect_timeout 3s;
    proxy_send_timeout 30s;
    proxy_read_timeout 30s;
  }

  # 健康检查端点
  location /health {
    access_log off;
    return 200 "OK\n";
    add_header Content-Type text/plain;
  }
}
```

---

## 9.4 容器日志管理

### 9.4.1 日志驱动详解

```bash
# 查看支持的日志驱动
$ docker info --format '{{.LoggingDriver}}'
json-file

$ docker info | grep "Logging Driver"
Logging Driver: json-file
```

**日志驱动对比**:

| 驱动 | 持久化 | 性能 | 支持docker logs | 适用场景 |
|------|-------|------|----------------|---------|
| **json-file** | ✅ | ⭐⭐⭐ | ✅ | 开发/小规模 |
| **syslog** | ✅ | ⭐⭐⭐⭐ | ❌ | 集中日志系统 |
| **journald** | ✅ | ⭐⭐⭐⭐ | ✅ | systemd环境 |
| **fluentd** | ❌ | ⭐⭐⭐⭐ | ❌ | 大规模集群 |
| **awslogs** | ✅ | ⭐⭐⭐⭐ | ❌ | AWS环境 |
| **none** | ❌ | ⭐⭐⭐⭐⭐ | ❌ | 无需日志 |

---

### 9.4.2 json-file日志配置

```json
// /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",      // 单文件最大100MB
    "max-file": "10",         // 保留10个历史文件
    "compress": "true",       // 压缩历史文件
    "labels": "production",   // 日志标签
    "env": "APP_ENV"          // 包含环境变量
  }
}
```

```bash
# 容器级别配置
$ docker run -d \
  --name myapp \
  --log-driver json-file \
  --log-opt max-size=50m \
  --log-opt max-file=5 \
  --log-opt compress=true \
  myapp:latest

# 查看日志
$ docker logs myapp
$ docker logs -f myapp  # 实时跟踪
$ docker logs --tail 100 myapp  # 最后100行
$ docker logs --since 2023-12-04T10:00:00 myapp  # 指定时间后
$ docker logs --until 2023-12-04T11:00:00 myapp  # 指定时间前

# 查看日志文件位置
$ docker inspect --format='{{.LogPath}}' myapp
/var/lib/docker/containers/abc123.../abc123...-json.log

# 清理日志(需停止容器)
$ docker stop myapp
$ truncate -s 0 $(docker inspect --format='{{.LogPath}}' myapp)
$ docker start myapp
```

---

### 9.4.3 集中式日志方案

**方案1: Fluentd**

```yaml
# docker-compose.yml
version: '3'

services:
  fluentd:
    image: fluent/fluentd:latest
    ports:
      - "24224:24224"
    volumes:
      - ./fluentd.conf:/fluentd/etc/fluent.conf
      - /data/fluentd:/fluentd/log

  app:
    image: myapp:latest
    logging:
      driver: fluentd
      options:
        fluentd-address: localhost:24224
        tag: myapp.{{.Name}}
```

```conf
# fluentd.conf
<source>
  @type forward
  port 24224
</source>

<filter myapp.**>
  @type record_transformer
  <record>
    hostname "#{Socket.gethostname}"
    tag ${tag}
  </record>
</filter>

<match myapp.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name fluentd
  type_name fluentd
</match>
```

**方案2: ELK Stack**

```yaml
# docker-compose.yml - ELK完整方案
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - es-data:/usr/share/elasticsearch/data
    ports:
      - 9200:9200

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    ports:
      - 5000:5000
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - 5601:5601
    depends_on:
      - elasticsearch

  app:
    image: myapp:latest
    logging:
      driver: syslog
      options:
        syslog-address: "tcp://logstash:5000"
        tag: "myapp"

volumes:
  es-data:
```

---

## 9.5 容器资源监控

### 9.5.1 docker stats实时监控

```bash
# 查看所有容器资源使用
$ docker stats
CONTAINER  CPU %  MEM USAGE / LIMIT   MEM %   NET I/O        BLOCK I/O
myapp      2.5%   256MB / 2GB         12.8%   1.2MB / 850KB  10MB / 5MB
nginx      0.1%   50MB / 512MB        9.8%    500KB / 200KB  2MB / 1MB

# 查看特定容器
$ docker stats myapp --no-stream  # 单次快照
$ docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# JSON格式输出
$ docker stats --format "{{json .}}" --no-stream
{"BlockIO":"10MB / 5MB","CPUPerc":"2.5%","Container":"myapp",...}
```

---

### 9.5.2 cAdvisor深度监控

```yaml
# docker-compose.yml - cAdvisor部署
version: '3'

services:
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: cadvisor
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    ports:
      - 8080:8080
    privileged: true
    devices:
      - /dev/kmsg

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - 9090:9090
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana:latest
    ports:
      - 3000:3000
    volumes:
      - grafana-data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  prometheus-data:
  grafana-data:
```

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']

  - job_name: 'docker'
    static_configs:
      - targets: ['host.docker.internal:9323']
```

---

### 9.5.3 监控告警配置

```yaml
# prometheus-rules.yml
groups:
  - name: docker_alerts
    interval: 30s
    rules:
      # CPU使用率告警
      - alert: HighCPUUsage
        expr: container_cpu_usage_seconds_total > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Container {{ $labels.name }} high CPU usage"
          description: "CPU usage is above 80% for 5 minutes"

      # 内存使用率告警
      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "Container {{ $labels.name }} high memory usage"
          description: "Memory usage is above 90%"

      # 容器重启告警
      - alert: ContainerRestarting
        expr: rate(container_restart_count[15m]) > 0
        labels:
          severity: warning
        annotations:
          summary: "Container {{ $labels.name }} is restarting"
          description: "Container restarted {{ $value }} times in 15 minutes"
```

---

## 9.6 本章总结

**核心要点**:
- ✅ 容器状态机:Created → Running → Paused/Stopped → Removed
- ✅ 重启策略:`unless-stopped`适合生产环境
- ✅ 健康检查:定义明确的检查逻辑,设置合理的超时和重试
- ✅ 日志管理:限制大小,集中收集,结构化输出
- ✅ 资源监控:实时监控+历史趋势+告警通知

---

# 第10章:Docker数据持久化方案

## 10.1 存储驱动详解

### 10.1.1 存储驱动对比

```bash
# 查看当前存储驱动
$ docker info | grep "Storage Driver"
Storage Driver: overlay2
```

**存储驱动选型对比**:

| 驱动 | Linux发行版 | 性能 | 稳定性 | 适用场景 |
|------|-----------|------|-------|---------|
| **overlay2** | Kernel 4.0+ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **生产环境首选** |
| **aufs** | Ubuntu/Debian | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 旧版Ubuntu |
| **devicemapper** | RHEL/CentOS | ⭐⭐⭐ | ⭐⭐⭐ | 已弃用 |
| **btrfs** | SLES | ⭐⭐⭐ | ⭐⭐⭐ | 特定场景 |
| **zfs** | Ubuntu 16.04+ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 高级用户 |
| **vfs** | 任意 | ⭐⭐ | ⭐⭐⭐⭐⭐ | 测试环境 |

---

### 10.1.2 overlay2工作原理

```bash
# overlay2目录结构
/var/lib/docker/overlay2/
├── l/  # 短链接目录(避免mount参数过长)
├── abc123.../  # 容器层
│   ├── diff/    # 读写层差异数据
│   ├── link     # 指向l/目录的短链接
│   ├── lower    # 指向下层镜像
│   ├── merged/  # 联合挂载点
│   └── work/    # overlay工作目录
└── def456.../  # 镜像层

# 查看容器的overlay2挂载
$ docker inspect myapp | jq '.[0].GraphDriver'
{
  "Data": {
    "LowerDir": "/var/lib/docker/overlay2/def456/diff",
    "MergedDir": "/var/lib/docker/overlay2/abc123/merged",
    "UpperDir": "/var/lib/docker/overlay2/abc123/diff",
    "WorkDir": "/var/lib/docker/overlay2/abc123/work"
  },
  "Name": "overlay2"
}

# 验证overlay挂载
$ mount | grep overlay
overlay on /var/lib/docker/overlay2/abc123/merged type overlay (rw,...)
```

**COW(Copy-on-Write)机制**:

```bash
# 场景演示:修改镜像中的文件
$ docker run -it --name test alpine sh
/ # echo "new content" > /etc/hosts  # 修改文件

# 宿主机查看
$ ls /var/lib/docker/overlay2/abc123/diff/etc/
hosts  # ✅ 文件被复制到容器层

# 删除文件
/ # rm /etc/passwd

$ ls /var/lib/docker/overlay2/abc123/diff/etc/
passwd  # ❌ 创建whiteout标记(字符设备 c 0 0)
```

---

## 10.2 Volume卷管理

### 10.2.1 Volume基础操作

```bash
# 创建卷
$ docker volume create mydata
mydata

# 查看卷列表
$ docker volume ls
DRIVER    VOLUME NAME
local     mydata
local     postgres-data

# 查看卷详细信息
$ docker volume inspect mydata
[
  {
    "CreatedAt": "2023-12-04T10:00:00Z",
    "Driver": "local",
    "Labels": {},
    "Mountpoint": "/var/lib/docker/volumes/mydata/_data",
    "Name": "mydata",
    "Options": {},
    "Scope": "local"
  }
]

# 使用卷
$ docker run -d \
  --name postgres \
  -v mydata:/var/lib/postgresql/data \
  postgres:15

# 删除卷
$ docker volume rm mydata
Error: volume is in use

$ docker stop postgres && docker rm postgres
$ docker volume rm mydata  # ✅ 成功删除

# 删除所有未使用卷
$ docker volume prune
WARNING! This will remove all local volumes not used by at least one container.
Total reclaimed space: 5.2GB
```

---

### 10.2.2 Volume挂载类型详解

```bash
# 1️⃣ Named Volume(命名卷)
$ docker run -v mydata:/data alpine
# 特点:Docker管理,持久化,可共享

# 2️⃣ Anonymous Volume(匿名卷)
$ docker run -v /data alpine
# 特点:Docker管理,容器删除时可选择删除

# 3️⃣ Bind Mount(绑定挂载)
$ docker run -v /host/path:/container/path alpine
# 特点:直接映射宿主机目录,开发环境常用

# 4️⃣ tmpfs Mount(内存挂载)
$ docker run --tmpfs /tmp:rw,size=100m alpine
# 特点:存储在内存,容器停止即清空
```

**挂载类型对比**:

| 类型 | 管理方 | 持久化 | 性能 | 跨主机 | 适用场景 |
|------|-------|-------|------|-------|---------|
| **Named Volume** | Docker | ✅ | ⭐⭐⭐⭐ | 使用插件 | **生产数据** |
| **Anonymous Volume** | Docker | ✅ | ⭐⭐⭐⭐ | ❌ | 临时数据 |
| **Bind Mount** | 用户 | ✅ | ⭐⭐⭐⭐⭐ | ❌ | 开发环境 |
| **tmpfs** | Docker | ❌ | ⭐⭐⭐⭐⭐ | ❌ | 敏感数据/缓存 |

---

### 10.2.3 Volume高级选项

```bash
# 只读挂载
$ docker run -v mydata:/data:ro alpine

# 指定卷驱动
$ docker volume create --driver local \
  --opt type=nfs \
  --opt o=addr=192.168.1.100,rw \
  --opt device=:/path/to/share \
  nfs-volume

# 使用NFS卷
$ docker run -v nfs-volume:/data alpine

# 设置卷标签
$ docker volume create --label env=production \
  --label app=database \
  prod-db-data

# 查询特定标签的卷
$ docker volume ls --filter label=env=production

# nocopy选项(不从镜像复制初始内容)
$ docker run -v mydata:/app:nocopy myapp:latest
```

**Bind Mount高级选项**:

```bash
# 指定权限
$ docker run \
  -v /host/data:/container/data:rw \  # 读写
  -v /host/config:/etc/app:ro \       # 只读
  alpine

# 传播模式(propagation)
$ docker run \
  -v /host/data:/data:rshared \  # 双向传播
  alpine

# propagation模式:
# - shared: 双向传播
# - slave: 单向传播(宿主机→容器)
# - private: 不传播(默认)
# - rshared/rslave/rprivate: 递归模式

# SELinux标签(CentOS/RHEL)
$ docker run -v /host/data:/data:z alpine  # 私有标签
$ docker run -v /host/data:/data:Z alpine  # 共享标签
```

---

## 10.3 生产环境数据持久化方案

### 10.3.1 数据库持久化最佳实践

**PostgreSQL**:

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    volumes:
      # 数据目录
      - postgres-data:/var/lib/postgresql/data
      # 初始化脚本
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
      # 配置文件
      - ./postgresql.conf:/etc/postgresql/postgresql.conf:ro
    command: postgres -c config_file=/etc/postgresql/postgresql.conf
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appuser -d myapp"]
      interval: 10s
      timeout: 5s
      retries: 5
    ports:
      - "5432:5432"

secrets:
  db_password:
    file: ./secrets/db_password.txt

volumes:
  postgres-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/postgres  # 指定宿主机路径
```

**MySQL**:

```yaml
services:
  mysql:
    image: mysql:8.0
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD_FILE: /run/secrets/mysql_root_password
      MYSQL_DATABASE: myapp
      MYSQL_USER: appuser
      MYSQL_PASSWORD_FILE: /run/secrets/mysql_password
    secrets:
      - mysql_root_password
      - mysql_password
    volumes:
      - mysql-data:/var/lib/mysql
      - ./my.cnf:/etc/mysql/conf.d/my.cnf:ro
    command: --default-authentication-plugin=mysql_native_password
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p$$MYSQL_ROOT_PASSWORD"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  mysql-data:
```

---

### 10.3.2 备份与恢复策略

**PostgreSQL备份**:

```bash
# 方式1: 逻辑备份(pg_dump)
$ docker exec postgres pg_dump -U appuser myapp > backup.sql

# 恢复
$ docker exec -i postgres psql -U appuser myapp < backup.sql

# 方式2: 文件系统备份(需停止数据库)
$ docker stop postgres
$ tar -czf postgres-backup-$(date +%Y%m%d).tar.gz /data/postgres
$ docker start postgres

# 方式3: 在线备份(pg_basebackup)
$ docker exec postgres pg_basebackup -U postgres -D /backup -Ft -z -P

# 自动化备份脚本
$ cat > /usr/local/bin/backup-postgres.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/backup/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/postgres_$TIMESTAMP.sql.gz"

mkdir -p "$BACKUP_DIR"

docker exec postgres pg_dump -U appuser myapp | gzip > "$BACKUP_FILE"

# 保留最近7天的备份
find "$BACKUP_DIR" -name "postgres_*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE"
EOF

$ chmod +x /usr/local/bin/backup-postgres.sh

# 添加定时任务(每天凌晨2点)
$ crontab -e
0 2 * * * /usr/local/bin/backup-postgres.sh >> /var/log/postgres-backup.log 2>&1
```

**MongoDB备份**:

```bash
# 备份
$ docker exec mongodb mongodump --out /backup/$(date +%Y%m%d)

# 恢复
$ docker exec mongodb mongorestore /backup/20231204
```

---

### 10.3.3 跨主机数据共享方案

**方案1: NFS挂载**:

```bash
# NFS服务器配置(192.168.1.100)
$ sudo apt install nfs-kernel-server
$ sudo mkdir -p /export/docker-data
$ sudo chown nobody:nogroup /export/docker-data

$ sudo vim /etc/exports
/export/docker-data 192.168.1.0/24(rw,sync,no_subtree_check,no_root_squash)

$ sudo exportfs -ra
$ sudo systemctl restart nfs-kernel-server

# Docker客户端使用NFS卷
$ docker volume create --driver local \
  --opt type=nfs \
  --opt o=addr=192.168.1.100,rw \
  --opt device=:/export/docker-data \
  nfs-data

$ docker run -v nfs-data:/data alpine
```

**方案2: REX-Ray(云存储)**:

```bash
# 安装REX-Ray
$ curl -sSL https://rexray.io/install | sh

# 配置AWS EBS
$ cat > /etc/rexray/config.yml <<EOF
libstorage:
  service: ebs
aws:
  accessKey: AKIAXXXXXXXXXXXXXXXX
  secretKey: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  region: us-east-1
EOF

$ sudo systemctl start rexray

# 创建EBS卷
$ docker volume create --driver rexray --name ebs-vol \
  --opt size=100

# 使用卷(可在多台EC2间迁移)
$ docker run -v ebs-vol:/data alpine
```

**方案3: GlusterFS集群**:

```bash
# 3节点GlusterFS集群部署(简化)
# 节点1,2,3: 192.168.1.101-103

# 每个节点安装GlusterFS
$ sudo apt install glusterfs-server

# 节点1创建卷
$ sudo gluster volume create docker-vol replica 3 \
  192.168.1.101:/data/gluster \
  192.168.1.102:/data/gluster \
  192.168.1.103:/data/gluster

$ sudo gluster volume start docker-vol

# Docker使用GlusterFS卷
$ docker volume create --driver local \
  --opt type=glusterfs \
  --opt o=addr=192.168.1.101 \
  --opt device=:/docker-vol \
  gluster-data
```

---

## 10.4 本章总结

**核心要点**:
- ✅ 存储驱动:**overlay2**是生产环境首选
- ✅ 数据持久化:**Named Volume**管理简单,适合生产
- ✅ 开发环境:**Bind Mount**方便实时同步
- ✅ 数据库:定期备份,使用健康检查,配置持久化卷
- ✅ 跨主机共享:NFS/GlusterFS/云存储方案

---

# 第11章:Docker Compose实战

## 11.1 Compose基础

### 11.1.1 Compose文件格式

```yaml
# docker-compose.yml - 完整示例
version: '3.8'  # Compose文件版本

# 定义服务
services:
  web:
    image: nginx:alpine
    container_name: web-server
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./html:/usr/share/nginx/html:ro
    networks:
      - frontend
    depends_on:
      - app
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/"]
      interval: 30s
      timeout: 3s
      retries: 3

  app:
    build:
      context: ./app
      dockerfile: Dockerfile
      args:
        - VERSION=1.0.0
    image: myapp:latest
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgres://appuser:${DB_PASSWORD}@db:5432/myapp
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env
    networks:
      - frontend
      - backend
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started

  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    volumes:
      - db-data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appuser"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    networks:
      - backend

# 定义网络
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # 内部网络,不能访问外网

# 定义卷
volumes:
  db-data:
    driver: local
  redis-data:
    driver: local

# 定义secrets
secrets:
  db_password:
    file: ./secrets/db_password.txt
```

---

### 11.1.2 Compose命令详解

```bash
# 启动服务(后台运行)
$ docker-compose up -d
Creating network "myapp_frontend" ... done
Creating network "myapp_backend" ... done
Creating volume "myapp_db-data" ... done
Creating myapp_redis_1 ... done
Creating myapp_db_1    ... done
Creating myapp_app_1   ... done
Creating myapp_web_1   ... done

# 查看服务状态
$ docker-compose ps
      Name                    Command               State          Ports
--------------------------------------------------------------------------------
myapp_app_1       /app/start.sh                   Up      8080/tcp
myapp_db_1        docker-entrypoint.sh postgres   Up      5432/tcp
myapp_redis_1     redis-server --appendonly yes   Up      6379/tcp
myapp_web_1       nginx -g daemon off;            Up      0.0.0.0:80->80/tcp

# 查看日志
$ docker-compose logs          # 所有服务
$ docker-compose logs -f app   # 跟踪app服务日志
$ docker-compose logs --tail=100 web  # 最后100行

# 执行命令
$ docker-compose exec app sh           # 进入app容器
$ docker-compose exec db psql -U appuser myapp  # 连接数据库

# 扩容服务
$ docker-compose up -d --scale app=3
Creating myapp_app_2 ... done
Creating myapp_app_3 ... done

# 停止服务
$ docker-compose stop     # 停止所有服务
$ docker-compose stop app # 停止app服务

# 停止并删除容器
$ docker-compose down
Stopping myapp_web_1   ... done
Stopping myapp_app_1   ... done
Stopping myapp_db_1    ... done
Stopping myapp_redis_1 ... done
Removing myapp_web_1   ... done
Removing myapp_app_1   ... done
Removing myapp_db_1    ... done
Removing myapp_redis_1 ... done
Removing network myapp_frontend
Removing network myapp_backend

# 删除容器和卷
$ docker-compose down -v  # ⚠️ 会删除数据

# 重建服务
$ docker-compose up -d --build  # 重新构建镜像
$ docker-compose up -d --force-recreate  # 强制重建容器
```

---

## 11.2 服务依赖管理

### 11.2.1 depends_on详解

```yaml
version: '3.8'

services:
  # 基础服务:数据库
  db:
    image: postgres:15
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 5s

  # 基础服务:缓存
  redis:
    image: redis:7-alpine

  # 应用服务:依赖db和redis
  app:
    image: myapp:latest
    depends_on:
      db:
        condition: service_healthy  # 等待db健康
      redis:
        condition: service_started   # 等待redis启动
    # 启动顺序: db → redis → app

  # Web服务:依赖app
  web:
    image: nginx:alpine
    depends_on:
      - app
    ports:
      - "80:80"
    # 启动顺序: db → redis → app → web
```

**depends_on条件类型**:

| 条件 | 说明 | 使用场景 |
|------|------|---------|
| `service_started` | 容器启动即可(默认) | 无需等待服务就绪 |
| `service_healthy` | 健康检查通过 | **数据库等关键服务(推荐)** |
| `service_completed_successfully` | 容器成功退出 | 初始化任务 |

---

### 11.2.2 启动顺序控制脚本

```bash
#!/bin/sh
# wait-for-it.sh - 等待服务可用

set -e

host="$1"
shift
cmd="$@"

until nc -z "$host" 2>/dev/null; do
  >&2 echo "Waiting for $host..."
  sleep 1
done

>&2 echo "$host is available - executing command"
exec $cmd
```

**在Compose中使用**:

```yaml
services:
  app:
    image: myapp:latest
    command: sh -c "/wait-for-it.sh db:5432 -- /app/start.sh"
    volumes:
      - ./wait-for-it.sh:/wait-for-it.sh:ro
    depends_on:
      - db
```

---

## 11.3 网络配置进阶

### 11.3.1 自定义网络

```yaml
version: '3.8'

services:
  web:
    image: nginx:alpine
    networks:
      - public
      - internal

  app:
    image: myapp:latest
    networks:
      internal:
        ipv4_address: 172.20.0.10  # 固定IP
        aliases:
          - api.local

  db:
    image: postgres:15
    networks:
      - internal

networks:
  # 公共网络(可访问外网)
  public:
    driver: bridge
    ipam:
      config:
        - subnet: 172.19.0.0/16

  # 内部网络(隔离外网)
  internal:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1
```

---

### 11.3.2 网络别名与服务发现

```yaml
services:
  app:
    image: myapp:latest
    networks:
      backend:
        aliases:
          - api
          - api-server
          - backend-api

  # 其他服务可通过别名访问
  worker:
    image: myworker:latest
    environment:
      - API_URL=http://api:8080  # 使用别名
    networks:
      - backend
```

**DNS解析测试**:

```bash
$ docker-compose exec worker nslookup api
Server:    127.0.0.11
Address:   127.0.0.11:53

Non-authoritative answer:
Name:   api
Address: 172.20.0.10

# 所有别名指向同一IP
$ docker-compose exec worker ping -c1 api-server
64 bytes from 172.20.0.10: icmp_seq=1 ttl=64
```

---

## 11.4 数据卷共享

### 11.4.1 卷的定义与使用

```yaml
version: '3.8'

services:
  web:
    image: nginx:alpine
    volumes:
      # 命名卷
      - static-data:/usr/share/nginx/html
      # 绑定挂载
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      # 临时文件系统
      - type: tmpfs
        target: /tmp
        tmpfs:
          size: 100M

  app:
    image: myapp:latest
    volumes:
      # 共享卷(与web共享)
      - static-data:/app/static
      # 应用数据卷
      - app-data:/app/data

volumes:
  static-data:
    driver: local
  app-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/app  # 映射到宿主机路径
```

---

### 11.4.2 卷的高级配置

```yaml
volumes:
  # NFS卷
  nfs-data:
    driver: local
    driver_opts:
      type: nfs
      o: addr=192.168.1.100,rw
      device: ":/export/data"

  # 外部卷(已存在)
  existing-vol:
    external: true

  # 卷标签
  labeled-vol:
    driver: local
    labels:
      env: production
      app: myapp
```

---

## 11.5 环境变量与配置

### 11.5.1 环境变量最佳实践

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    image: myapp:latest
    environment:
      # 方式1:直接定义
      - NODE_ENV=production
      # 方式2:引用宿主机环境变量
      - DATABASE_URL=${DATABASE_URL}
      # 方式3:默认值
      - REDIS_URL=${REDIS_URL:-redis://redis:6379}
    env_file:
      - .env            # 默认环境文件
      - .env.production # 生产环境配置
```

**.env文件**:

```bash
# .env
DATABASE_URL=postgres://user:pass@db:5432/myapp
REDIS_URL=redis://redis:6379/0
API_KEY=secret-key-here
LOG_LEVEL=info
```

**环境变量优先级**:

```bash
# 优先级从高到低:
1. docker-compose.yml中的environment
2. --env-file指定的文件
3. .env文件
4. Dockerfile中的ENV
5. 宿主机环境变量
```

---

### 11.5.2 多环境配置

```bash
# 项目结构
.
├── docker-compose.yml         # 基础配置
├── docker-compose.dev.yml     # 开发环境
├── docker-compose.prod.yml    # 生产环境
├── .env.dev
└── .env.prod

# docker-compose.yml (基础配置)
version: '3.8'
services:
  app:
    image: myapp:latest
    env_file:
      - .env

# docker-compose.dev.yml (开发覆盖)
version: '3.8'
services:
  app:
    build:
      context: .
      target: dev
    volumes:
      - .:/app  # 源码挂载
    environment:
      - DEBUG=true

# docker-compose.prod.yml (生产覆盖)
version: '3.8'
services:
  app:
    restart: unless-stopped
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 1G

# 使用方式
$ docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d   # 开发
$ docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d  # 生产
```

---

## 11.6 生产环境Compose配置

### 11.6.1 完整生产环境示例

```yaml
# docker-compose.prod.yml
version: '3.8'

x-logging: &default-logging
  driver: "json-file"
  options:
    max-size: "50m"
    max-file: "3"
    compress: "true"

services:
  nginx:
    image: nginx:1.25-alpine
    container_name: nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - static-files:/var/www/static:ro
    networks:
      - frontend
    logging: *default-logging
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M

  app:
    image: myapp:${VERSION:-latest}
    restart: unless-stopped
    environment:
      - DATABASE_URL_FILE=/run/secrets/db_url
      - REDIS_URL=redis://redis:6379/0
    secrets:
      - db_url
    volumes:
      - static-files:/app/static
      - uploads:/app/uploads
    networks:
      - frontend
      - backend
    depends_on:
      db:
        condition: service_healthy
    logging: *default-logging
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3

  db:
    image: postgres:15-alpine
    container_name: postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    volumes:
      - db-data:/var/lib/postgresql/data
      - ./postgresql.conf:/etc/postgresql/postgresql.conf:ro
    command: postgres -c config_file=/etc/postgresql/postgresql.conf
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appuser -d myapp"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    logging: *default-logging
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

  redis:
    image: redis:7-alpine
    container_name: redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    networks:
      - backend
    logging: *default-logging

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true

volumes:
  db-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/postgres
  redis-data:
    driver: local
  static-files:
  uploads:

secrets:
  db_password:
    file: ./secrets/db_password.txt
  db_url:
    file: ./secrets/db_url.txt
```

---

## 11.7 本章总结

**核心要点**:
- ✅ Compose文件结构:services/networks/volumes/secrets
- ✅ 服务依赖:`depends_on`配合`healthcheck`
- ✅ 网络隔离:前端/后端网络分离,内部网络禁止外网
- ✅ 数据持久化:命名卷管理,支持NFS等外部存储
- ✅ 环境配置:多环境配置文件,敏感信息使用secrets

---

# 第12章:容器编排基础与Swarm

## 12.1 Docker Swarm架构

### 12.1.1 Swarm核心概念

```bash
# 初始化Swarm集群(管理节点)
$ docker swarm init --advertise-addr 192.168.1.10
Swarm initialized: current node (abc123) is now a manager.

To add a worker to this swarm, run the following command:
    docker swarm join --token SWMTKN-1-xxx 192.168.1.10:2377

To add a manager to this swarm, run 'docker swarm join-token manager'

# 查看集群状态
$ docker node ls
ID                  HOSTNAME  STATUS  AVAILABILITY  MANAGER STATUS
abc123 *            node1     Ready   Active        Leader
```

**Swarm架构组件**:

| 组件 | 作用 | 说明 |
|------|------|------|
| **Manager Node** | 集群管理 | 接收任务,调度容器,维护集群状态 |
| **Worker Node** | 任务执行 | 运行容器,接收管理节点调度 |
| **Service** | 服务定义 | 声明容器副本数,更新策略等 |
| **Task** | 任务单元 | Service的最小调度单元(容器实例) |

---

### 12.1.2 节点管理

```bash
# 添加Worker节点(在worker机器上执行)
$ docker swarm join --token SWMTKN-1-xxx 192.168.1.10:2377
This node joined a swarm as a worker.

# 添加Manager节点
$ docker swarm join-token manager
To add a manager:
    docker swarm join --token SWMTKN-1-yyy 192.168.1.10:2377

# 查看节点详情
$ docker node inspect node1

# 节点角色变更
$ docker node promote worker1   # Worker提升为Manager
$ docker node demote manager2   # Manager降级为Worker

# 节点可用性设置
$ docker node update --availability drain worker1  # 排空节点(不调度新任务)
$ docker node update --availability active worker1 # 激活节点

# 删除节点
$ docker node rm worker1  # 需先在worker1上执行: docker swarm leave
```

---

## 12.2 服务部署与管理

### 12.2.1 服务创建

```bash
# 创建服务
$ docker service create \
  --name web \
  --replicas 3 \
  --publish 80:80 \
  --env NODE_ENV=production \
  --limit-memory 512M \
  --limit-cpu 0.5 \
  nginx:alpine

# 查看服务列表
$ docker service ls
ID         NAME  MODE        REPLICAS  IMAGE
abc123     web   replicated  3/3       nginx:alpine

# 查看服务详情
$ docker service inspect web

# 查看服务任务(容器)
$ docker service ps web
ID      NAME    IMAGE          NODE    DESIRED STATE  CURRENT STATE
xyz1    web.1   nginx:alpine   node1   Running        Running 2 minutes
xyz2    web.2   nginx:alpine   node2   Running        Running 2 minutes
xyz3    web.3   nginx:alpine   node3   Running        Running 2 minutes
```

---

### 12.2.2 服务扩缩容

```bash
# 扩容到5个副本
$ docker service scale web=5
web scaled to 5
overall progress: 5 out of 5 tasks
verify: Service converged

# 缩容到2个副本
$ docker service scale web=2

# 查看扩容结果
$ docker service ps web | grep Running
```

---

### 12.2.3 服务更新

```bash
# 滚动更新镜像
$ docker service update \
  --image nginx:1.25 \
  --update-parallelism 1 \  # 每次更新1个任务
  --update-delay 10s \       # 间隔10秒
  --update-failure-action rollback \
  web

# 更新环境变量
$ docker service update --env-add DEBUG=true web

# 更新资源限制
$ docker service update \
  --limit-memory 1G \
  --limit-cpu 1 \
  web

# 回滚到上一版本
$ docker service rollback web
```

---

## 12.3 Stack部署

### 12.3.1 Stack配置文件

```yaml
# stack.yml - Swarm Stack配置
version: '3.8'

services:
  web:
    image: nginx:alpine
    ports:
      - "80:80"
    networks:
      - frontend
    deploy:
      mode: replicated
      replicas: 3
      placement:
        constraints:
          - node.role == worker
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.25'
          memory: 128M

  app:
    image: myapp:latest
    networks:
      - frontend
      - backend
    secrets:
      - db_password
    deploy:
      mode: replicated
      replicas: 5
      placement:
        preferences:
          - spread: node.labels.zone
      update_config:
        parallelism: 2
        order: start-first

  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    networks:
      - backend
    volumes:
      - db-data:/var/lib/postgresql/data
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - node.hostname == node1  # 固定节点

networks:
  frontend:
  backend:

volumes:
  db-data:

secrets:
  db_password:
    external: true
```

---

### 12.3.2 Stack部署命令

```bash
# 创建secret
$ echo "mysecretpassword" | docker secret create db_password -

# 部署Stack
$ docker stack deploy -c stack.yml myapp
Creating network myapp_frontend
Creating network myapp_backend
Creating service myapp_web
Creating service myapp_app
Creating service myapp_db

# 查看Stack
$ docker stack ls
NAME   SERVICES
myapp  3

# 查看Stack服务
$ docker stack services myapp
ID         NAME        MODE      REPLICAS  IMAGE
abc123     myapp_web   replicated  3/3     nginx:alpine
def456     myapp_app   replicated  5/5     myapp:latest
ghi789     myapp_db    replicated  1/1     postgres:15

# 查看Stack任务
$ docker stack ps myapp

# 更新Stack(修改stack.yml后)
$ docker stack deploy -c stack.yml myapp

# 删除Stack
$ docker stack rm myapp
```

---

## 12.4 负载均衡与路由

### 12.4.1 Ingress网络

```bash
# Swarm自动负载均衡
$ docker service create --name web --replicas 3 -p 80:80 nginx:alpine

# 访问任意节点的80端口,自动路由到可用容器
$ curl http://node1  # 可能路由到node2的容器
$ curl http://node2  # 可能路由到node3的容器
$ curl http://node3  # 可能路由到node1的容器

# 路由模式:
# - ingress(默认): VIP负载均衡,任意节点接入
# - host: 直接映射到容器所在节点

# 查看ingress网络
$ docker network inspect ingress
```

---

### 12.4.2 Overlay网络

```bash
# 创建overlay网络
$ docker network create \
  --driver overlay \
  --attachable \
  --subnet 10.10.0.0/16 \
  my-overlay

# 服务使用overlay网络
$ docker service create \
  --name app \
  --network my-overlay \
  myapp:latest

# 跨主机容器通信
# node1上的容器可以直接ping node2上的容器名
```

---

## 12.5 生产环境Swarm配置

### 12.5.1 高可用Swarm集群

```bash
# 推荐配置: 3个Manager + N个Worker
# Manager奇数个,保证Raft一致性算法正常工作

# 节点规划:
# - Manager1 (Leader): 192.168.1.10
# - Manager2: 192.168.1.11
# - Manager3: 192.168.1.12
# - Worker1-N: 192.168.1.20-30

# Manager1初始化
$ docker swarm init --advertise-addr 192.168.1.10

# Manager2,3加入
$ docker swarm join --token SWMTKN-1-manager-xxx 192.168.1.10:2377

# Worker加入
$ docker swarm join --token SWMTKN-1-worker-yyy 192.168.1.10:2377

# 验证集群
$ docker node ls
ID   HOSTNAME  STATUS  AVAILABILITY  MANAGER STATUS
*m1  manager1  Ready   Active        Leader
 m2  manager2  Ready   Active        Reachable
 m3  manager3  Ready   Active        Reachable
 w1  worker1   Ready   Active
 w2  worker2   Ready   Active
```

---

### 12.5.2 节点标签与约束

```bash
# 添加节点标签
$ docker node update --label-add zone=us-east-1a worker1
$ docker node update --label-add zone=us-east-1b worker2
$ docker node update --label-add ssd=true worker1

# 使用标签约束部署
$ docker service create \
  --name db \
  --constraint 'node.labels.ssd == true' \
  postgres:15

# 多重约束
$ docker service create \
  --name app \
  --constraint 'node.role == worker' \
  --constraint 'node.labels.zone == us-east-1a' \
  myapp:latest
```

---

## 12.6 本章总结

**核心要点**:
- ✅ Swarm集群:推荐3个Manager(奇数)+多个Worker
- ✅ 服务部署:使用Stack进行声明式部署
- ✅ 负载均衡:Ingress网络自动路由,无需外部LB
- ✅ 滚动更新:支持蓝绿部署,自动回滚
- ✅ 高可用:Manager节点Raft一致性,服务副本分布

---

---

---

# 第四部分:生产环境部署与运维

---

# 第13章:生产环境部署架构

## 13.1 部署架构模式

### 13.1.1 单机部署架构

**适用场景**: 开发环境、小型应用、PoC验证

```yaml
# docker-compose.yml (单机All-in-One)
version: '3.8'

services:
  # Web应用
  app:
    image: myapp:latest
    restart: unless-stopped
    ports:
      - "8080:8080"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    environment:
      DATABASE_URL: postgresql://appuser:${DB_PASSWORD}@db:5432/appdb
      REDIS_URL: redis://redis:6379/0
    volumes:
      - app-logs:/var/log/app
    networks:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 10s
      timeout: 3s
      retries: 3

  # 反向代理
  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - nginx-logs:/var/log/nginx
    depends_on:
      - app
    networks:
      - backend

  # 数据库
  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
      POSTGRES_DB: appdb
    secrets:
      - db_password
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appuser"]
      interval: 10s

  # 缓存
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: >
      --requirepass ${REDIS_PASSWORD}
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    networks:
      - backend

networks:
  backend:
    driver: bridge

volumes:
  postgres-data:
  redis-data:
  app-logs:
  nginx-logs:

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

**Nginx配置示例**:

```nginx
# nginx/nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 50M;

    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    # 后端应用
    upstream backend {
        server app:8080 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    # HTTP重定向到HTTPS
    server {
        listen 80;
        server_name example.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS主配置
    server {
        listen 443 ssl http2;
        server_name example.com;

        # SSL证书
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # 安全头
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # 反向代理
        location / {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
            proxy_buffering off;
        }

        # 静态资源缓存
        location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2)$ {
            proxy_pass http://backend;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # 健康检查端点
        location /health {
            access_log off;
            proxy_pass http://backend/health;
        }
    }
}
```

---

### 13.1.2 Docker Swarm集群架构

**适用场景**: 中小型生产环境(10-100台节点)

```bash
# 集群拓扑
┌─────────────────────────────────────────────────────────┐
│                     负载均衡层                           │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │  HAProxy 1 │  │  HAProxy 2 │  │  HAProxy 3 │        │
│  │ (keepalived)│ │ (keepalived)│ │ (keepalived)│        │
│  └────────────┘  └────────────┘  └────────────┘        │
└─────────────────────────────────────────────────────────┘
                         │
┌─────────────────────────────────────────────────────────┐
│                  Swarm Manager节点                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │ Manager 1  │  │ Manager 2  │  │ Manager 3  │        │
│  │  (Leader)  │  │ (Reachable)│  │ (Reachable)│        │
│  └────────────┘  └────────────┘  └────────────┘        │
└─────────────────────────────────────────────────────────┘
                         │
┌─────────────────────────────────────────────────────────┐
│                  Swarm Worker节点                        │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐         │
│  │Worker│ │Worker│ │Worker│ │Worker│ │Worker│  ...    │
│  │  1   │ │  2   │ │  3   │ │  4   │ │  5   │         │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘         │
└─────────────────────────────────────────────────────────┘
```

**Swarm集群初始化**:

```bash
# ========================================
# 1. 准备节点(所有节点执行)
# ========================================

# 关闭防火墙或开放必要端口
$ firewall-cmd --permanent --add-port=2377/tcp  # Swarm管理端口
$ firewall-cmd --permanent --add-port=7946/tcp  # 节点间通信
$ firewall-cmd --permanent --add-port=7946/udp
$ firewall-cmd --permanent --add-port=4789/udp  # Overlay网络
$ firewall-cmd --reload

# 配置时间同步(关键!)
$ timedatectl set-ntp true
$ systemctl enable chronyd && systemctl start chronyd

# ========================================
# 2. 初始化Swarm集群(Manager1执行)
# ========================================

# 初始化第一个Manager
$ docker swarm init \
  --advertise-addr 192.168.1.10 \
  --data-path-addr 192.168.1.10

# 输出:
Swarm initialized: current node (abc123) is now a manager.

To add a worker to this swarm, run the following command:
    docker swarm join --token SWMTKN-1-xxx-worker 192.168.1.10:2377

To add a manager to this swarm, run 'docker swarm join-token manager' and follow the instructions.

# 获取Manager加入令牌
$ docker swarm join-token manager
docker swarm join --token SWMTKN-1-xxx-manager 192.168.1.10:2377

# 获取Worker加入令牌
$ docker swarm join-token worker
docker swarm join --token SWMTKN-1-xxx-worker 192.168.1.10:2377

# ========================================
# 3. 添加Manager节点(Manager2/3执行)
# ========================================

# Manager2 (192.168.1.11)
$ docker swarm join \
  --token SWMTKN-1-xxx-manager \
  --advertise-addr 192.168.1.11 \
  192.168.1.10:2377

# Manager3 (192.168.1.12)
$ docker swarm join \
  --token SWMTKN-1-xxx-manager \
  --advertise-addr 192.168.1.12 \
  192.168.1.10:2377

# ========================================
# 4. 添加Worker节点(Worker1-N执行)
# ========================================

# Worker1 (192.168.1.21)
$ docker swarm join \
  --token SWMTKN-1-xxx-worker \
  --advertise-addr 192.168.1.21 \
  192.168.1.10:2377

# Worker2-N 类似操作...

# ========================================
# 5. 验证集群状态(任意Manager执行)
# ========================================

$ docker node ls
ID                HOSTNAME    STATUS  AVAILABILITY  MANAGER STATUS
abc123 *          manager1    Ready   Active        Leader
def456            manager2    Ready   Active        Reachable
ghi789            manager3    Ready   Active        Reachable
jkl012            worker1     Ready   Active
mno345            worker2     Ready   Active
pqr678            worker3     Ready   Active

# 查看集群详细信息
$ docker info | grep -A 10 Swarm
Swarm: active
 NodeID: abc123
 Is Manager: true
 ClusterID: xyz789
 Managers: 3
 Nodes: 6
 Default Address Pool: 10.0.0.0/8
 SubnetSize: 24
 Orchestration:
  Task History Retention Limit: 5
```

**生产级Stack部署**:

```yaml
# stack.yml - 完整生产环境配置
version: '3.8'

# 全局配置锚点
x-default-logging: &default-logging
  driver: "json-file"
  options:
    max-size: "50m"
    max-file: "3"
    compress: "true"
    labels: "service,stack"

x-deploy-defaults: &deploy-defaults
  update_config:
    parallelism: 1
    delay: 10s
    failure_action: rollback
    monitor: 60s
  rollback_config:
    parallelism: 1
    delay: 5s
  restart_policy:
    condition: on-failure
    delay: 5s
    max_attempts: 3
    window: 120s

services:
  # ========================================
  # Web应用层
  # ========================================
  app:
    image: registry.company.com/myapp:${VERSION:-latest}
    logging: *default-logging
    networks:
      - frontend
      - backend
    environment:
      NODE_ENV: production
      DATABASE_URL: postgresql://appuser:${DB_PASSWORD}@db:5432/appdb
      REDIS_URL: redis://redis:6379/0
    secrets:
      - db_password
      - app_secret_key
    configs:
      - source: app_config
        target: /etc/app/config.yaml
    deploy:
      <<: *deploy-defaults
      mode: replicated
      replicas: 6
      placement:
        constraints:
          - node.role == worker
          - node.labels.tier == app
        preferences:
          - spread: node.labels.zone  # 跨可用区分布
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.app.rule=Host(`app.example.com`)"
        - "traefik.http.services.app.loadbalancer.server.port=8080"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 40s

  # ========================================
  # 负载均衡/反向代理
  # ========================================
  traefik:
    image: traefik:v2.10
    logging: *default-logging
    ports:
      - target: 80
        published: 80
        protocol: tcp
        mode: host
      - target: 443
        published: 443
        protocol: tcp
        mode: host
      - target: 8080
        published: 8080
        protocol: tcp
        mode: host  # 监控面板
    networks:
      - frontend
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik-certs:/etc/traefik/certs
    configs:
      - source: traefik_config
        target: /etc/traefik/traefik.yml
    deploy:
      mode: global
      placement:
        constraints:
          - node.role == manager  # 仅在Manager节点运行
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.25'
          memory: 128M

  # ========================================
  # 数据库(有状态服务)
  # ========================================
  db:
    image: postgres:15-alpine
    logging: *default-logging
    networks:
      - backend
    environment:
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
      POSTGRES_DB: appdb
      PGDATA: /var/lib/postgresql/data/pgdata
    secrets:
      - db_password
    volumes:
      - postgres-data:/var/lib/postgresql/data
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - node.role == worker
          - node.labels.tier == db
          - node.labels.ssd == true  # 要求SSD存储
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
      restart_policy:
        condition: on-failure
        delay: 10s
        max_attempts: 5
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appuser"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ========================================
  # 缓存层
  # ========================================
  redis:
    image: redis:7-alpine
    logging: *default-logging
    networks:
      - backend
    command: >
      redis-server
      --requirepass ${REDIS_PASSWORD}
      --maxmemory 2gb
      --maxmemory-policy allkeys-lru
      --save 900 1
      --save 300 10
      --save 60 10000
      --appendonly yes
    secrets:
      - redis_password
    volumes:
      - redis-data:/data
    deploy:
      mode: replicated
      replicas: 3
      placement:
        constraints:
          - node.role == worker
          - node.labels.tier == cache
        preferences:
          - spread: node.labels.zone
      resources:
        limits:
          cpus: '1'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  # ========================================
  # 后台任务Worker
  # ========================================
  worker:
    image: registry.company.com/myapp:${VERSION:-latest}
    logging: *default-logging
    networks:
      - backend
    command: ["python", "worker.py"]
    environment:
      WORKER_CONCURRENCY: 4
      REDIS_URL: redis://redis:6379/0
    secrets:
      - db_password
    deploy:
      <<: *deploy-defaults
      mode: replicated
      replicas: 3
      placement:
        constraints:
          - node.role == worker
          - node.labels.tier == app
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  # ========================================
  # 定时任务调度器
  # ========================================
  scheduler:
    image: registry.company.com/myapp:${VERSION:-latest}
    logging: *default-logging
    networks:
      - backend
    command: ["python", "scheduler.py"]
    environment:
      REDIS_URL: redis://redis:6379/0
    secrets:
      - db_password
    deploy:
      mode: replicated
      replicas: 1  # 仅运行1个实例避免重复调度
      placement:
        constraints:
          - node.role == worker
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

# ========================================
# 网络配置
# ========================================
networks:
  frontend:
    driver: overlay
    attachable: true
    ipam:
      config:
        - subnet: 10.10.0.0/24
  backend:
    driver: overlay
    internal: true  # 内部网络,不允许外部访问
    attachable: true
    ipam:
      config:
        - subnet: 10.10.1.0/24

# ========================================
# 数据卷
# ========================================
volumes:
  postgres-data:
    driver: local
    driver_opts:
      type: nfs
      o: addr=192.168.1.100,rw,nolock
      device: ":/export/postgres-data"

  redis-data:
    driver: local

  traefik-certs:
    driver: local

# ========================================
# 配置文件
# ========================================
configs:
  app_config:
    file: ./configs/app-config.yaml

  traefik_config:
    file: ./configs/traefik.yml

# ========================================
# 秘钥
# ========================================
secrets:
  db_password:
    external: true

  redis_password:
    external: true

  app_secret_key:
    external: true
```

**部署与管理**:

```bash
# ========================================
# 创建外部秘钥
# ========================================

# 从文件创建秘钥
$ echo "MyDBPassword123" | docker secret create db_password -
$ echo "MyRedisPassword456" | docker secret create redis_password -
$ openssl rand -base64 32 | docker secret create app_secret_key -

# 验证秘钥
$ docker secret ls
ID            NAME              CREATED
abc123        db_password       10 seconds ago
def456        redis_password    8 seconds ago
ghi789        app_secret_key    5 seconds ago

# ========================================
# 部署Stack
# ========================================

# 部署到生产环境
$ docker stack deploy -c stack.yml --with-registry-auth myapp

# 验证部署状态
$ docker stack services myapp
ID        NAME           MODE        REPLICAS  IMAGE
abc123    myapp_app      replicated  6/6       registry.company.com/myapp:v1.2.3
def456    myapp_db       replicated  1/1       postgres:15-alpine
ghi789    myapp_redis    replicated  3/3       redis:7-alpine
jkl012    myapp_worker   replicated  3/3       registry.company.com/myapp:v1.2.3
mno345    myapp_traefik  global      3/3       traefik:v2.10

# 查看服务详情
$ docker service ps myapp_app
ID        NAME          IMAGE                           NODE      DESIRED STATE  CURRENT STATE
abc123    myapp_app.1   registry.company.com/myapp:v1  worker1   Running        Running 2 minutes ago
def456    myapp_app.2   registry.company.com/myapp:v1  worker2   Running        Running 2 minutes ago
ghi789    myapp_app.3   registry.company.com/myapp:v1  worker3   Running        Running 2 minutes ago

# 查看服务日志
$ docker service logs -f myapp_app --tail 100

# ========================================
# 扩缩容
# ========================================

# 水平扩容
$ docker service scale myapp_app=10

# 验证扩容
$ docker service ls
ID        NAME        REPLICAS
abc123    myapp_app   10/10

# ========================================
# 滚动更新
# ========================================

# 更新镜像版本
$ docker service update \
  --image registry.company.com/myapp:v1.2.4 \
  --update-parallelism 2 \
  --update-delay 30s \
  myapp_app

# 监控更新进度
$ watch -n 1 'docker service ps myapp_app'

# 回滚到上一版本
$ docker service rollback myapp_app

# ========================================
# 清理
# ========================================

# 删除Stack(保留数据卷)
$ docker stack rm myapp

# 完全清理(包括数据卷)
$ docker stack rm myapp
$ docker volume prune -f
```

---

### 13.1.3 Kubernetes集群架构(对比)

**适用场景**: 大型生产环境(100+台节点)、多集群管理

```bash
# Kubernetes vs Swarm 对比

┌────────────────┬─────────────────────┬─────────────────────┐
│   特性         │   Docker Swarm      │   Kubernetes        │
├────────────────┼─────────────────────┼─────────────────────┤
│ 学习曲线       │ ⭐⭐ 简单            │ ⭐⭐⭐⭐⭐ 复杂      │
│ 部署复杂度     │ ⭐⭐ 内置            │ ⭐⭐⭐⭐ 需额外安装  │
│ 集群规模       │ 中小(10-100节点)    │ 大型(1000+节点)     │
│ 生态系统       │ ⭐⭐⭐ 够用          │ ⭐⭐⭐⭐⭐ 丰富      │
│ 服务发现       │ 内置DNS             │ CoreDNS + Ingress   │
│ 负载均衡       │ Ingress自动         │ Service + Ingress   │
│ 存储编排       │ Volume插件          │ StorageClass + PV   │
│ 配置管理       │ Config + Secret     │ ConfigMap + Secret  │
│ 自动扩缩容     │ 手动scale           │ HPA自动             │
│ 多集群管理     │ ❌ 不支持            │ ✅ Federation       │
│ RBAC权限       │ ⭐⭐⭐ 基础          │ ⭐⭐⭐⭐⭐ 细粒度    │
│ 监控集成       │ 需自行部署          │ Metrics Server      │
│ 社区活跃度     │ ⭐⭐⭐ 中等          │ ⭐⭐⭐⭐⭐ 非常活跃  │
└────────────────┴─────────────────────┴─────────────────────┘

# 选型建议:
✅ Swarm: 中小型团队、快速上线、Docker原生、学习成本低
✅ K8s: 大型企业、复杂场景、需要高级特性、有运维团队
```

**K8s等效配置(仅供参考)**:

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  namespace: production
spec:
  replicas: 6
  selector:
    matchLabels:
      app: myapp
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: myapp
        version: v1.2.3
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - myapp
              topologyKey: kubernetes.io/hostname
      containers:
      - name: app
        image: registry.company.com/myapp:v1.2.3
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        resources:
          limits:
            cpu: "1"
            memory: "1Gi"
          requests:
            cpu: "500m"
            memory: "512Mi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 40
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: myapp-service
  namespace: production
spec:
  type: ClusterIP
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8080
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
  namespace: production
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - app.example.com
    secretName: app-tls
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myapp-service
            port:
              number: 80
```

---

## 13.2 服务发现与注册

### 13.2.1 Docker内置服务发现

**Swarm DNS自动服务发现**:

```bash
# Swarm自动为每个服务创建DNS记录

# 部署服务
$ docker service create --name web --replicas 3 nginx:alpine
$ docker service create --name api --replicas 5 myapi:latest

# 在任意容器内测试DNS解析
$ docker run --rm --network myapp_backend alpine nslookup web
Server:    127.0.0.11
Address 1: 127.0.0.11

Name:      web
Address 1: 10.0.1.2 web.1.abc123  # VIP(虚拟IP)

# DNS负载均衡测试
$ for i in {1..10}; do
    docker run --rm --network myapp_backend alpine \
      wget -qO- http://api:8080/health
  done

# Swarm自动轮询所有api服务副本
```

**服务别名(Service Alias)**:

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    image: myapp:latest
    networks:
      backend:
        aliases:
          - myapp  # 别名
          - application  # 多个别名

  db:
    image: postgres:15
    networks:
      backend:
        aliases:
          - database
          - postgres-master

networks:
  backend:
    driver: overlay
```

```bash
# 通过别名访问服务
$ docker run --rm --network backend alpine ping myapp
$ docker run --rm --network backend alpine ping application
$ docker run --rm --network backend alpine ping database
```

---

### 13.2.2 Consul服务注册与发现

**Consul架构**:

```bash
# Consul集群拓扑
┌─────────────────────────────────────────────┐
│           Consul Server集群 (3节点)         │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐│
│  │  Server 1  │ │  Server 2  │ │  Server 3  ││
│  │  (Leader)  │ │ (Follower) │ │ (Follower) ││
│  └────────────┘ └────────────┘ └────────────┘│
└─────────────────────────────────────────────┘
              │         │         │
    ┌─────────┴─────────┴─────────┴─────────┐
    │                                        │
┌───▼────┐  ┌────────┐  ┌────────┐  ┌────────┐
│Client 1│  │Client 2│  │Client 3│  │Client N│
│(Agent) │  │(Agent) │  │(Agent) │  │(Agent) │
└────────┘  └────────┘  └────────┘  └────────┘
```

**Consul部署**:

```yaml
# consul-stack.yml
version: '3.8'

services:
  # Consul Server集群
  consul-server-1:
    image: consul:1.17
    hostname: consul-server-1
    command: >
      agent -server -bootstrap-expect=3
      -ui -client=0.0.0.0
      -bind='{{ GetInterfaceIP "eth0" }}'
      -retry-join=consul-server-2
      -retry-join=consul-server-3
    environment:
      CONSUL_LOCAL_CONFIG: |
        {
          "datacenter": "dc1",
          "data_dir": "/consul/data",
          "log_level": "INFO",
          "node_name": "consul-server-1",
          "server": true
        }
    volumes:
      - consul-server-1-data:/consul/data
    networks:
      - consul-net
    ports:
      - "8500:8500"  # HTTP API
      - "8600:8600/udp"  # DNS
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - node.labels.consul == server1

  consul-server-2:
    image: consul:1.17
    hostname: consul-server-2
    command: >
      agent -server -bootstrap-expect=3
      -bind='{{ GetInterfaceIP "eth0" }}'
      -retry-join=consul-server-1
      -retry-join=consul-server-3
    environment:
      CONSUL_LOCAL_CONFIG: |
        {
          "datacenter": "dc1",
          "data_dir": "/consul/data",
          "log_level": "INFO",
          "node_name": "consul-server-2",
          "server": true
        }
    volumes:
      - consul-server-2-data:/consul/data
    networks:
      - consul-net
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - node.labels.consul == server2

  consul-server-3:
    image: consul:1.17
    hostname: consul-server-3
    command: >
      agent -server -bootstrap-expect=3
      -bind='{{ GetInterfaceIP "eth0" }}'
      -retry-join=consul-server-1
      -retry-join=consul-server-2
    environment:
      CONSUL_LOCAL_CONFIG: |
        {
          "datacenter": "dc1",
          "data_dir": "/consul/data",
          "log_level": "INFO",
          "node_name": "consul-server-3",
          "server": true
        }
    volumes:
      - consul-server-3-data:/consul/data
    networks:
      - consul-net
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - node.labels.consul == server3

  # Consul Client (每个Worker节点运行)
  consul-agent:
    image: consul:1.17
    command: >
      agent -client=0.0.0.0
      -bind='{{ GetInterfaceIP "eth0" }}'
      -retry-join=consul-server-1
      -retry-join=consul-server-2
      -retry-join=consul-server-3
    environment:
      CONSUL_LOCAL_CONFIG: |
        {
          "datacenter": "dc1",
          "data_dir": "/consul/data",
          "log_level": "INFO",
          "enable_script_checks": true,
          "leave_on_terminate": true
        }
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - consul-agent-data:/consul/data
    networks:
      - consul-net
    deploy:
      mode: global
      placement:
        constraints:
          - node.role == worker

networks:
  consul-net:
    driver: overlay
    attachable: true

volumes:
  consul-server-1-data:
  consul-server-2-data:
  consul-server-3-data:
  consul-agent-data:
```

**应用注册到Consul**:

```python
# app.py - Python应用示例
import os
import consul
import socket
from flask import Flask, jsonify

app = Flask(__name__)

# Consul配置
CONSUL_HOST = os.getenv('CONSUL_HOST', 'consul-agent')
CONSUL_PORT = int(os.getenv('CONSUL_PORT', 8500))
SERVICE_NAME = os.getenv('SERVICE_NAME', 'myapp')
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 8080))

def register_service():
    """注册服务到Consul"""
    c = consul.Consul(host=CONSUL_HOST, port=CONSUL_PORT)

    # 获取容器IP
    hostname = socket.gethostname()
    container_ip = socket.gethostbyname(hostname)

    # 健康检查配置
    check = consul.Check.http(
        url=f'http://{container_ip}:{SERVICE_PORT}/health',
        interval='10s',
        timeout='5s',
        deregister='30s'  # 30秒无响应自动注销
    )

    # 注册服务
    c.agent.service.register(
        name=SERVICE_NAME,
        service_id=f'{SERVICE_NAME}-{hostname}',
        address=container_ip,
        port=SERVICE_PORT,
        tags=['api', 'v1', 'production'],
        check=check,
        meta={
            'version': '1.2.3',
            'git_commit': 'abc123',
            'environment': 'production'
        }
    )
    print(f'✅ Service registered: {SERVICE_NAME} at {container_ip}:{SERVICE_PORT}')

def deregister_service():
    """注销服务"""
    c = consul.Consul(host=CONSUL_HOST, port=CONSUL_PORT)
    hostname = socket.gethostname()
    service_id = f'{SERVICE_NAME}-{hostname}'
    c.agent.service.deregister(service_id)
    print(f'✅ Service deregistered: {service_id}')

@app.route('/health')
def health():
    """健康检查端点"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/users')
def get_users():
    """业务API"""
    return jsonify({'users': []}), 200

if __name__ == '__main__':
    import atexit
    import signal

    # 启动时注册
    register_service()

    # 优雅关闭时注销
    def cleanup(signum, frame):
        deregister_service()
        exit(0)

    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)
    atexit.register(deregister_service)

    # 启动Flask
    app.run(host='0.0.0.0', port=SERVICE_PORT)
```

**服务发现客户端**:

```python
# client.py - 从Consul发现服务
import consul
import requests
import random

def discover_service(service_name='myapp'):
    """从Consul发现服务实例"""
    c = consul.Consul(host='consul-agent', port=8500)

    # 查询健康的服务实例
    index, services = c.health.service(service_name, passing=True)

    if not services:
        raise Exception(f'No healthy instances found for {service_name}')

    # 随机选择一个实例(客户端负载均衡)
    instance = random.choice(services)
    service_info = instance['Service']

    return {
        'address': service_info['Address'],
        'port': service_info['Port'],
        'tags': service_info['Tags'],
        'meta': service_info['Meta']
    }

# 使用示例
def call_api():
    service = discover_service('myapp')
    url = f"http://{service['address']}:{service['port']}/api/users"
    response = requests.get(url)
    return response.json()

# 测试
if __name__ == '__main__':
    for i in range(10):
        service = discover_service('myapp')
        print(f"Request {i+1}: {service['address']}:{service['port']}")
        result = call_api()
        print(f"  Response: {result}")
```

**Consul管理命令**:

```bash
# ========================================
# Consul集群管理
# ========================================

# 查看集群成员
$ docker exec consul-server-1 consul members
Node              Address          Status  Type    Build  Protocol  DC   Segment
consul-server-1   10.0.1.2:8301    alive   server  1.17   2         dc1  <all>
consul-server-2   10.0.1.3:8301    alive   server  1.17   2         dc1  <all>
consul-server-3   10.0.1.4:8301    alive   server  1.17   2         dc1  <all>
worker1           10.0.1.10:8301   alive   client  1.17   2         dc1  <default>
worker2           10.0.1.11:8301   alive   client  1.17   2         dc1  <default>

# 查看Leader
$ docker exec consul-server-1 consul operator raft list-peers
Node              ID               Address          State     Voter  RaftProtocol
consul-server-1   abc123           10.0.1.2:8300    leader    true   3
consul-server-2   def456           10.0.1.3:8300    follower  true   3
consul-server-3   ghi789           10.0.1.4:8300    follower  true   3

# ========================================
# 服务查询
# ========================================

# 查看所有服务
$ docker exec consul-server-1 consul catalog services
consul
myapp
postgres
redis

# 查看服务详情
$ docker exec consul-server-1 consul catalog service myapp
Node     Address    TaggedAddresses  ServiceID      ServiceName  ServiceTags
worker1  10.0.1.10  ...              myapp-abc123   myapp        api,v1,production
worker2  10.0.1.11  ...              myapp-def456   myapp        api,v1,production
worker3  10.0.1.12  ...              myapp-ghi789   myapp        api,v1,production

# DNS查询服务
$ dig @127.0.0.1 -p 8600 myapp.service.consul SRV
;; ANSWER SECTION:
myapp.service.consul. 0 IN SRV 1 1 8080 abc123.node.dc1.consul.
myapp.service.consul. 0 IN SRV 1 1 8080 def456.node.dc1.consul.
myapp.service.consul. 0 IN SRV 1 1 8080 ghi789.node.dc1.consul.

# ========================================
# 健康检查
# ========================================

# 查看服务健康状态
$ docker exec consul-server-1 consul health checks myapp
Node     CheckID          Name                 Status  Notes
worker1  service:myapp    Service 'myapp' check passing
worker2  service:myapp    Service 'myapp' check passing
worker3  service:myapp    Service 'myapp' check critical HTTP GET http://10.0.1.12:8080/health: timeout

# ========================================
# KV存储
# ========================================

# 写入配置
$ docker exec consul-server-1 consul kv put config/myapp/db_host postgres.example.com
$ docker exec consul-server-1 consul kv put config/myapp/db_port 5432

# 读取配置
$ docker exec consul-server-1 consul kv get config/myapp/db_host
postgres.example.com

# 监听配置变更
$ docker exec consul-server-1 consul watch -type=key -key=config/myapp/db_host \
  /usr/local/bin/reload-config.sh
```

---

## 13.3 负载均衡方案

### 13.3.1 HAProxy高可用负载均衡

**HAProxy + Keepalived架构**:

```bash
# 高可用负载均衡拓扑
┌────────────────────────────────────────┐
│       虚拟IP (VIP: 192.168.1.100)      │
│              Keepalived                │
│  ┌──────────────┐   ┌──────────────┐  │
│  │  HAProxy 1   │   │  HAProxy 2   │  │
│  │  (MASTER)    │   │  (BACKUP)    │  │
│  │192.168.1.101 │   │192.168.1.102 │  │
│  └──────────────┘   └──────────────┘  │
└────────────────────────────────────────┘
           │                 │
    ┌──────┴─────────────────┴──────┐
    │                                │
┌───▼────┐  ┌────────┐  ┌────────┐ ┌▼──────┐
│Backend │  │Backend │  │Backend │ │Backend│
│   1    │  │   2    │  │   3    │ │   N   │
└────────┘  └────────┘  └────────┘ └───────┘
```

**HAProxy配置**:

```bash
# haproxy.cfg
global
    log stdout format raw local0 info
    maxconn 40000
    user haproxy
    group haproxy
    daemon
    stats socket /var/run/haproxy.sock mode 660 level admin
    stats timeout 30s

    # SSL配置
    ssl-default-bind-ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256
    ssl-default-bind-options ssl-min-ver TLSv1.2 no-tls-tickets

defaults
    log     global
    mode    http
    option  httplog
    option  dontlognull
    option  http-server-close
    option  forwardfor except 127.0.0.0/8
    option  redispatch
    retries 3
    timeout connect 5000
    timeout client  50000
    timeout server  50000
    errorfile 400 /etc/haproxy/errors/400.http
    errorfile 403 /etc/haproxy/errors/403.http
    errorfile 408 /etc/haproxy/errors/408.http
    errorfile 500 /etc/haproxy/errors/500.http
    errorfile 502 /etc/haproxy/errors/502.http
    errorfile 503 /etc/haproxy/errors/503.http
    errorfile 504 /etc/haproxy/errors/504.http

# ========================================
# 监控面板
# ========================================
listen stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 5s
    stats show-legends
    stats show-node
    stats auth admin:SecurePassword123

# ========================================
# HTTP前端(80端口)
# ========================================
frontend http_front
    bind *:80
    mode http

    # 请求限速(防DDoS)
    stick-table type ip size 100k expire 30s store http_req_rate(10s)
    http-request track-sc0 src
    http-request deny if { sc_http_req_rate(0) gt 100 }

    # ACL规则
    acl is_api path_beg /api
    acl is_static path_end .jpg .jpeg .png .gif .css .js .ico .svg .woff .woff2
    acl is_health path /health

    # 路由规则
    use_backend api_backend if is_api
    use_backend static_backend if is_static
    use_backend health_backend if is_health
    default_backend web_backend

# ========================================
# HTTPS前端(443端口)
# ========================================
frontend https_front
    bind *:443 ssl crt /etc/haproxy/certs/example.com.pem alpn h2,http/1.1
    mode http

    # HSTS头
    http-response set-header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"

    # 同样的ACL和路由规则
    acl is_api path_beg /api
    acl is_static path_end .jpg .jpeg .png .gif .css .js .ico .svg .woff .woff2

    use_backend api_backend if is_api
    use_backend static_backend if is_static
    default_backend web_backend

# ========================================
# Web应用后端
# ========================================
backend web_backend
    mode http
    balance roundrobin
    option httpchk GET /health
    http-check expect status 200

    # 后端服务器
    server web1 192.168.1.21:8080 check inter 5s fall 3 rise 2 weight 100
    server web2 192.168.1.22:8080 check inter 5s fall 3 rise 2 weight 100
    server web3 192.168.1.23:8080 check inter 5s fall 3 rise 2 weight 100
    server web4 192.168.1.24:8080 check inter 5s fall 3 rise 2 weight 50 backup

# ========================================
# API后端(粘性会话)
# ========================================
backend api_backend
    mode http
    balance leastconn
    option httpchk GET /api/health
    http-check expect status 200

    # Cookie粘性会话
    cookie SERVERID insert indirect nocache

    server api1 192.168.1.31:8080 check cookie api1 inter 5s
    server api2 192.168.1.32:8080 check cookie api2 inter 5s
    server api3 192.168.1.33:8080 check cookie api3 inter 5s
    server api4 192.168.1.34:8080 check cookie api4 inter 5s
    server api5 192.168.1.35:8080 check cookie api5 inter 5s

# ========================================
# 静态资源后端(缓存)
# ========================================
backend static_backend
    mode http
    balance roundrobin
    option httpchk GET /health

    # 缓存配置
    http-request cache-use static_cache
    http-response cache-store static_cache

    server static1 192.168.1.41:8080 check inter 10s
    server static2 192.168.1.42:8080 check inter 10s

cache static_cache
    total-max-size 256
    max-object-size 10240
    max-age 3600

# ========================================
# 健康检查后端
# ========================================
backend health_backend
    mode http
    server health 127.0.0.1:8404
```

**Keepalived配置(HAProxy 1 - MASTER)**:

```bash
# /etc/keepalived/keepalived.conf (HAProxy 1)
global_defs {
    router_id HAProxy_1
    vrrp_skip_check_adv_addr
    vrrp_garp_interval 0
    vrrp_gna_interval 0
}

vrrp_script chk_haproxy {
    script "/usr/bin/killall -0 haproxy"
    interval 2
    weight 2
}

vrrp_instance VI_1 {
    state MASTER
    interface eth0
    virtual_router_id 51
    priority 101
    advert_int 1

    authentication {
        auth_type PASS
        auth_pass SecurePassword123
    }

    virtual_ipaddress {
        192.168.1.100/24
    }

    track_script {
        chk_haproxy
    }

    notify_master "/etc/keepalived/notify.sh MASTER"
    notify_backup "/etc/keepalived/notify.sh BACKUP"
    notify_fault "/etc/keepalived/notify.sh FAULT"
}
```

**Keepalived配置(HAProxy 2 - BACKUP)**:

```bash
# /etc/keepalived/keepalived.conf (HAProxy 2)
global_defs {
    router_id HAProxy_2
    vrrp_skip_check_adv_addr
    vrrp_garp_interval 0
    vrrp_gna_interval 0
}

vrrp_script chk_haproxy {
    script "/usr/bin/killall -0 haproxy"
    interval 2
    weight 2
}

vrrp_instance VI_1 {
    state BACKUP
    interface eth0
    virtual_router_id 51
    priority 100  # 比MASTER低
    advert_int 1

    authentication {
        auth_type PASS
        auth_pass SecurePassword123
    }

    virtual_ipaddress {
        192.168.1.100/24
    }

    track_script {
        chk_haproxy
    }

    notify_master "/etc/keepalived/notify.sh MASTER"
    notify_backup "/etc/keepalived/notify.sh BACKUP"
    notify_fault "/etc/keepalived/notify.sh FAULT"
}
```

**Docker Compose部署HAProxy**:

```yaml
# haproxy-stack.yml
version: '3.8'

services:
  haproxy:
    image: haproxy:2.9-alpine
    ports:
      - target: 80
        published: 80
        protocol: tcp
        mode: host
      - target: 443
        published: 443
        protocol: tcp
        mode: host
      - target: 8404
        published: 8404
        protocol: tcp
        mode: host
    volumes:
      - ./haproxy/haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro
      - ./haproxy/certs:/etc/haproxy/certs:ro
      - haproxy-logs:/var/log/haproxy
    networks:
      - frontend
      - backend
    deploy:
      mode: global
      placement:
        constraints:
          - node.labels.lb == true
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '1'
          memory: 512M
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"
    healthcheck:
      test: ["CMD", "nc", "-z", "127.0.0.1", "80"]
      interval: 10s
      timeout: 3s
      retries: 3

networks:
  frontend:
    driver: overlay
    attachable: true
  backend:
    driver: overlay
    attachable: true

volumes:
  haproxy-logs:
```

**验证与监控**:

```bash
# ========================================
# 验证VIP
# ========================================

# HAProxy 1上查看VIP
$ ip addr show eth0 | grep 192.168.1.100
    inet 192.168.1.100/24 scope global secondary eth0

# 测试故障转移
# 在HAProxy 1上停止服务
$ systemctl stop haproxy

# VIP应自动漂移到HAProxy 2
$ ip addr show eth0 | grep 192.168.1.100  # HAProxy 2上执行
    inet 192.168.1.100/24 scope global secondary eth0

# ========================================
# 访问监控面板
# ========================================

# 浏览器访问:
# http://192.168.1.100:8404/stats
# 用户名: admin
# 密码: SecurePassword123

# 命令行查看统计
$ echo "show stat" | socat unix-connect:/var/run/haproxy.sock stdio

# ========================================
# 压力测试
# ========================================

# 使用ab进行压测
$ ab -n 100000 -c 100 http://192.168.1.100/

# 使用wrk进行压测
$ wrk -t 12 -c 400 -d 60s http://192.168.1.100/

# 观察HAProxy统计
$ watch -n 1 'echo "show stat" | socat unix-connect:/var/run/haproxy.sock stdio | grep web_backend'
```

---

### 13.3.2 Traefik动态负载均衡

**Traefik特点**:
- ✅ 自动服务发现(Docker/Swarm/K8s)
- ✅ 自动HTTPS(Let's Encrypt)
- ✅ 动态配置(无需重启)
- ✅ 中间件支持(认证/限流/压缩)
- ✅ WebSocket/gRPC支持
- ✅ 现代化Dashboard

**Traefik配置**:

```yaml
# traefik/traefik.yml
# ========================================
# 全局配置
# ========================================
global:
  checkNewVersion: true
  sendAnonymousUsage: false

# ========================================
# API和Dashboard
# ========================================
api:
  dashboard: true
  insecure: false  # 生产环境必须false

# ========================================
# 日志
# ========================================
log:
  level: INFO
  format: json
  filePath: /var/log/traefik/traefik.log

accessLog:
  filePath: /var/log/traefik/access.log
  format: json
  fields:
    headers:
      defaultMode: keep
      names:
        User-Agent: keep
        Authorization: drop
        Content-Type: keep

# ========================================
# 入口点(EntryPoints)
# ========================================
entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
          permanent: true

  websecure:
    address: ":443"
    http:
      tls:
        certResolver: letsencrypt

  metrics:
    address: ":8082"

# ========================================
# 证书解析器(Let's Encrypt)
# ========================================
certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@example.com
      storage: /etc/traefik/acme/acme.json
      httpChallenge:
        entryPoint: web
      # 生产环境使用:
      # caServer: "https://acme-v02.api.letsencrypt.org/directory"
      # 测试环境使用:
      caServer: "https://acme-staging-v02.api.letsencrypt.org/directory"

# ========================================
# 提供商(Providers)
# ========================================
providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false  # 默认不暴露服务
    network: traefik-public
    swarmMode: true
    watch: true

  file:
    directory: /etc/traefik/dynamic
    watch: true

# ========================================
# 指标(Metrics)
# ========================================
metrics:
  prometheus:
    entryPoint: metrics
    addEntryPointsLabels: true
    addServicesLabels: true
    buckets:
      - 0.1
      - 0.3
      - 1.2
      - 5.0
```

**Traefik Stack部署**:

```yaml
# traefik-stack.yml
version: '3.8'

services:
  traefik:
    image: traefik:v2.10
    command:
      - "--configFile=/etc/traefik/traefik.yml"
    ports:
      - target: 80
        published: 80
        protocol: tcp
        mode: host
      - target: 443
        published: 443
        protocol: tcp
        mode: host
      - target: 8082
        published: 8082
        protocol: tcp
        mode: host
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik/traefik.yml:/etc/traefik/traefik.yml:ro
      - ./traefik/dynamic:/etc/traefik/dynamic:ro
      - traefik-certs:/etc/traefik/acme
      - traefik-logs:/var/log/traefik
    networks:
      - traefik-public
    deploy:
      mode: global
      placement:
        constraints:
          - node.role == manager
      labels:
        # Dashboard路由
        - "traefik.enable=true"
        - "traefik.http.routers.dashboard.rule=Host(`traefik.example.com`)"
        - "traefik.http.routers.dashboard.entrypoints=websecure"
        - "traefik.http.routers.dashboard.tls.certresolver=letsencrypt"
        - "traefik.http.routers.dashboard.service=api@internal"
        # Dashboard认证
        - "traefik.http.routers.dashboard.middlewares=dashboard-auth"
        - "traefik.http.middlewares.dashboard-auth.basicauth.users=admin:$$apr1$$xxx"  # htpasswd生成
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "3"

networks:
  traefik-public:
    driver: overlay
    attachable: true

volumes:
  traefik-certs:
  traefik-logs:
```

**应用服务配置(使用Traefik标签)**:

```yaml
# app-stack.yml
version: '3.8'

services:
  # Web应用
  app:
    image: myapp:latest
    networks:
      - traefik-public
      - backend
    environment:
      DATABASE_URL: postgresql://db:5432/appdb
    deploy:
      replicas: 6
      labels:
        # 启用Traefik
        - "traefik.enable=true"

        # HTTP路由
        - "traefik.http.routers.app.rule=Host(`app.example.com`)"
        - "traefik.http.routers.app.entrypoints=websecure"
        - "traefik.http.routers.app.tls.certresolver=letsencrypt"

        # 服务配置
        - "traefik.http.services.app.loadbalancer.server.port=8080"
        - "traefik.http.services.app.loadbalancer.sticky.cookie=true"
        - "traefik.http.services.app.loadbalancer.sticky.cookie.name=SERVERID"
        - "traefik.http.services.app.loadbalancer.healthcheck.path=/health"
        - "traefik.http.services.app.loadbalancer.healthcheck.interval=10s"

        # 中间件: 压缩
        - "traefik.http.middlewares.app-compress.compress=true"
        # 中间件: 限流
        - "traefik.http.middlewares.app-ratelimit.ratelimit.average=100"
        - "traefik.http.middlewares.app-ratelimit.ratelimit.burst=50"
        # 中间件: 安全头
        - "traefik.http.middlewares.app-headers.headers.sslredirect=true"
        - "traefik.http.middlewares.app-headers.headers.stsSeconds=31536000"
        - "traefik.http.middlewares.app-headers.headers.contentTypeNosniff=true"
        - "traefik.http.middlewares.app-headers.headers.browserXssFilter=true"
        - "traefik.http.middlewares.app-headers.headers.frameDeny=true"

        # 应用中间件
        - "traefik.http.routers.app.middlewares=app-compress,app-ratelimit,app-headers"

      resources:
        limits:
          cpus: '1'
          memory: 1G

  # API服务(不同域名)
  api:
    image: myapi:latest
    networks:
      - traefik-public
      - backend
    deploy:
      replicas: 5
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.api.rule=Host(`api.example.com`)"
        - "traefik.http.routers.api.entrypoints=websecure"
        - "traefik.http.routers.api.tls.certresolver=letsencrypt"
        - "traefik.http.services.api.loadbalancer.server.port=3000"
        - "traefik.http.middlewares.api-cors.headers.accesscontrolallowmethods=GET,POST,PUT,DELETE"
        - "traefik.http.middlewares.api-cors.headers.accesscontrolalloworiginlist=https://app.example.com"
        - "traefik.http.middlewares.api-cors.headers.accesscontrolmaxage=100"
        - "traefik.http.middlewares.api-cors.headers.addvaryheader=true"
        - "traefik.http.routers.api.middlewares=api-cors"

  # 静态文件服务
  static:
    image: nginx:alpine
    networks:
      - traefik-public
    volumes:
      - static-files:/usr/share/nginx/html:ro
    deploy:
      replicas: 3
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.static.rule=Host(`static.example.com`)"
        - "traefik.http.routers.static.entrypoints=websecure"
        - "traefik.http.routers.static.tls.certresolver=letsencrypt"
        - "traefik.http.services.static.loadbalancer.server.port=80"
        # 静态资源缓存
        - "traefik.http.middlewares.static-cache.headers.customResponseHeaders.Cache-Control=public, max-age=31536000, immutable"
        - "traefik.http.routers.static.middlewares=static-cache,app-compress"

networks:
  traefik-public:
    external: true
  backend:
    driver: overlay
    internal: true

volumes:
  static-files:
```

**动态配置文件**:

```yaml
# traefik/dynamic/middlewares.yml
http:
  middlewares:
    # 自定义错误页面
    custom-errors:
      errors:
        status:
          - "404"
          - "500-599"
        service: error-pages
        query: "/{status}.html"

    # IP白名单
    ip-whitelist:
      ipWhiteList:
        sourceRange:
          - "127.0.0.1/32"
          - "192.168.1.0/24"
          - "10.0.0.0/8"

    # Basic认证
    basic-auth:
      basicAuth:
        users:
          - "admin:$apr1$xxx..."  # htpasswd生成
          - "user:$apr1$yyy..."
        removeHeader: true

    # 重定向
    redirect-www:
      redirectRegex:
        regex: "^https://example.com/(.*)"
        replacement: "https://www.example.com/${1}"
        permanent: true

  services:
    error-pages:
      loadBalancer:
        servers:
          - url: "http://error-pages:8080"
```

**验证与监控**:

```bash
# ========================================
# 部署Traefik
# ========================================

# 创建网络
$ docker network create --driver=overlay traefik-public

# 部署Traefik
$ docker stack deploy -c traefik-stack.yml traefik

# 部署应用
$ docker stack deploy -c app-stack.yml myapp

# ========================================
# 验证
# ========================================

# 查看Traefik日志
$ docker service logs -f traefik_traefik

# 访问Dashboard
# https://traefik.example.com/dashboard/

# 查看路由
$ curl -s http://localhost:8080/api/http/routers | jq

# 查看服务
$ curl -s http://localhost:8080/api/http/services | jq

# ========================================
# 测试自动HTTPS
# ========================================

# 测试HTTP重定向到HTTPS
$ curl -I http://app.example.com
HTTP/1.1 308 Permanent Redirect
Location: https://app.example.com/

# 测试HTTPS
$ curl -I https://app.example.com
HTTP/2 200
Strict-Transport-Security: max-age=31536000

# ========================================
# Prometheus指标
# ========================================

# 访问指标端点
$ curl http://localhost:8082/metrics

# 指标示例
traefik_entrypoint_requests_total{code="200",entrypoint="websecure",method="GET",protocol="http"} 1234
traefik_service_requests_total{code="200",method="GET",service="app@docker"} 5678
```

---

## 13.4 反向代理与API网关

### 13.4.1 Nginx作为API网关

**Nginx API网关配置**:

```nginx
# /etc/nginx/nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 10000;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # 日志格式
    log_format api '$remote_addr - $remote_user [$time_local] '
                   '"$request" $status $body_bytes_sent '
                   '"$http_referer" "$http_user_agent" '
                   'request_id=$request_id '
                   'upstream_addr=$upstream_addr '
                   'upstream_status=$upstream_status '
                   'request_time=$request_time '
                   'upstream_response_time=$upstream_response_time '
                   'upstream_connect_time=$upstream_connect_time '
                   'upstream_header_time=$upstream_header_time';

    access_log /var/log/nginx/access.log api;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 20M;
    client_body_buffer_size 128k;

    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # 缓存配置
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m inactive=60m use_temp_path=off;

    # 限流区域
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/s;
    limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/s;
    limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

    # 上游服务
    upstream auth_service {
        least_conn;
        server auth:3000 max_fails=3 fail_timeout=30s;
        server auth:3001 max_fails=3 fail_timeout=30s backup;
        keepalive 32;
    }

    upstream user_service {
        least_conn;
        server user:4000 max_fails=3 fail_timeout=30s weight=2;
        server user:4001 max_fails=3 fail_timeout=30s weight=1;
        keepalive 32;
    }

    upstream order_service {
        least_conn;
        server order:5000 max_fails=3 fail_timeout=30s;
        server order:5001 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    # API网关主配置
    server {
        listen 80;
        server_name api.example.com;

        # 安全头
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Request-ID $request_id always;

        # CORS配置
        add_header Access-Control-Allow-Origin "https://app.example.com" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization" always;
        add_header Access-Control-Expose-Headers "Content-Length,Content-Range" always;
        add_header Access-Control-Max-Age 1728000 always;

        # OPTIONS请求处理
        if ($request_method = 'OPTIONS') {
            return 204;
        }

        # ====================================
        # 认证服务(/api/auth/*)
        # ====================================
        location /api/auth/ {
            # 限流: 每秒5个请求
            limit_req zone=auth_limit burst=10 nodelay;
            limit_conn conn_limit 10;

            # 代理配置
            proxy_pass http://auth_service/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Request-ID $request_id;

            proxy_connect_timeout 5s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
            proxy_buffering off;

            # 错误处理
            proxy_intercept_errors on;
            error_page 502 503 504 = @fallback_auth;
        }

        # ====================================
        # 用户服务(/api/users/*)  需要JWT认证
        # ====================================
        location /api/users/ {
            # JWT验证(使用auth_request)
            auth_request /api/auth/verify;
            auth_request_set $auth_user_id $upstream_http_x_user_id;
            auth_request_set $auth_user_role $upstream_http_x_user_role;

            # 限流
            limit_req zone=api_limit burst=50 nodelay;

            # 代理配置
            proxy_pass http://user_service/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-User-ID $auth_user_id;
            proxy_set_header X-User-Role $auth_user_role;
            proxy_set_header X-Request-ID $request_id;

            # 缓存配置(GET请求)
            proxy_cache api_cache;
            proxy_cache_methods GET;
            proxy_cache_key "$scheme$request_method$host$request_uri$auth_user_id";
            proxy_cache_valid 200 5m;
            proxy_cache_valid 404 1m;
            proxy_cache_bypass $http_cache_control;
            add_header X-Cache-Status $upstream_cache_status;
        }

        # ====================================
        # 订单服务(/api/orders/*)  需要认证
        # ====================================
        location /api/orders/ {
            # JWT验证
            auth_request /api/auth/verify;
            auth_request_set $auth_user_id $upstream_http_x_user_id;

            # 限流
            limit_req zone=api_limit burst=30 nodelay;

            # 代理配置
            proxy_pass http://order_service/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-User-ID $auth_user_id;
            proxy_set_header X-Request-ID $request_id;

            # 超时配置(订单处理可能较慢)
            proxy_connect_timeout 10s;
            proxy_send_timeout 120s;
            proxy_read_timeout 120s;
        }

        # ====================================
        # JWT验证端点(内部)
        # ====================================
        location = /api/auth/verify {
            internal;
            proxy_pass http://auth_service/verify;
            proxy_pass_request_body off;
            proxy_set_header Content-Length "";
            proxy_set_header X-Original-URI $request_uri;
            proxy_set_header Authorization $http_authorization;
        }

        # ====================================
        # 健康检查
        # ====================================
        location /health {
            access_log off;
            add_header Content-Type text/plain;
            return 200 "healthy\n";
        }

        # ====================================
        # Fallback处理
        # ====================================
        location @fallback_auth {
            add_header Content-Type application/json;
            return 503 '{"error":"Authentication service temporarily unavailable"}';
        }
    }
}
```

**JWT验证服务示例(auth_service)**:

```javascript
// auth-service/server.js
const express = require('express');
const jwt = require('jsonwebtoken');
const app = express();

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

// 登录端点
app.post('/login', express.json(), (req, res) => {
    const { username, password } = req.body;

    // 验证用户名密码(示例)
    if (username === 'admin' && password === 'password') {
        const token = jwt.sign(
            {
                userId: 1,
                username: 'admin',
                role: 'admin'
            },
            JWT_SECRET,
            { expiresIn: '24h' }
        );

        res.json({ token });
    } else {
        res.status(401).json({ error: 'Invalid credentials' });
    }
});

// JWT验证端点(供Nginx auth_request使用)
app.get('/verify', (req, res) => {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return res.status(401).send('Unauthorized');
    }

    const token = authHeader.substring(7);

    try {
        const decoded = jwt.verify(token, JWT_SECRET);

        // 设置自定义响应头(Nginx会传递给后端)
        res.setHeader('X-User-ID', decoded.userId);
        res.setHeader('X-User-Role', decoded.role);
        res.setHeader('X-Username', decoded.username);

        res.status(200).send('OK');
    } catch (err) {
        res.status(401).send('Invalid token');
    }
});

app.listen(3000, () => {
    console.log('Auth service listening on port 3000');
});
```

**Docker Compose部署**:

```yaml
# api-gateway-stack.yml
version: '3.8'

services:
  # Nginx API网关
  api-gateway:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - nginx-cache:/var/cache/nginx
      - nginx-logs:/var/log/nginx
    networks:
      - frontend
      - backend
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 512M
    depends_on:
      - auth
      - user
      - order

  # 认证服务
  auth:
    image: auth-service:latest
    environment:
      JWT_SECRET: ${JWT_SECRET}
      NODE_ENV: production
    networks:
      - backend
    deploy:
      replicas: 2

  # 用户服务
  user:
    image: user-service:latest
    networks:
      - backend
    deploy:
      replicas: 3

  # 订单服务
  order:
    image: order-service:latest
    networks:
      - backend
    deploy:
      replicas: 3

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true

volumes:
  nginx-cache:
  nginx-logs:
```

**测试API网关**:

```bash
# ========================================
# 测试认证
# ========================================

# 登录获取JWT
$ curl -X POST http://api.example.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# 响应:
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

# ========================================
# 测试需要认证的API
# ========================================

# 无Token访问(被拒绝)
$ curl http://api.example.com/api/users/profile
# 响应: 401 Unauthorized

# 带Token访问(成功)
$ TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
$ curl -H "Authorization: Bearer $TOKEN" \
  http://api.example.com/api/users/profile

# 响应:
{
  "userId": 1,
  "username": "admin",
  "role": "admin"
}

# 查看请求ID(用于追踪)
$ curl -I -H "Authorization: Bearer $TOKEN" \
  http://api.example.com/api/users/profile | grep X-Request-ID
X-Request-ID: abc123def456

# ========================================
# 测试限流
# ========================================

# 快速发送100个请求(会触发限流)
$ for i in {1..100}; do
    curl -H "Authorization: Bearer $TOKEN" \
      http://api.example.com/api/users/profile &
  done

# 部分响应: 429 Too Many Requests

# ========================================
# 测试缓存
# ========================================

# 第一次请求(MISS)
$ curl -H "Authorization: Bearer $TOKEN" \
  http://api.example.com/api/users/1 -I | grep X-Cache-Status
X-Cache-Status: MISS

# 第二次请求(HIT)
$ curl -H "Authorization: Bearer $TOKEN" \
  http://api.example.com/api/users/1 -I | grep X-Cache-Status
X-Cache-Status: HIT
```

---

## 13.5 配置管理与秘钥管理

### 13.5.1 Docker Secrets(Swarm内置)

**创建秘钥**:

```bash
# ========================================
# 从文件创建秘钥
# ========================================

# 数据库密码
$ echo "MySecureDBPassword123!" > db_password.txt
$ docker secret create db_password db_password.txt
$ rm db_password.txt  # 删除明文文件

# 从标准输入创建
$ echo "MyRedisPassword456!" | docker secret create redis_password -

# 从环境变量创建
$ openssl rand -base64 32 | docker secret create jwt_secret -

# TLS证书
$ docker secret create ssl_cert ./certs/fullchain.pem
$ docker secret create ssl_key ./certs/privkey.pem

# ========================================
# 查看秘钥
# ========================================

$ docker secret ls
ID                NAME            CREATED
abc123            db_password     10 minutes ago
def456            redis_password  5 minutes ago
ghi789            jwt_secret      2 minutes ago

# 查看秘钥详情(不显示内容)
$ docker secret inspect db_password
[
    {
        "ID": "abc123",
        "Version": {
            "Index": 10
        },
        "CreatedAt": "2023-12-04T10:00:00Z",
        "UpdatedAt": "2023-12-04T10:00:00Z",
        "Spec": {
            "Name": "db_password",
            "Labels": {}
        }
    }
]
```

**在服务中使用秘钥**:

```yaml
# stack.yml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      # 通过_FILE后缀引用秘钥文件
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
      POSTGRES_USER: appuser
      POSTGRES_DB: appdb
    secrets:
      - db_password
    deploy:
      replicas: 1

  app:
    image: myapp:latest
    environment:
      # 应用代码需要读取秘钥文件
      DB_PASSWORD_FILE: /run/secrets/db_password
      JWT_SECRET_FILE: /run/secrets/jwt_secret
    secrets:
      - db_password
      - jwt_secret
    deploy:
      replicas: 5

secrets:
  db_password:
    external: true  # 使用已存在的秘钥

  jwt_secret:
    external: true
```

**应用代码读取秘钥**:

```python
# app.py
import os

def read_secret(secret_name):
    """从Docker Secrets读取秘钥"""
    secret_file = os.getenv(f'{secret_name.upper()}_FILE',
                            f'/run/secrets/{secret_name}')
    try:
        with open(secret_file, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        # Fallback到环境变量(开发环境)
        return os.getenv(secret_name.upper())

# 使用秘钥
DB_PASSWORD = read_secret('db_password')
JWT_SECRET = read_secret('jwt_secret')

# 数据库连接
DATABASE_URL = f"postgresql://appuser:{DB_PASSWORD}@db:5432/appdb"
```

**轮换秘钥**:

```bash
# ========================================
# 秘钥轮换步骤
# ========================================

# 1. 创建新秘钥
$ echo "NewDBPassword789!" | docker secret create db_password_v2 -

# 2. 更新服务使用新秘钥
$ docker service update \
  --secret-rm db_password \
  --secret-add source=db_password_v2,target=db_password \
  myapp_db

# 3. 验证服务正常
$ docker service ps myapp_db

# 4. 删除旧秘钥
$ docker secret rm db_password

# 5. 重命名新秘钥(可选)
# Docker不支持重命名,需要重新创建
```

---

### 13.5.2 Vault集成(企业级秘钥管理)

**HashiCorp Vault架构**:

```bash
# Vault集群架构
┌─────────────────────────────────────────┐
│         Vault集群 (HA模式)              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │ Vault 1  │  │ Vault 2  │  │ Vault 3  ││
│  │ (Active) │  │ (Standby)│  │ (Standby)││
│  └──────────┘  └──────────┘  └──────────┘│
│       │              │              │     │
│       └──────────────┴──────────────┘     │
│                    │                      │
│          ┌─────────▼─────────┐           │
│          │   Consul Backend  │           │
│          │  (存储+HA协调)     │           │
│          └───────────────────┘           │
└─────────────────────────────────────────┘
```

**Vault部署**:

```yaml
# vault-stack.yml
version: '3.8'

services:
  # Consul(Vault后端存储)
  consul:
    image: consul:1.17
    command: agent -server -bootstrap-expect=1 -ui -client=0.0.0.0
    environment:
      CONSUL_LOCAL_CONFIG: |
        {
          "datacenter": "dc1",
          "data_dir": "/consul/data",
          "log_level": "INFO"
        }
    volumes:
      - consul-data:/consul/data
    networks:
      - vault-net
    ports:
      - "8500:8500"

  # Vault Server
  vault:
    image: hashicorp/vault:1.15
    ports:
      - "8200:8200"
    environment:
      VAULT_ADDR: http://0.0.0.0:8200
      VAULT_API_ADDR: http://vault:8200
    cap_add:
      - IPC_LOCK
    volumes:
      - ./vault/config:/vault/config:ro
      - vault-data:/vault/data
      - vault-logs:/vault/logs
    networks:
      - vault-net
    command: server
    deploy:
      replicas: 1
      resources:
        limits:
          cpus: '1'
          memory: 1G

networks:
  vault-net:
    driver: overlay

volumes:
  consul-data:
  vault-data:
  vault-logs:
```

**Vault配置文件**:

```hcl
# vault/config/vault.hcl
storage "consul" {
  address = "consul:8500"
  path    = "vault/"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1
}

api_addr = "http://vault:8200"
cluster_addr = "https://vault:8201"
ui = true

# 日志配置
log_level = "info"
log_format = "json"

# Telemetry
telemetry {
  prometheus_retention_time = "30s"
  disable_hostname = false
}
```

**初始化Vault**:

```bash
# ========================================
# 初始化Vault
# ========================================

# 部署Vault
$ docker stack deploy -c vault-stack.yml vault

# 等待Vault启动
$ docker service logs -f vault_vault

# 初始化Vault(仅第一次)
$ docker exec -it $(docker ps -q -f name=vault_vault) vault operator init
Unseal Key 1: abc123...
Unseal Key 2: def456...
Unseal Key 3: ghi789...
Unseal Key 4: jkl012...
Unseal Key 5: mno345...

Initial Root Token: s.xxxxxxxxxxxx

# ⚠️ 重要: 保存Unseal Keys和Root Token到安全地方!

# ========================================
# 解封Vault(每次重启后需要)
# ========================================

# 需要3个Unseal Key才能解封
$ docker exec -it $(docker ps -q -f name=vault_vault) \
  vault operator unseal abc123...

$ docker exec -it $(docker ps -q -f name=vault_vault) \
  vault operator unseal def456...

$ docker exec -it $(docker ps -q -f name=vault_vault) \
  vault operator unseal ghi789...

# 验证状态
$ docker exec -it $(docker ps -q -f name=vault_vault) \
  vault status

Key             Value
---             -----
Seal Type       shamir
Initialized     true
Sealed          false  # ✅ 已解封
Total Shares    5
Threshold       3
Version         1.15.0
```

**配置Vault**:

```bash
# ========================================
# 登录Vault
# ========================================

$ export VAULT_ADDR='http://localhost:8200'
$ vault login s.xxxxxxxxxxxx  # 使用Root Token

# ========================================
# 启用KV秘钥引擎
# ========================================

# 启用KV v2引擎
$ vault secrets enable -version=2 kv

# 写入秘钥
$ vault kv put kv/myapp/production \
  db_password="MySecureDBPassword123!" \
  redis_password="MyRedisPassword456!" \
  jwt_secret="MyJWTSecret789!"

# 读取秘钥
$ vault kv get kv/myapp/production
===== Data =====
Key               Value
---               -----
db_password       MySecureDBPassword123!
redis_password    MyRedisPassword456!
jwt_secret        MyJWTSecret789!

# 读取特定字段
$ vault kv get -field=db_password kv/myapp/production
MySecureDBPassword123!

# ========================================
# 创建策略(最小权限)
# ========================================

# 创建策略文件
$ cat <<EOF > myapp-policy.hcl
# 允许读取myapp的生产秘钥
path "kv/data/myapp/production" {
  capabilities = ["read"]
}

# 允许列出秘钥
path "kv/metadata/myapp/*" {
  capabilities = ["list"]
}
EOF

# 应用策略
$ vault policy write myapp myapp-policy.hcl

# ========================================
# 创建AppRole(供应用使用)
# ========================================

# 启用AppRole认证
$ vault auth enable approle

# 创建角色
$ vault write auth/approle/role/myapp \
  token_policies="myapp" \
  token_ttl=1h \
  token_max_ttl=24h \
  secret_id_ttl=0

# 获取Role ID
$ vault read auth/approle/role/myapp/role-id
role_id    abc-123-def-456

# 生成Secret ID
$ vault write -f auth/approle/role/myapp/secret-id
secret_id            xyz-789-uvw-012
secret_id_accessor   ...
```

**应用集成Vault**:

```python
# app.py - Python集成Vault
import hvac
import os

# Vault配置
VAULT_ADDR = os.getenv('VAULT_ADDR', 'http://vault:8200')
VAULT_ROLE_ID = os.getenv('VAULT_ROLE_ID')
VAULT_SECRET_ID = os.getenv('VAULT_SECRET_ID')

def get_vault_client():
    """创建Vault客户端"""
    client = hvac.Client(url=VAULT_ADDR)

    # 使用AppRole登录
    client.auth.approle.login(
        role_id=VAULT_ROLE_ID,
        secret_id=VAULT_SECRET_ID
    )

    if not client.is_authenticated():
        raise Exception('Vault authentication failed')

    return client

def get_secrets():
    """从Vault获取秘钥"""
    client = get_vault_client()

    # 读取秘钥
    secret = client.secrets.kv.v2.read_secret_version(
        path='myapp/production',
        mount_point='kv'
    )

    return secret['data']['data']

# 使用秘钥
secrets = get_secrets()
DB_PASSWORD = secrets['db_password']
REDIS_PASSWORD = secrets['redis_password']
JWT_SECRET = secrets['jwt_secret']

print(f"✅ Successfully loaded {len(secrets)} secrets from Vault")
```

**Docker Compose集成**:

```yaml
# app-stack.yml
version: '3.8'

services:
  app:
    image: myapp:latest
    environment:
      VAULT_ADDR: http://vault:8200
      VAULT_ROLE_ID: abc-123-def-456
      VAULT_SECRET_ID: xyz-789-uvw-012
    networks:
      - vault-net
      - backend
    deploy:
      replicas: 5
    command: >
      sh -c "python -c 'from app import get_secrets; get_secrets()' &&
             python app.py"

networks:
  vault-net:
    external: true
  backend:
    driver: overlay
```

---

### 13.5.3 环境变量管理最佳实践

**多环境配置策略**:

```bash
# 项目结构
.
├── .env.example          # 示例配置(提交到Git)
├── .env.development      # 开发环境(不提交)
├── .env.staging          # 测试环境(不提交)
├── .env.production       # 生产环境(不提交)
├── docker-compose.yml    # 基础配置
├── docker-compose.dev.yml
├── docker-compose.prod.yml
└── .gitignore           # 忽略所有.env文件
```

**.env.example**:

```bash
# 应用配置
NODE_ENV=production
LOG_LEVEL=info
PORT=8080

# 数据库配置
DATABASE_URL=postgresql://user:password@db:5432/dbname
DB_POOL_MIN=2
DB_POOL_MAX=10

# Redis配置
REDIS_URL=redis://redis:6379/0

# 外部服务
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=secret...

# 秘钥(生产环境使用Docker Secrets或Vault)
JWT_SECRET=change_me_in_production
API_KEY=change_me_in_production
```

**.env.development**:

```bash
NODE_ENV=development
LOG_LEVEL=debug
PORT=8080

DATABASE_URL=postgresql://dev:dev123@localhost:5432/dev_db
REDIS_URL=redis://localhost:6379/0

JWT_SECRET=dev_jwt_secret
API_KEY=dev_api_key
```

**.env.production**:

```bash
NODE_ENV=production
LOG_LEVEL=warn
PORT=8080

# 生产环境使用Docker Secrets
DATABASE_URL_FILE=/run/secrets/database_url
REDIS_URL_FILE=/run/secrets/redis_url
JWT_SECRET_FILE=/run/secrets/jwt_secret
API_KEY_FILE=/run/secrets/api_key

# AWS使用IAM角色,无需硬编码密钥
AWS_REGION=us-east-1
```

**优先级规则**:

```python
# config.py - 统一配置加载
import os
from pathlib import Path

def read_secret(name):
    """读取秘钥(支持文件和环境变量)"""
    # 1. 优先从文件读取(Docker Secrets/Vault)
    file_path = os.getenv(f'{name}_FILE')
    if file_path and Path(file_path).exists():
        with open(file_path, 'r') as f:
            return f.read().strip()

    # 2. 从环境变量读取
    value = os.getenv(name)
    if value:
        return value

    # 3. 从.env文件读取(开发环境)
    from dotenv import load_dotenv
    load_dotenv()
    value = os.getenv(name)
    if value:
        return value

    # 4. 抛出异常
    raise ValueError(f'Missing required config: {name}')

class Config:
    """应用配置"""
    # 基础配置
    NODE_ENV = os.getenv('NODE_ENV', 'development')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'info')
    PORT = int(os.getenv('PORT', 8080))

    # 秘钥配置
    DATABASE_URL = read_secret('DATABASE_URL')
    REDIS_URL = read_secret('REDIS_URL')
    JWT_SECRET = read_secret('JWT_SECRET')
    API_KEY = read_secret('API_KEY')

    @classmethod
    def is_production(cls):
        return cls.NODE_ENV == 'production'

    @classmethod
    def is_development(cls):
        return cls.NODE_ENV == 'development'

# 使用
config = Config()
print(f'Running in {config.NODE_ENV} mode')
print(f'Database: {config.DATABASE_URL}')
```

---

## 13.6 生产部署最佳实践

### 13.6.1 部署清单(Checklist)

```yaml
# 生产部署检查清单

## 安全性
- [ ] 所有秘钥使用Docker Secrets或Vault管理
- [ ] 删除默认账号和密码
- [ ] 启用HTTPS和TLS 1.2+
- [ ] 配置防火墙规则
- [ ] 使用非root用户运行容器
- [ ] 扫描镜像漏洞(Trivy/Clair)
- [ ] 限制容器权限(drop capabilities)
- [ ] 配置内部网络隔离

## 高可用性
- [ ] 至少3个Manager节点(Swarm)
- [ ] 跨可用区分布服务副本
- [ ] 配置健康检查和自动重启
- [ ] 实现优雅关闭(SIGTERM处理)
- [ ] 配置资源limits和reservations
- [ ] 数据库主从/集群部署
- [ ] 负载均衡器高可用(HAProxy+Keepalived)

## 数据持久化
- [ ] 数据卷使用NFS/云存储
- [ ] 配置自动备份(每日/每周)
- [ ] 测试备份恢复流程
- [ ] 数据库binlog/WAL归档
- [ ] 重要数据多地域备份

## 监控告警
- [ ] 部署Prometheus+Grafana
- [ ] 配置关键指标告警规则
- [ ] 集成PagerDuty/钉钉/企业微信
- [ ] 日志集中收集(ELK/Loki)
- [ ] APM性能监控
- [ ] 业务指标监控

## 性能优化
- [ ] 容器资源限制优化
- [ ] 数据库连接池配置
- [ ] Redis缓存策略
- [ ] CDN加速静态资源
- [ ] Gzip压缩启用
- [ ] HTTP/2启用
- [ ] 数据库索引优化

## 部署流程
- [ ] 使用声明式部署(Stack)
- [ ] 配置滚动更新策略
- [ ] 设置健康检查探针
- [ ] 实现蓝绿/金丝雀部署
- [ ] 自动化CI/CD流程
- [ ] 版本标签规范(semver)
- [ ] 回滚预案

## 文档和培训
- [ ] 部署架构图
- [ ] 运维手册(SOP)
- [ ] 故障排查手册
- [ ] 应急响应流程
- [ ] 团队培训完成
```

---

### 13.6.2 部署脚本示例

```bash
#!/bin/bash
# deploy.sh - 生产环境部署脚本

set -euo pipefail  # 遇到错误立即退出

# ========================================
# 配置
# ========================================

STACK_NAME="myapp"
ENVIRONMENT="production"
DOCKER_REGISTRY="registry.company.com"
VERSION="${1:-latest}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'  # No Color

# ========================================
# 函数定义
# ========================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found"
        exit 1
    fi

    # 检查Swarm模式
    if ! docker info | grep -q "Swarm: active"; then
        log_error "Docker Swarm is not active"
        exit 1
    fi

    # 检查Manager节点
    MANAGER_COUNT=$(docker node ls --filter "role=manager" --format "{{.ID}}" | wc -l)
    if [ "$MANAGER_COUNT" -lt 3 ]; then
        log_warn "Only $MANAGER_COUNT manager nodes (recommended: 3+)"
    fi

    log_info "✅ Prerequisites check passed"
}

pull_images() {
    log_info "Pulling Docker images..."

    docker pull "${DOCKER_REGISTRY}/${STACK_NAME}:${VERSION}"
    docker pull postgres:15-alpine
    docker pull redis:7-alpine
    docker pull nginx:alpine

    log_info "✅ Images pulled successfully"
}

create_secrets() {
    log_info "Creating Docker secrets..."

    # 检查秘钥是否已存在
    if ! docker secret ls | grep -q "db_password"; then
        echo "$DB_PASSWORD" | docker secret create db_password -
        log_info "Created secret: db_password"
    else
        log_info "Secret already exists: db_password"
    fi

    if ! docker secret ls | grep -q "jwt_secret"; then
        openssl rand -base64 32 | docker secret create jwt_secret -
        log_info "Created secret: jwt_secret"
    else
        log_info "Secret already exists: jwt_secret"
    fi
}

deploy_stack() {
    log_info "Deploying stack: ${STACK_NAME}"

    # 导出环境变量
    export VERSION
    export ENVIRONMENT

    # 部署Stack
    docker stack deploy \
      -c docker-compose.yml \
      -c docker-compose.${ENVIRONMENT}.yml \
      --with-registry-auth \
      ${STACK_NAME}

    log_info "✅ Stack deployed"
}

wait_for_services() {
    log_info "Waiting for services to become healthy..."

    local max_wait=300  # 5分钟超时
    local elapsed=0

    while [ $elapsed -lt $max_wait ]; do
        local total=$(docker stack services ${STACK_NAME} --format "{{.Name}}" | wc -l)
        local ready=$(docker stack services ${STACK_NAME} --format "{{.Name}} {{.Replicas}}" | \
                     grep -E " [0-9]+/\1 " | wc -l)

        if [ "$ready" -eq "$total" ]; then
            log_info "✅ All services are ready ($ready/$total)"
            return 0
        fi

        log_info "Waiting... ($ready/$total services ready)"
        sleep 10
        elapsed=$((elapsed + 10))
    done

    log_error "Timeout waiting for services"
    return 1
}

run_health_check() {
    log_info "Running health checks..."

    # 检查应用健康
    if curl -f -s http://localhost/health > /dev/null; then
        log_info "✅ Application health check passed"
    else
        log_error "Application health check failed"
        return 1
    fi

    # 检查数据库连接
    if docker exec -it $(docker ps -q -f name=${STACK_NAME}_db) \
       pg_isready -U appuser > /dev/null 2>&1; then
        log_info "✅ Database health check passed"
    else
        log_error "Database health check failed"
        return 1
    fi
}

show_deployment_info() {
    log_info "Deployment Information:"
    echo ""
    echo "Stack Name: ${STACK_NAME}"
    echo "Environment: ${ENVIRONMENT}"
    echo "Version: ${VERSION}"
    echo ""
    echo "Services:"
    docker stack services ${STACK_NAME}
    echo ""
    echo "Access URLs:"
    echo "  Application: https://app.example.com"
    echo "  API: https://api.example.com"
    echo "  Monitoring: https://grafana.example.com"
}

cleanup_old_images() {
    log_info "Cleaning up old images..."
    docker image prune -f --filter "until=72h"
    log_info "✅ Cleanup completed"
}

# ========================================
# 主流程
# ========================================

main() {
    log_info "Starting deployment process..."
    log_info "============================================"

    # 1. 前置检查
    check_prerequisites

    # 2. 拉取镜像
    pull_images

    # 3. 创建秘钥
    create_secrets

    # 4. 部署Stack
    deploy_stack

    # 5. 等待服务就绪
    if ! wait_for_services; then
        log_error "Deployment failed"
        log_info "Rolling back..."
        docker stack rm ${STACK_NAME}
        exit 1
    fi

    # 6. 健康检查
    if ! run_health_check; then
        log_error "Health check failed"
        exit 1
    fi

    # 7. 显示部署信息
    show_deployment_info

    # 8. 清理旧镜像
    cleanup_old_images

    log_info "============================================"
    log_info "✅ Deployment completed successfully!"
}

# 执行主流程
main "$@"
```

**使用部署脚本**:

```bash
# 赋予执行权限
$ chmod +x deploy.sh

# 部署指定版本
$ ./deploy.sh v1.2.3

# 部署latest
$ ./deploy.sh

# 输出示例:
[INFO] Starting deployment process...
[INFO] ============================================
[INFO] Checking prerequisites...
[INFO] ✅ Prerequisites check passed
[INFO] Pulling Docker images...
[INFO] ✅ Images pulled successfully
[INFO] Creating Docker secrets...
[INFO] Created secret: db_password
[INFO] ✅ Stack deployed
[INFO] Waiting for services to become healthy...
[INFO] Waiting... (3/5 services ready)
[INFO] Waiting... (4/5 services ready)
[INFO] ✅ All services are ready (5/5)
[INFO] Running health checks...
[INFO] ✅ Application health check passed
[INFO] ✅ Database health check passed
[INFO] Deployment Information:

Stack Name: myapp
Environment: production
Version: v1.2.3

Services:
ID        NAME           MODE        REPLICAS  IMAGE
abc123    myapp_app      replicated  6/6       registry.company.com/myapp:v1.2.3
def456    myapp_db       replicated  1/1       postgres:15-alpine
...

[INFO] ✅ Deployment completed successfully!
```

---

## 13.7 本章总结

**核心要点**:

- ✅ **部署架构**: 根据规模选择单机/Swarm/K8s
- ✅ **服务发现**: Swarm内置DNS + Consul高级特性
- ✅ **负载均衡**: HAProxy(稳定) vs Traefik(现代化)
- ✅ **API网关**: Nginx实现认证、限流、缓存
- ✅ **秘钥管理**: Docker Secrets(简单) vs Vault(企业级)
- ✅ **配置管理**: 环境变量 + 文件 + 优先级规则
- ✅ **部署流程**: 自动化脚本 + 健康检查 + 回滚预案

**架构对比**:

| 特性 | 单机 | Swarm | Kubernetes |
|------|------|-------|-----------|
| 适用规模 | <10容器 | 10-100节点 | 100+节点 |
| 复杂度 | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 高可用 | ❌ | ✅ | ✅ |
| 自动扩缩容 | ❌ | 手动 | ✅ HPA |
| 生态系统 | 基础 | 够用 | 丰富 |

---

---

---

# 第14章:高可用性与灾难恢复

## 14.1 高可用架构设计

### 14.1.1 高可用基本原则

**SLA与可用性级别**:

```bash
# 可用性等级对照表
┌─────────┬─────────────┬─────────────┬──────────────────┐
│  级别   │  可用性%    │ 年停机时间  │      适用场景     │
├─────────┼─────────────┼─────────────┼──────────────────┤
│  99%    │  Two Nines  │  3.65天     │ 内部工具          │
│  99.9%  │  Three 9s   │  8.76小时   │ 一般业务系统      │
│  99.99% │  Four 9s    │  52.56分钟  │ 重要业务系统      │
│  99.999%│  Five 9s    │  5.26分钟   │ 金融、电商核心    │
│ 99.9999%│  Six 9s     │  31.5秒     │ 电信运营商        │
└─────────┴─────────────┴─────────────┴──────────────────┘

# SLA计算公式
可用性% = (总时间 - 停机时间) / 总时间 × 100%

# 示例: 达到99.99%可用性
年允许停机时间 = 365天 × 24小时 × 60分钟 × (1 - 0.9999)
                = 525,600分钟 × 0.0001
                = 52.56分钟/年
                ≈ 4.38分钟/月
```

**高可用设计原则**:

```yaml
# 1. 消除单点故障(SPOF - Single Point of Failure)
原则: 任何组件都不应该成为单点故障
实践:
  - 所有服务至少2个副本
  - 数据库主从/集群部署
  - 负载均衡器双活
  - 存储冗余(RAID/分布式存储)

# 2. 故障检测与自动恢复
原则: 快速检测故障并自动恢复
实践:
  - 健康检查机制(HTTP/TCP探针)
  - 自动重启策略
  - 服务自动注册/注销
  - 熔断器模式

# 3. 冗余与备份
原则: 关键数据和服务多副本
实践:
  - 数据库实时复制
  - 定期备份(全量+增量)
  - 跨可用区部署
  - 异地灾备

# 4. 降级与限流
原则: 保证核心功能可用
实践:
  - 功能降级开关
  - 限流保护
  - 熔断机制
  - 优雅降级

# 5. 监控与告警
原则: 实时监控,快速响应
实践:
  - 全链路监控
  - 实时告警
  - 自动化运维
  - 事件溯源
```

---

### 14.1.2 多层级高可用架构

**完整高可用架构图**:

```bash
# 三层高可用架构
┌──────────────────────────────────────────────────────────┐
│                      DNS层(多地域)                        │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│   │  Route53 US  │  │  Route53 EU  │  │  Route53 AS  │  │
│   │   (主DNS)    │  │   (备DNS)    │  │   (备DNS)    │  │
│   └──────────────┘  └──────────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────────┘
                         │
┌──────────────────────────────────────────────────────────┐
│                  CDN/WAF层(边缘加速)                      │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│   │ CloudFlare 1 │  │ CloudFlare 2 │  │ CloudFlare 3 │  │
│   │   (北美)     │  │   (欧洲)     │  │   (亚太)     │  │
│   └──────────────┘  └──────────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────────┘
                         │
┌──────────────────────────────────────────────────────────┐
│              负载均衡层(跨可用区)                         │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│   │  VIP (AZ-A)  │  │  VIP (AZ-B)  │  │  VIP (AZ-C)  │  │
│   │  HAProxy+    │  │  HAProxy+    │  │  HAProxy+    │  │
│   │  Keepalived  │  │  Keepalived  │  │  Keepalived  │  │
│   └──────────────┘  └──────────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────────┘
                         │
┌──────────────────────────────────────────────────────────┐
│              应用层(Swarm集群)                            │
│   ┌──────────────────────────────────────────────────┐  │
│   │  Manager节点(3个,跨AZ)                           │  │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐          │  │
│   │  │Manager1 │  │Manager2 │  │Manager3 │          │  │
│   │  │  (AZ-A) │  │  (AZ-B) │  │  (AZ-C) │          │  │
│   │  └─────────┘  └─────────┘  └─────────┘          │  │
│   └──────────────────────────────────────────────────┘  │
│   ┌──────────────────────────────────────────────────┐  │
│   │  Worker节点(N个,跨AZ)                            │  │
│   │  ┌────┐┌────┐┌────┐┌────┐┌────┐┌────┐          │  │
│   │  │W-1 ││W-2 ││W-3 ││W-4 ││W-5 ││W-N │  ...     │  │
│   │  │AZ-A││AZ-B││AZ-C││AZ-A││AZ-B││AZ-C│          │  │
│   │  └────┘└────┘└────┘└────┘└────┘└────┘          │  │
│   └──────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                         │
┌──────────────────────────────────────────────────────────┐
│              数据层(主从+集群)                            │
│   ┌──────────────────────────────────────────────────┐  │
│   │  PostgreSQL主从集群                              │  │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐          │  │
│   │  │ Master  │→→│ Slave1  │  │ Slave2  │          │  │
│   │  │  (AZ-A) │  │  (AZ-B) │  │  (AZ-C) │          │  │
│   │  └─────────┘  └─────────┘  └─────────┘          │  │
│   └──────────────────────────────────────────────────┘  │
│   ┌──────────────────────────────────────────────────┐  │
│   │  Redis Sentinel集群                              │  │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐          │  │
│   │  │ Master  │  │Sentinel1│  │Sentinel2│          │  │
│   │  │  (AZ-A) │  │  (AZ-B) │  │  (AZ-C) │          │  │
│   │  └─────────┘  └─────────┘  └─────────┘          │  │
│   └──────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                         │
┌──────────────────────────────────────────────────────────┐
│              存储层(分布式存储)                           │
│   ┌──────────────────────────────────────────────────┐  │
│   │  Ceph/GlusterFS分布式存储                        │  │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐          │  │
│   │  │  OSD 1  │  │  OSD 2  │  │  OSD 3  │  ...    │  │
│   │  │  (AZ-A) │  │  (AZ-B) │  │  (AZ-C) │          │  │
│   │  └─────────┘  └─────────┘  └─────────┘          │  │
│   └──────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

### 14.1.3 跨可用区部署实践

**可用区标签配置**:

```bash
# ========================================
# 为节点打可用区标签
# ========================================

# Manager节点
$ docker node update --label-add zone=us-east-1a manager1
$ docker node update --label-add zone=us-east-1b manager2
$ docker node update --label-add zone=us-east-1c manager3

# Worker节点
$ docker node update --label-add zone=us-east-1a worker1
$ docker node update --label-add zone=us-east-1a worker2
$ docker node update --label-add zone=us-east-1b worker3
$ docker node update --label-add zone=us-east-1b worker4
$ docker node update --label-add zone=us-east-1c worker5
$ docker node update --label-add zone=us-east-1c worker6

# 验证标签
$ docker node ls --format "table {{.Hostname}}\t{{.ManagerStatus}}\t{{.Availability}}"
HOSTNAME    MANAGER STATUS  AVAILABILITY
manager1    Leader          Active
manager2    Reachable       Active
manager3    Reachable       Active
worker1                     Active
worker2                     Active
worker3                     Active

$ docker node inspect manager1 --format '{{.Spec.Labels.zone}}'
us-east-1a
```

**跨可用区服务部署**:

```yaml
# stack-ha.yml - 高可用Stack配置
version: '3.8'

services:
  # ========================================
  # Web应用(跨AZ分布)
  # ========================================
  app:
    image: myapp:latest
    deploy:
      replicas: 9  # 每个AZ至少3个副本
      placement:
        max_replicas_per_node: 2  # 单节点最多2个副本
        constraints:
          - node.role == worker
        preferences:
          - spread: node.labels.zone  # 跨AZ均匀分布
      update_config:
        parallelism: 3  # 每次更新3个副本(每个AZ 1个)
        delay: 10s
        failure_action: rollback
        order: start-first  # 先启动新副本再停止旧副本
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    networks:
      - frontend
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 40s

  # ========================================
  # 数据库(主从复制,跨AZ)
  # ========================================
  db-master:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
      POSTGRES_DB: appdb
      # 主库配置
      POSTGRES_INITDB_ARGS: "-E UTF8 --locale=C"
    secrets:
      - db_password
    volumes:
      - db-master-data:/var/lib/postgresql/data
      - ./postgres/master/postgresql.conf:/etc/postgresql/postgresql.conf
      - ./postgres/master/pg_hba.conf:/etc/postgresql/pg_hba.conf
    networks:
      - backend
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.role == worker
          - node.labels.zone == us-east-1a  # 主库固定在AZ-A
          - node.labels.ssd == true
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appuser"]
      interval: 10s
      timeout: 5s
      retries: 5

  db-slave-1:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
      # 从库配置
      POSTGRES_MASTER_HOST: db-master
      POSTGRES_MASTER_PORT: 5432
    secrets:
      - db_password
    volumes:
      - db-slave-1-data:/var/lib/postgresql/data
      - ./postgres/slave/postgresql.conf:/etc/postgresql/postgresql.conf
      - ./postgres/slave/recovery.conf:/var/lib/postgresql/data/recovery.conf
    networks:
      - backend
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.labels.zone == us-east-1b  # 从库1在AZ-B
          - node.labels.ssd == true
      resources:
        limits:
          cpus: '2'
          memory: 4G
    depends_on:
      - db-master

  db-slave-2:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
      POSTGRES_MASTER_HOST: db-master
      POSTGRES_MASTER_PORT: 5432
    secrets:
      - db_password
    volumes:
      - db-slave-2-data:/var/lib/postgresql/data
      - ./postgres/slave/postgresql.conf:/etc/postgresql/postgresql.conf
      - ./postgres/slave/recovery.conf:/var/lib/postgresql/data/recovery.conf
    networks:
      - backend
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.labels.zone == us-east-1c  # 从库2在AZ-C
          - node.labels.ssd == true
      resources:
        limits:
          cpus: '2'
          memory: 4G
    depends_on:
      - db-master

  # ========================================
  # Redis Sentinel高可用
  # ========================================
  redis-master:
    image: redis:7-alpine
    command: >
      redis-server
      --requirepass ${REDIS_PASSWORD}
      --maxmemory 2gb
      --maxmemory-policy allkeys-lru
      --save 900 1
      --save 300 10
      --appendonly yes
      --replica-announce-ip redis-master
    volumes:
      - redis-master-data:/data
    networks:
      - backend
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.labels.zone == us-east-1a

  redis-sentinel-1:
    image: redis:7-alpine
    command: >
      redis-sentinel /etc/redis/sentinel.conf
      --sentinel announce-ip redis-sentinel-1
    volumes:
      - ./redis/sentinel.conf:/etc/redis/sentinel.conf
    networks:
      - backend
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.labels.zone == us-east-1a

  redis-sentinel-2:
    image: redis:7-alpine
    command: >
      redis-sentinel /etc/redis/sentinel.conf
      --sentinel announce-ip redis-sentinel-2
    volumes:
      - ./redis/sentinel.conf:/etc/redis/sentinel.conf
    networks:
      - backend
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.labels.zone == us-east-1b

  redis-sentinel-3:
    image: redis:7-alpine
    command: >
      redis-sentinel /etc/redis/sentinel.conf
      --sentinel announce-ip redis-sentinel-3
    volumes:
      - ./redis/sentinel.conf:/etc/redis/sentinel.conf
    networks:
      - backend
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.labels.zone == us-east-1c

networks:
  frontend:
    driver: overlay
    attachable: true
  backend:
    driver: overlay
    internal: true
    attachable: true

volumes:
  db-master-data:
    driver: local
    driver_opts:
      type: nfs
      o: addr=nfs-az-a.example.com,rw
      device: ":/export/db-master"

  db-slave-1-data:
    driver: local
    driver_opts:
      type: nfs
      o: addr=nfs-az-b.example.com,rw
      device: ":/export/db-slave-1"

  db-slave-2-data:
    driver: local
    driver_opts:
      type: nfs
      o: addr=nfs-az-c.example.com,rw
      device: ":/export/db-slave-2"

  redis-master-data:
    driver: local

secrets:
  db_password:
    external: true
```

**PostgreSQL主从配置**:

```bash
# postgres/master/postgresql.conf
# 主库配置

# 基本设置
listen_addresses = '*'
port = 5432
max_connections = 200

# WAL配置(Write-Ahead Logging)
wal_level = replica  # 启用流复制
max_wal_senders = 10  # 最多10个从库
wal_keep_size = 1GB   # 保留1GB WAL日志
hot_standby = on      # 启用热备

# 归档配置
archive_mode = on
archive_command = 'test ! -f /archive/%f && cp %p /archive/%f'

# 同步复制(可选,保证数据一致性)
synchronous_commit = on
synchronous_standby_names = 'slave1,slave2'

# 性能调优
shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 512MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 10MB
min_wal_size = 1GB
max_wal_size = 4GB
```

```bash
# postgres/master/pg_hba.conf
# 主库访问控制

# TYPE  DATABASE        USER            ADDRESS                 METHOD

# 本地连接
local   all             all                                     trust

# IPv4本地连接
host    all             all             127.0.0.1/32            md5

# 允许Swarm网络访问
host    all             all             10.0.0.0/8              md5

# 允许从库复制
host    replication     replicator      10.0.0.0/8              md5
```

```bash
# postgres/slave/recovery.conf
# 从库复制配置

# 声明为备库
standby_mode = 'on'

# 主库连接信息
primary_conninfo = 'host=db-master port=5432 user=replicator password=ReplicatorPassword123 application_name=slave1'

# 恢复目标时间线
recovery_target_timeline = 'latest'

# 触发文件(用于手动提升为主库)
trigger_file = '/tmp/postgresql.trigger'

# 归档恢复
restore_command = 'cp /archive/%f %p'
```

**Redis Sentinel配置**:

```bash
# redis/sentinel.conf
# Redis Sentinel配置

# 端口
port 26379

# 工作目录
dir /tmp

# 监控主库
# sentinel monitor <master-name> <ip> <port> <quorum>
sentinel monitor mymaster redis-master 6379 2

# 主库密码
sentinel auth-pass mymaster ${REDIS_PASSWORD}

# 主库多久无响应视为下线(毫秒)
sentinel down-after-milliseconds mymaster 5000

# 故障转移超时时间
sentinel failover-timeout mymaster 60000

# 并行同步的从库数量
sentinel parallel-syncs mymaster 1

# 通知脚本(可选)
# sentinel notification-script mymaster /etc/redis/notify.sh

# 客户端重新配置脚本(可选)
# sentinel client-reconfig-script mymaster /etc/redis/reconfig.sh

# 日志
logfile "/var/log/redis/sentinel.log"
loglevel notice
```

---

## 14.2 故障转移与自动恢复

### 14.2.1 应用层故障转移

**Swarm自动故障转移**:

```bash
# ========================================
# Swarm自动故障转移演示
# ========================================

# 查看服务初始状态
$ docker service ps myapp_app
ID      NAME          NODE     DESIRED STATE  CURRENT STATE
abc123  myapp_app.1   worker1  Running        Running 10 minutes ago
def456  myapp_app.2   worker2  Running        Running 10 minutes ago
ghi789  myapp_app.3   worker3  Running        Running 10 minutes ago

# 模拟worker1节点故障(关机)
$ ssh worker1 "sudo shutdown -h now"

# Swarm自动检测到节点故障
$ docker node ls
ID        HOSTNAME    STATUS   AVAILABILITY  MANAGER STATUS
abc123    manager1    Ready    Active        Leader
...
xyz789    worker1     Down     Active
...

# 服务自动在其他节点重启
$ docker service ps myapp_app
ID      NAME              NODE     DESIRED STATE  CURRENT STATE
abc123  myapp_app.1       worker1  Shutdown       Failed 1 minute ago
jkl012  \_ myapp_app.1    worker4  Running        Running 30 seconds ago  # ✅ 自动迁移
def456  myapp_app.2       worker2  Running        Running 10 minutes ago
ghi789  myapp_app.3       worker3  Running        Running 10 minutes ago

# 节点恢复后,容器不会自动迁移回去(保持稳定)
$ ssh worker1 "sudo systemctl start docker"
$ docker node update --availability active worker1
```

**健康检查与自动重启**:

```yaml
# 完善的健康检查配置
services:
  app:
    image: myapp:latest
    healthcheck:
      # 健康检查命令
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      # 启动宽限期(容器启动后等待40秒再开始检查)
      start_period: 40s
      # 检查间隔
      interval: 10s
      # 超时时间
      timeout: 3s
      # 连续失败3次才视为不健康
      retries: 3
    deploy:
      replicas: 6
      # 更新配置
      update_config:
        # 先启动新容器,健康检查通过后再停止旧容器
        order: start-first
        # 每次更新1个副本
        parallelism: 1
        # 等待10秒
        delay: 10s
        # 失败后自动回滚
        failure_action: rollback
        # 监控窗口60秒
        monitor: 60s
      # 回滚配置
      rollback_config:
        parallelism: 2
        delay: 5s
      # 重启策略
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s
```

**应用层健康检查实现**:

```python
# app.py - Flask应用健康检查
from flask import Flask, jsonify
import psycopg2
import redis
import os

app = Flask(__name__)

# 数据库连接池
db_pool = None
redis_client = None

def check_database():
    """检查数据库连接"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'db-master'),
            port=5432,
            user='appuser',
            password=os.getenv('DB_PASSWORD'),
            connect_timeout=3
        )
        conn.close()
        return True
    except Exception as e:
        print(f"Database check failed: {e}")
        return False

def check_redis():
    """检查Redis连接"""
    try:
        r = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis-master'),
            port=6379,
            password=os.getenv('REDIS_PASSWORD'),
            socket_connect_timeout=3
        )
        r.ping()
        return True
    except Exception as e:
        print(f"Redis check failed: {e}")
        return False

@app.route('/health')
def health():
    """健康检查端点"""
    checks = {
        'status': 'healthy',
        'database': check_database(),
        'redis': check_redis(),
    }

    # 任何依赖失败都返回503
    if not all(checks.values()):
        checks['status'] = 'unhealthy'
        return jsonify(checks), 503

    return jsonify(checks), 200

@app.route('/ready')
def ready():
    """就绪检查端点(Kubernetes用)"""
    # 检查应用是否已完全启动
    # 可以包含更复杂的逻辑,如缓存预热、配置加载等
    return jsonify({'status': 'ready'}), 200

@app.route('/live')
def live():
    """存活检查端点(Kubernetes用)"""
    # 简单检查应用进程是否存活
    return jsonify({'status': 'alive'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

---

### 14.2.2 数据库故障转移

**PostgreSQL自动故障转移(使用Patroni)**:

```yaml
# patroni-stack.yml - PostgreSQL高可用方案
version: '3.8'

services:
  # ========================================
  # etcd集群(Patroni依赖的分布式配置存储)
  # ========================================
  etcd-1:
    image: quay.io/coreos/etcd:v3.5.10
    environment:
      ETCD_NAME: etcd-1
      ETCD_INITIAL_CLUSTER: etcd-1=http://etcd-1:2380,etcd-2=http://etcd-2:2380,etcd-3=http://etcd-3:2380
      ETCD_INITIAL_CLUSTER_STATE: new
      ETCD_INITIAL_CLUSTER_TOKEN: patroni-cluster
      ETCD_LISTEN_PEER_URLS: http://0.0.0.0:2380
      ETCD_LISTEN_CLIENT_URLS: http://0.0.0.0:2379
      ETCD_ADVERTISE_CLIENT_URLS: http://etcd-1:2379
    networks:
      - db-net
    volumes:
      - etcd-1-data:/etcd-data
    deploy:
      placement:
        constraints:
          - node.labels.zone == us-east-1a

  etcd-2:
    image: quay.io/coreos/etcd:v3.5.10
    environment:
      ETCD_NAME: etcd-2
      ETCD_INITIAL_CLUSTER: etcd-1=http://etcd-1:2380,etcd-2=http://etcd-2:2380,etcd-3=http://etcd-3:2380
      ETCD_INITIAL_CLUSTER_STATE: new
      ETCD_INITIAL_CLUSTER_TOKEN: patroni-cluster
      ETCD_LISTEN_PEER_URLS: http://0.0.0.0:2380
      ETCD_LISTEN_CLIENT_URLS: http://0.0.0.0:2379
      ETCD_ADVERTISE_CLIENT_URLS: http://etcd-2:2379
    networks:
      - db-net
    volumes:
      - etcd-2-data:/etcd-data
    deploy:
      placement:
        constraints:
          - node.labels.zone == us-east-1b

  etcd-3:
    image: quay.io/coreos/etcd:v3.5.10
    environment:
      ETCD_NAME: etcd-3
      ETCD_INITIAL_CLUSTER: etcd-1=http://etcd-1:2380,etcd-2=http://etcd-2:2380,etcd-3=http://etcd-3:2380
      ETCD_INITIAL_CLUSTER_STATE: new
      ETCD_INITIAL_CLUSTER_TOKEN: patroni-cluster
      ETCD_LISTEN_PEER_URLS: http://0.0.0.0:2380
      ETCD_LISTEN_CLIENT_URLS: http://0.0.0.0:2379
      ETCD_ADVERTISE_CLIENT_URLS: http://etcd-3:2379
    networks:
      - db-net
    volumes:
      - etcd-3-data:/etcd-data
    deploy:
      placement:
        constraints:
          - node.labels.zone == us-east-1c

  # ========================================
  # Patroni PostgreSQL节点
  # ========================================
  patroni-1:
    image: patroni/patroni:3.2.0
    hostname: patroni-1
    environment:
      PATRONI_NAME: patroni-1
      PATRONI_SCOPE: postgres-cluster
      PATRONI_RESTAPI_LISTEN: 0.0.0.0:8008
      PATRONI_POSTGRESQL_LISTEN: 0.0.0.0:5432
      PATRONI_POSTGRESQL_DATA_DIR: /var/lib/postgresql/data
      PATRONI_ETCD3_HOSTS: etcd-1:2379,etcd-2:2379,etcd-3:2379
      PATRONI_POSTGRESQL_PGPASS: /tmp/pgpass
      PATRONI_SUPERUSER_USERNAME: postgres
      PATRONI_SUPERUSER_PASSWORD: ${POSTGRES_PASSWORD}
      PATRONI_REPLICATION_USERNAME: replicator
      PATRONI_REPLICATION_PASSWORD: ${REPLICATION_PASSWORD}
    volumes:
      - patroni-1-data:/var/lib/postgresql/data
      - ./patroni/patroni.yml:/etc/patroni/patroni.yml
    networks:
      - db-net
    ports:
      - "5432:5432"  # PostgreSQL
      - "8008:8008"  # Patroni REST API
    deploy:
      placement:
        constraints:
          - node.labels.zone == us-east-1a
          - node.labels.ssd == true

  patroni-2:
    image: patroni/patroni:3.2.0
    hostname: patroni-2
    environment:
      PATRONI_NAME: patroni-2
      PATRONI_SCOPE: postgres-cluster
      PATRONI_RESTAPI_LISTEN: 0.0.0.0:8008
      PATRONI_POSTGRESQL_LISTEN: 0.0.0.0:5432
      PATRONI_POSTGRESQL_DATA_DIR: /var/lib/postgresql/data
      PATRONI_ETCD3_HOSTS: etcd-1:2379,etcd-2:2379,etcd-3:2379
      PATRONI_SUPERUSER_USERNAME: postgres
      PATRONI_SUPERUSER_PASSWORD: ${POSTGRES_PASSWORD}
      PATRONI_REPLICATION_USERNAME: replicator
      PATRONI_REPLICATION_PASSWORD: ${REPLICATION_PASSWORD}
    volumes:
      - patroni-2-data:/var/lib/postgresql/data
      - ./patroni/patroni.yml:/etc/patroni/patroni.yml
    networks:
      - db-net
    deploy:
      placement:
        constraints:
          - node.labels.zone == us-east-1b
          - node.labels.ssd == true

  patroni-3:
    image: patroni/patroni:3.2.0
    hostname: patroni-3
    environment:
      PATRONI_NAME: patroni-3
      PATRONI_SCOPE: postgres-cluster
      PATRONI_RESTAPI_LISTEN: 0.0.0.0:8008
      PATRONI_POSTGRESQL_LISTEN: 0.0.0.0:5432
      PATRONI_POSTGRESQL_DATA_DIR: /var/lib/postgresql/data
      PATRONI_ETCD3_HOSTS: etcd-1:2379,etcd-2:2379,etcd-3:2379
      PATRONI_SUPERUSER_USERNAME: postgres
      PATRONI_SUPERUSER_PASSWORD: ${POSTGRES_PASSWORD}
      PATRONI_REPLICATION_USERNAME: replicator
      PATRONI_REPLICATION_PASSWORD: ${REPLICATION_PASSWORD}
    volumes:
      - patroni-3-data:/var/lib/postgresql/data
      - ./patroni/patroni.yml:/etc/patroni/patroni.yml
    networks:
      - db-net
    deploy:
      placement:
        constraints:
          - node.labels.zone == us-east-1c
          - node.labels.ssd == true

  # ========================================
  # HAProxy(数据库负载均衡)
  # ========================================
  haproxy-db:
    image: haproxy:2.9-alpine
    ports:
      - "5433:5432"  # 主库端口
      - "5434:5433"  # 从库端口(读负载均衡)
      - "7000:7000"  # HAProxy统计页面
    volumes:
      - ./haproxy/haproxy-db.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro
    networks:
      - db-net
    deploy:
      mode: global
      placement:
        constraints:
          - node.role == manager

networks:
  db-net:
    driver: overlay
    attachable: true

volumes:
  etcd-1-data:
  etcd-2-data:
  etcd-3-data:
  patroni-1-data:
  patroni-2-data:
  patroni-3-data:
```

**Patroni配置文件**:

```yaml
# patroni/patroni.yml
scope: postgres-cluster
namespace: /service/
name: ${PATRONI_NAME}

restapi:
  listen: 0.0.0.0:8008
  connect_address: ${PATRONI_NAME}:8008

etcd3:
  hosts: etcd-1:2379,etcd-2:2379,etcd-3:2379

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
    postgresql:
      use_pg_rewind: true
      parameters:
        max_connections: 200
        shared_buffers: 2GB
        effective_cache_size: 6GB
        maintenance_work_mem: 512MB
        checkpoint_completion_target: 0.9
        wal_buffers: 16MB
        default_statistics_target: 100
        random_page_cost: 1.1
        effective_io_concurrency: 200
        work_mem: 10MB
        min_wal_size: 1GB
        max_wal_size: 4GB
        max_worker_processes: 8
        max_parallel_workers_per_gather: 4
        max_parallel_workers: 8

  initdb:
    - encoding: UTF8
    - data-checksums

  pg_hba:
    - host replication replicator 0.0.0.0/0 md5
    - host all all 0.0.0.0/0 md5

  users:
    admin:
      password: ${ADMIN_PASSWORD}
      options:
        - createrole
        - createdb

postgresql:
  listen: 0.0.0.0:5432
  connect_address: ${PATRONI_NAME}:5432
  data_dir: /var/lib/postgresql/data
  pgpass: /tmp/pgpass
  authentication:
    replication:
      username: replicator
      password: ${REPLICATION_PASSWORD}
    superuser:
      username: postgres
      password: ${POSTGRES_PASSWORD}
  parameters:
    unix_socket_directories: '/var/run/postgresql'

tags:
    nofailover: false
    noloadbalance: false
    clonefrom: false
    nosync: false
```

**HAProxy数据库负载均衡配置**:

```bash
# haproxy/haproxy-db.cfg
global
    log stdout format raw local0 info
    maxconn 100

defaults
    log global
    mode tcp
    retries 2
    timeout client 30m
    timeout connect 4s
    timeout server 30m
    timeout check 5s

# 统计页面
listen stats
    bind *:7000
    mode http
    stats enable
    stats uri /
    stats refresh 5s

# 主库(写)
listen postgres-master
    bind *:5432
    mode tcp
    option httpchk GET /master
    http-check expect status 200
    default-server inter 3s fall 3 rise 2 on-marked-down shutdown-sessions

    server patroni-1 patroni-1:5432 check port 8008
    server patroni-2 patroni-2:5432 check port 8008
    server patroni-3 patroni-3:5432 check port 8008

# 从库(读,负载均衡)
listen postgres-replicas
    bind *:5433
    mode tcp
    balance roundrobin
    option httpchk GET /replica
    http-check expect status 200
    default-server inter 3s fall 3 rise 2 on-marked-down shutdown-sessions

    server patroni-1 patroni-1:5432 check port 8008
    server patroni-2 patroni-2:5432 check port 8008
    server patroni-3 patroni-3:5432 check port 8008
```

**故障转移测试**:

```bash
# ========================================
# 模拟主库故障
# ========================================

# 查看当前主库
$ curl -s http://patroni-1:8008/patroni | jq .role
"master"

$ curl -s http://patroni-2:8008/patroni | jq .role
"replica"

$ curl -s http://patroni-3:8008/patroni | jq .role
"replica"

# 停止主库容器(模拟故障)
$ docker stop $(docker ps -q -f name=patroni-1)

# Patroni自动检测故障并选举新主库(约15-30秒)
# 查看新主库
$ curl -s http://patroni-2:8008/patroni | jq .role
"master"  # ✅ patroni-2已提升为主库

$ curl -s http://patroni-3:8008/patroni | jq .role
"replica"

# 恢复旧主库
$ docker start $(docker ps -aq -f name=patroni-1)

# 旧主库自动变为从库
$ curl -s http://patroni-1:8008/patroni | jq .role
"replica"  # ✅ patroni-1降级为从库

# 验证数据一致性
$ docker exec -it $(docker ps -q -f name=patroni-2) \
  psql -U postgres -c "SELECT pg_current_wal_lsn();"
 pg_current_wal_lsn
--------------------
 0/5000000

$ docker exec -it $(docker ps -q -f name=patroni-1) \
  psql -U postgres -c "SELECT pg_last_wal_replay_lsn();"
 pg_last_wal_replay_lsn
------------------------
 0/5000000  # ✅ 数据已同步
```

---

### 14.2.3 Redis故障转移(Sentinel)

**Redis Sentinel工作原理**:

```bash
# Redis Sentinel架构
┌────────────────────────────────────────────────┐
│              Redis Sentinel集群                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │ Sentinel 1  │ │ Sentinel 2  │ │ Sentinel 3  ││
│  │   (AZ-A)    │ │   (AZ-B)    │ │   (AZ-C)    ││
│  │ Port: 26379 │ │ Port: 26379 │ │ Port: 26379 ││
│  └─────────────┘ └─────────────┘ └─────────────┘│
│         │               │               │        │
│         └───────────────┼───────────────┘        │
│                         │                        │
└─────────────────────────┼────────────────────────┘
                          │ 监控
┌─────────────────────────┼────────────────────────┐
│                Redis数据节点                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │   Master    │→│   Replica1  │ │   Replica2  ││
│  │   (AZ-A)    │ │   (AZ-B)    │ │   (AZ-C)    ││
│  │ Port: 6379  │ │ Port: 6379  │ │ Port: 6379  ││
│  └─────────────┘ └─────────────┘ └─────────────┘│
└──────────────────────────────────────────────────┘

# 故障转移流程:
1. Sentinel定期PING主库
2. 超过down-after-milliseconds无响应,标记为主观下线(SDOWN)
3. 达到quorum个Sentinel确认,标记为客观下线(ODOWN)
4. Sentinel Leader选举(Raft算法)
5. Leader发起故障转移:
   a. 从所有从库中选出新主库(优先级/复制偏移量/RunID)
   b. 向新主库发送SLAVEOF NO ONE(提升为主库)
   c. 向其他从库发送SLAVEOF <new-master>
   d. 更新配置,通知客户端
```

**应用集成Sentinel**:

```python
# app.py - Python应用使用Redis Sentinel
from redis.sentinel import Sentinel
import os

# Sentinel配置
SENTINEL_HOSTS = [
    ('redis-sentinel-1', 26379),
    ('redis-sentinel-2', 26379),
    ('redis-sentinel-3', 26379)
]
MASTER_NAME = 'mymaster'
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

# 创建Sentinel连接
sentinel = Sentinel(
    SENTINEL_HOSTS,
    socket_timeout=0.5,
    password=REDIS_PASSWORD
)

# 获取主库连接(写操作)
def get_master():
    return sentinel.master_for(
        MASTER_NAME,
        socket_timeout=0.5,
        password=REDIS_PASSWORD,
        db=0
    )

# 获取从库连接(读操作)
def get_slave():
    return sentinel.slave_for(
        MASTER_NAME,
        socket_timeout=0.5,
        password=REDIS_PASSWORD,
        db=0
    )

# 使用示例
def set_value(key, value):
    """写操作(使用主库)"""
    master = get_master()
    master.set(key, value)
    print(f"✅ Set {key}={value} to master")

def get_value(key):
    """读操作(使用从库)"""
    slave = get_slave()
    value = slave.get(key)
    print(f"✅ Get {key}={value} from slave")
    return value

# 测试
if __name__ == '__main__':
    # 写入数据
    set_value('user:1001', 'John Doe')

    # 读取数据
    user = get_value('user:1001')
    print(f"User: {user}")

    # 查看当前主库信息
    master_addr = sentinel.discover_master(MASTER_NAME)
    print(f"Current master: {master_addr}")

    # 查看从库列表
    slaves = sentinel.discover_slaves(MASTER_NAME)
    print(f"Slaves: {slaves}")
```

**故障转移测试**:

```bash
# ========================================
# 测试Redis Sentinel故障转移
# ========================================

# 查看当前主库
$ docker exec redis-sentinel-1 \
  redis-cli -p 26379 sentinel get-master-addr-by-name mymaster
1) "redis-master"
2) "6379"

# 查看主库信息
$ docker exec redis-sentinel-1 \
  redis-cli -p 26379 sentinel master mymaster
name: mymaster
ip: redis-master
port: 6379
runid: abc123...
flags: master
num-slaves: 2
num-other-sentinels: 2

# 模拟主库故障(暂停容器)
$ docker pause $(docker ps -q -f name=redis-master)

# Sentinel检测故障并开始选举(约5-10秒)
$ docker logs -f $(docker ps -q -f name=redis-sentinel-1)
+sdown master mymaster redis-master 6379  # 主观下线
+odown master mymaster redis-master 6379 #quorum 2/2  # 客观下线
+failover-triggered master mymaster redis-master 6379  # 触发故障转移
+failover-state-select-slave master mymaster redis-master 6379  # 选择新主库
+selected-slave slave redis-replica-1:6379 redis-replica-1 6379 @ mymaster redis-master 6379  # 选中replica-1
+failover-state-send-slaveof-noone slave redis-replica-1:6379 redis-replica-1 6379 @ mymaster redis-master 6379  # 提升为主库
+failover-state-reconf-slaves master mymaster redis-master 6379  # 重新配置从库
+slave-reconf-sent slave redis-replica-2:6379 redis-replica-2 6379 @ mymaster redis-master 6379
+failover-end master mymaster redis-master 6379  # 故障转移完成
+switch-master mymaster redis-master 6379 redis-replica-1 6379  # 切换主库

# 验证新主库
$ docker exec redis-sentinel-1 \
  redis-cli -p 26379 sentinel get-master-addr-by-name mymaster
1) "redis-replica-1"  # ✅ 新主库
2) "6379"

# 恢复旧主库
$ docker unpause $(docker ps -q -f name=redis-master)

# 旧主库自动变为从库
$ docker exec $(docker ps -q -f name=redis-master) \
  redis-cli -a ${REDIS_PASSWORD} info replication | grep role
role:slave  # ✅ 已降级为从库
```

---

## 14.3 数据备份策略

### 14.3.1 数据库备份方案

**PostgreSQL完整备份策略**:

```bash
#!/bin/bash
# backup-postgres.sh - PostgreSQL自动备份脚本

set -euo pipefail

# ========================================
# 配置
# ========================================

BACKUP_DIR="/backup/postgres"
DB_HOST="${DB_HOST:-db-master}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-appdb}"
PGPASSWORD="${PGPASSWORD}"

# 备份保留策略
DAILY_RETENTION=7    # 保留7天的每日备份
WEEKLY_RETENTION=4   # 保留4周的每周备份
MONTHLY_RETENTION=12 # 保留12个月的月度备份

DATE=$(date +%Y%m%d)
TIME=$(date +%H%M%S)
BACKUP_TYPE="${1:-full}"  # full/incremental

# ========================================
# 函数定义
# ========================================

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# 全量备份
full_backup() {
    local backup_file="${BACKUP_DIR}/full/pg_dump_${DB_NAME}_${DATE}_${TIME}.sql.gz"

    log "Starting full backup to $backup_file"

    # 创建目录
    mkdir -p "${BACKUP_DIR}/full"

    # 使用pg_dump进行全量备份
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -Fc -Z 9 \
      --verbose --file="${backup_file%.gz}" "$DB_NAME" 2>&1 | \
      tee -a "${BACKUP_DIR}/backup.log"

    # 压缩
    gzip -9 "${backup_file%.gz}"

    # 验证备份
    if [ -f "$backup_file" ]; then
        local size=$(du -h "$backup_file" | cut -f1)
        log "✅ Full backup completed: $backup_file ($size)"

        # 记录备份元数据
        cat > "${backup_file}.meta" <<EOF
Backup Date: $(date)
Database: $DB_NAME
Type: Full
Size: $size
Host: $DB_HOST
EOF
    else
        log "❌ Backup failed!"
        exit 1
    fi
}

# WAL归档备份(增量)
wal_backup() {
    local wal_dir="${BACKUP_DIR}/wal"
    mkdir -p "$wal_dir"

    log "Archiving WAL files to $wal_dir"

    # 触发WAL归档
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "SELECT pg_switch_wal();" "$DB_NAME"

    # 复制WAL文件
    rsync -avz --progress \
      "${DB_HOST}:/var/lib/postgresql/data/pg_wal/" \
      "$wal_dir/" \
      2>&1 | tee -a "${BACKUP_DIR}/backup.log"

    log "✅ WAL backup completed"
}

# 基础备份(PITR - Point-In-Time Recovery)
base_backup() {
    local backup_dir="${BACKUP_DIR}/basebackup/${DATE}"

    log "Starting base backup to $backup_dir"

    mkdir -p "$backup_dir"

    # 使用pg_basebackup
    pg_basebackup -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
      -D "$backup_dir" -Ft -z -Xs -P \
      2>&1 | tee -a "${BACKUP_DIR}/backup.log"

    log "✅ Base backup completed"
}

# 清理旧备份
cleanup_old_backups() {
    log "Cleaning up old backups..."

    # 删除超过保留期的每日备份
    find "${BACKUP_DIR}/full" -name "*.sql.gz" -mtime +${DAILY_RETENTION} -delete

    # 每周备份(保留每周日的备份)
    # TODO: 实现周备份逻辑

    # 每月备份(保留每月1号的备份)
    # TODO: 实现月备份逻辑

    log "✅ Cleanup completed"
}

# 备份到远程存储
upload_to_s3() {
    local backup_file="$1"

    log "Uploading backup to S3..."

    # 使用AWS CLI上传到S3
    aws s3 cp "$backup_file" \
      "s3://my-backup-bucket/postgres/${DATE}/" \
      --storage-class STANDARD_IA \
      2>&1 | tee -a "${BACKUP_DIR}/backup.log"

    log "✅ Upload completed"
}

# ========================================
# 主流程
# ========================================

main() {
    log "========================================="
    log "PostgreSQL Backup Started"
    log "Type: $BACKUP_TYPE"
    log "========================================="

    # 检查数据库连接
    if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; then
        log "❌ Database is not ready!"
        exit 1
    fi

    case "$BACKUP_TYPE" in
        full)
            full_backup
            ;;
        incremental)
            wal_backup
            ;;
        base)
            base_backup
            ;;
        *)
            log "❌ Unknown backup type: $BACKUP_TYPE"
            exit 1
            ;;
    esac

    # 清理旧备份
    cleanup_old_backups

    # 上传到S3(可选)
    if [ -n "${AWS_S3_BUCKET:-}" ]; then
        upload_to_s3 "${BACKUP_DIR}/full/pg_dump_${DB_NAME}_${DATE}_${TIME}.sql.gz"
    fi

    log "========================================="
    log "✅ Backup process completed successfully"
    log "========================================="
}

# 执行
main "$@"
```

**定时备份Cron配置**:

```yaml
# backup-cron-stack.yml
version: '3.8'

services:
  backup-cron:
    image: postgres:15-alpine
    environment:
      DB_HOST: db-master
      DB_PORT: 5432
      DB_USER: postgres
      DB_NAME: appdb
      PGPASSWORD_FILE: /run/secrets/db_password
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
      AWS_S3_BUCKET: my-backup-bucket
    secrets:
      - db_password
    volumes:
      - backup-data:/backup
      - ./scripts/backup-postgres.sh:/scripts/backup-postgres.sh:ro
    networks:
      - backend
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - node.role == manager
    command: >
      sh -c "
        apk add --no-cache aws-cli rsync &&
        chmod +x /scripts/backup-postgres.sh &&
        echo '0 2 * * * /scripts/backup-postgres.sh full >> /backup/cron.log 2>&1' > /etc/crontabs/root &&
        echo '0 */6 * * * /scripts/backup-postgres.sh incremental >> /backup/cron.log 2>&1' >> /etc/crontabs/root &&
        crond -f -l 2
      "

networks:
  backend:
    external: true

volumes:
  backup-data:
    driver: local
    driver_opts:
      type: nfs
      o: addr=backup-nfs.example.com,rw
      device: ":/export/backups"

secrets:
  db_password:
    external: true
```

**数据恢复脚本**:

```bash
#!/bin/bash
# restore-postgres.sh - PostgreSQL恢复脚本

set -euo pipefail

BACKUP_FILE="$1"
DB_HOST="${DB_HOST:-db-master}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-appdb}"
PGPASSWORD="${PGPASSWORD}"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

log "========================================="
log "PostgreSQL Restore Started"
log "Backup file: $BACKUP_FILE"
log "========================================="

# 验证备份文件存在
if [ ! -f "$BACKUP_FILE" ]; then
    log "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

# 停止应用服务(避免连接)
log "Stopping application services..."
docker service scale myapp_app=0

# 删除现有数据库
log "Dropping existing database..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "DROP DATABASE IF EXISTS ${DB_NAME};"

# 创建新数据库
log "Creating new database..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "CREATE DATABASE ${DB_NAME};"

# 恢复备份
log "Restoring backup..."
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --verbose
else
    pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --verbose "$BACKUP_FILE"
fi

# 验证恢复
log "Verifying restore..."
TABLE_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
log "Restored $TABLE_COUNT tables"

# 重启应用服务
log "Restarting application services..."
docker service scale myapp_app=6

log "========================================="
log "✅ Restore completed successfully"
log "========================================="
```

---

### 14.3.2 文件系统备份

**Docker Volume备份**:

```bash
#!/bin/bash
# backup-volumes.sh - Docker Volume备份脚本

set -euo pipefail

VOLUME_NAME="$1"
BACKUP_DIR="/backup/volumes"
DATE=$(date +%Y%m%d)

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 备份Volume
backup_volume() {
    local volume="$1"
    local backup_file="${BACKUP_DIR}/${volume}_${DATE}.tar.gz"

    log "Backing up volume: $volume"

    # 使用临时容器挂载Volume并打包
    docker run --rm \
      -v "${volume}:/data:ro" \
      -v "${BACKUP_DIR}:/backup" \
      alpine \
      tar czf "/backup/$(basename $backup_file)" -C /data .

    if [ -f "$backup_file" ]; then
        local size=$(du -h "$backup_file" | cut -f1)
        log "✅ Volume backup completed: $backup_file ($size)"
    else
        log "❌ Backup failed!"
        exit 1
    fi
}

# 恢复Volume
restore_volume() {
    local volume="$1"
    local backup_file="$2"

    log "Restoring volume: $volume from $backup_file"

    # 创建新Volume(如果不存在)
    docker volume create "$volume"

    # 使用临时容器解压到Volume
    docker run --rm \
      -v "${volume}:/data" \
      -v "$(dirname $backup_file):/backup:ro" \
      alpine \
      tar xzf "/backup/$(basename $backup_file)" -C /data

    log "✅ Volume restored: $volume"
}

# 列出所有Volume
list_volumes() {
    log "Docker Volumes:"
    docker volume ls --format "table {{.Name}}\t{{.Driver}}\t{{.Mountpoint}}"
}

# 主流程
case "${2:-backup}" in
    backup)
        backup_volume "$VOLUME_NAME"
        ;;
    restore)
        restore_volume "$VOLUME_NAME" "$3"
        ;;
    list)
        list_volumes
        ;;
    *)
        echo "Usage: $0 <volume-name> [backup|restore|list] [backup-file]"
        exit 1
        ;;
esac
```

**使用Restic进行增量备份**:

```yaml
# restic-backup-stack.yml
version: '3.8'

services:
  restic-backup:
    image: restic/restic:latest
    environment:
      # Restic仓库配置
      RESTIC_REPOSITORY: s3:s3.amazonaws.com/my-backup-bucket/restic
      RESTIC_PASSWORD_FILE: /run/secrets/restic_password
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
    secrets:
      - restic_password
    volumes:
      # 需要备份的Volume
      - app-data:/data/app:ro
      - db-data:/data/db:ro
      - redis-data:/data/redis:ro
    networks:
      - backend
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - node.role == manager
    command: >
      sh -c "
        # 初始化仓库(仅首次)
        restic snapshots || restic init &&
        # 每天凌晨2点执行备份
        while true; do
          restic backup /data \
            --tag daily \
            --exclude '*.tmp' \
            --exclude '*.log' &&
          restic forget \
            --keep-daily 7 \
            --keep-weekly 4 \
            --keep-monthly 12 \
            --prune &&
          sleep 86400
        done
      "

secrets:
  restic_password:
    external: true

networks:
  backend:
    external: true
```

**Restic备份管理**:

```bash
# ========================================
# Restic常用命令
# ========================================

# 查看所有快照
$ docker exec restic-backup restic snapshots
ID        Time                 Host        Tags        Paths
----------------------------------------------------------------------
abc123    2023-12-04 02:00:01  restic-1    daily       /data
def456    2023-12-05 02:00:01  restic-1    daily       /data
ghi789    2023-12-06 02:00:01  restic-1    daily       /data

# 比较两个快照的差异
$ docker exec restic-backup restic diff abc123 def456
+    /data/app/new-file.txt
M    /data/db/database.db
-    /data/redis/old-cache.rdb

# 恢复特定快照
$ docker exec restic-backup restic restore abc123 \
  --target /restore \
  --path /data/app

# 恢复特定文件
$ docker exec restic-backup restic restore latest \
  --target /restore \
  --include /data/app/config.yaml

# 验证备份完整性
$ docker exec restic-backup restic check

# 查看备份仓库统计
$ docker exec restic-backup restic stats
Total File Count:   12345
Total Size:         10.5 GiB
```

---

## 14.4 灾难恢复演练

### 14.4.1 灾难恢复计划(DRP)

**RTO与RPO定义**:

```bash
# 灾难恢复关键指标
┌───────────────────────────────────────────────────┐
│                                                   │
│  正常运行  →  故障发生  →  检测故障  →  恢复完成  │
│             ↑          ↑            ↑            │
│             │          │            │            │
│          故障时间      │         恢复时间        │
│                     检测时间                      │
│             ←──────────────────────→             │
│                      RTO                         │
│             ←──────────────→                     │
│                  RPO                             │
└───────────────────────────────────────────────────┘

# RTO (Recovery Time Objective) - 恢复时间目标
定义: 从故障发生到系统恢复正常的最大可接受时间
示例:
  - Tier 1: RTO < 5分钟   (关键业务)
  - Tier 2: RTO < 1小时   (重要业务)
  - Tier 3: RTO < 24小时  (一般业务)

# RPO (Recovery Point Objective) - 恢复点目标
定义: 系统可接受的最大数据丢失量
示例:
  - Tier 1: RPO = 0       (实时同步,零数据丢失)
  - Tier 2: RPO < 15分钟  (5分钟一次增量备份)
  - Tier 3: RPO < 24小时  (每日全量备份)
```

**灾难恢复等级**:

```yaml
# 灾难恢复等级划分
Tier 0: 无灾备
  - RTO: 无限制
  - RPO: 最后一次备份
  - 成本: 最低
  - 适用: 非关键系统

Tier 1: 冷备份
  - RTO: 24-72小时
  - RPO: 24小时
  - 方案: 定期离线备份
  - 成本: 低
  - 适用: 内部工具

Tier 2: 温备份
  - RTO: 4-12小时
  - RPO: 1-4小时
  - 方案: 定期在线备份 + 异地存储
  - 成本: 中等
  - 适用: 一般业务系统

Tier 3: 热备份
  - RTO: 1-4小时
  - RPO: 15分钟-1小时
  - 方案: 实时复制 + 异地备机
  - 成本: 较高
  - 适用: 重要业务系统

Tier 4: 双活(主备)
  - RTO: 10-30分钟
  - RPO: 几分钟
  - 方案: 主备数据库 + 自动故障转移
  - 成本: 高
  - 适用: 核心业务

Tier 5: 多活(异地多活)
  - RTO: < 5分钟
  - RPO: 几秒(准实时)
  - 方案: 多数据中心同时提供服务
  - 成本: 非常高
  - 适用: 金融、电商核心
```

---

### 14.4.2 灾难场景演练

**场景1: 单节点故障**:

```bash
# ========================================
# 演练步骤
# ========================================

# 1. 记录初始状态
$ docker service ps myapp_app
ID      NAME          NODE     DESIRED STATE  CURRENT STATE
abc123  myapp_app.1   worker1  Running        Running 1 hour ago
def456  myapp_app.2   worker2  Running        Running 1 hour ago
ghi789  myapp_app.3   worker3  Running        Running 1 hour ago

# 2. 模拟worker1节点故障
$ ssh worker1 "sudo systemctl stop docker"

# 3. 观察Swarm自动恢复
$ watch -n 1 'docker service ps myapp_app'
# 约30秒后,容器自动在worker4启动

# 4. 验证服务可用性
$ for i in {1..100}; do
    curl -s http://app.example.com/health || echo "FAIL"
  done | grep -c FAIL
0  # ✅ 无失败请求

# 5. 检查数据一致性
$ curl http://app.example.com/api/users/count
{"count": 10000}  # ✅ 数据无丢失

# 6. 恢复节点
$ ssh worker1 "sudo systemctl start docker"

# 7. 记录恢复时间
RTO实际: 约35秒
RPO实际: 0(无数据丢失)
```

**场景2: 数据库主库故障**:

```bash
# ========================================
# 演练步骤
# ========================================

# 1. 记录当前主库
$ curl http://patroni-1:8008/patroni | jq .role
"master"

# 2. 记录最后一笔交易
$ psql -h db-master -U postgres -d appdb -c \
  "SELECT MAX(id) FROM transactions;"
 max
-------
 100000

# 3. 模拟主库故障
$ docker stop patroni-1

# 4. 观察自动故障转移
$ watch -n 1 'curl -s http://patroni-2:8008/patroni | jq .role'
# 约15秒后变为"master"

# 5. 验证数据一致性
$ psql -h patroni-2 -U postgres -d appdb -c \
  "SELECT MAX(id) FROM transactions;"
 max
-------
 100000  # ✅ 数据一致

# 6. 验证应用仍可写入
$ curl -X POST http://app.example.com/api/transactions \
  -d '{"amount": 100}'
{"id": 100001, "status": "success"}  # ✅ 写入成功

# 7. 恢复旧主库
$ docker start patroni-1

# 8. 验证旧主库降级为从库
$ curl -s http://patroni-1:8008/patroni | jq .role
"replica"  # ✅ 已降级

# 9. 记录恢复时间
检测时间: 约5秒
故障转移时间: 约15秒
RTO实际: 约20秒
RPO实际: 0(同步复制,无数据丢失)
```

**场景3: 可用区故障(AZ-A完全不可用)**:

```bash
# ========================================
# 演练步骤
# ========================================

# 1. 记录AZ-A的资源
$ docker node ls --filter "node.labels.zone=us-east-1a"
ID        HOSTNAME    STATUS  AVAILABILITY
abc123    manager1    Ready   Active
def456    worker1     Ready   Active
ghi789    worker2     Ready   Active

# 2. 模拟AZ-A完全故障(网络隔离)
$ for node in manager1 worker1 worker2; do
    ssh $node "sudo iptables -A INPUT -j DROP"
    ssh $node "sudo iptables -A OUTPUT -j DROP"
  done

# 3. 观察Manager Leader切换
$ docker node ls
ID        HOSTNAME    STATUS   AVAILABILITY  MANAGER STATUS
abc123    manager1    Unknown  Active        Unreachable
xyz789    manager2    Ready    Active        Leader  # ✅ 新Leader
...

# 4. 观察服务自动重新调度
$ docker service ps myapp_app
# AZ-A的容器全部迁移到AZ-B和AZ-C

# 5. 验证数据库主库状态
# 如果主库在AZ-A,Patroni会自动选举AZ-B或AZ-C的从库为主库

# 6. 验证服务可用性
$ for i in {1..1000}; do
    curl -s -o /dev/null -w "%{http_code}\n" http://app.example.com/
  done | grep -v 200 | wc -l
5  # ✅ 仅5个请求失败(0.5%错误率)

# 7. 恢复AZ-A
$ for node in manager1 worker1 worker2; do
    ssh $node "sudo iptables -F"
  done

# 8. 记录恢复时间
检测时间: 约10秒
服务迁移时间: 约60秒
RTO实际: 约70秒
RPO实际: 0(数据库主从同步)
受影响请求: 5/1000 (0.5%)
```

**场景4: 完整灾难恢复(从备份恢复)**:

```bash
# ========================================
# 演练步骤
# ========================================

# 1. 模拟灾难(删除所有数据)
$ docker stack rm myapp
$ docker volume rm postgres-data redis-data

# 2. 从最新备份恢复
LATEST_BACKUP=$(ls -t /backup/postgres/full/*.sql.gz | head -1)
echo "Restoring from: $LATEST_BACKUP"

# 3. 重新部署基础设施
$ docker stack deploy -c stack.yml myapp

# 4. 等待数据库就绪
$ docker exec -it $(docker ps -q -f name=myapp_db) \
  pg_isready -U appuser
/var/run/postgresql:5432 - accepting connections

# 5. 恢复数据库
$ ./restore-postgres.sh "$LATEST_BACKUP"

# 6. 恢复Redis数据
$ docker run --rm \
  -v redis-data:/data \
  -v /backup/redis:/backup:ro \
  redis:7-alpine \
  sh -c "redis-cli --rdb /backup/dump.rdb > /data/dump.rdb"

# 7. 验证数据完整性
$ psql -h db-master -U postgres -d appdb -c \
  "SELECT COUNT(*) FROM users;"
 count
--------
 10000  # ✅ 数据恢复成功

# 8. 重启应用服务
$ docker service scale myapp_app=6

# 9. 验证服务可用
$ curl http://app.example.com/health
{"status": "healthy"}  # ✅ 服务正常

# 10. 记录恢复时间
基础设施部署: 约5分钟
数据库恢复: 约10分钟
服务启动: 约2分钟
RTO实际: 约17分钟
RPO实际: 约6小时(最后一次备份)
```

---

## 14.5 本章总结

**核心要点**:

- ✅ **高可用原则**: 消除SPOF、自动恢复、跨AZ部署、降级限流
- ✅ **故障转移**: Swarm自动调度、Patroni数据库HA、Redis Sentinel
- ✅ **备份策略**: 全量+增量、定期+实时、本地+异地、自动化备份
- ✅ **灾难恢复**: RTO/RPO目标、定期演练、自动化恢复、多级容灾

**高可用检查清单**:

```yaml
应用层:
  - [x] 服务至少3个副本
  - [x] 跨可用区分布
  - [x] 健康检查配置
  - [x] 自动重启策略
  - [x] 滚动更新配置

负载均衡层:
  - [x] HAProxy/Traefik高可用
  - [x] Keepalived VIP漂移
  - [x] 健康检查探针
  - [x] 会话保持(如需要)

数据库层:
  - [x] 主从复制/Patroni集群
  - [x] 自动故障转移
  - [x] 数据同步复制
  - [x] 定期备份
  - [x] PITR能力

存储层:
  - [x] 分布式存储(NFS/Ceph)
  - [x] 数据冗余(RAID/副本)
  - [x] 快照备份
  - [x] 异地备份

监控告警:
  - [x] 全链路监控
  - [x] 实时告警
  - [x] 故障自愈
  - [x] 事件溯源
```

**SLA达成策略**:

| 目标SLA | 架构要求 | 备份策略 | 预计成本 |
|---------|---------|---------|---------|
| 99.9%   | 单AZ,主从 | 每日备份 | 基准 |
| 99.99%  | 跨AZ,集群 | 每小时备份 | 2-3x |
| 99.999% | 多数据中心 | 实时同步 | 5-10x |

---

📝 **下一章预告**: Prometheus监控部署、Grafana可视化、AlertManager告警、APM性能监控

---

*（第14章完成,约2100行。已完成14章,剩余5章...）*

---

# 第十五章: 监控告警体系

> **本章目标**: 掌握Docker生产环境完整监控方案,包括Prometheus+Grafana+AlertManager的企业级部署、自定义告警规则设计、分布式追踪系统集成,以及APM性能监控实践。

---

## 15.1 监控体系架构设计

### 15.1.1 监控层次模型

**完整监控金字塔**:

```yaml
┌─────────────────────────────────────────────┐
│         业务监控 (Business Metrics)          │  ← 核心业务指标
│  - 订单成功率、用户活跃度、转化率            │
├─────────────────────────────────────────────┤
│         应用监控 (Application Metrics)       │  ← APM、慢查询、异常
│  - QPS、延迟、错误率、调用链                │
├─────────────────────────────────────────────┤
│         中间件监控 (Middleware Metrics)      │  ← Redis、MySQL、MQ
│  - 连接数、缓存命中率、队列深度              │
├─────────────────────────────────────────────┤
│         容器监控 (Container Metrics)         │  ← Docker运行时
│  - CPU、内存、网络IO、磁盘IO                │
├─────────────────────────────────────────────┤
│         主机监控 (Host Metrics)              │  ← 操作系统层
│  - 系统负载、磁盘空间、网卡流量              │
└─────────────────────────────────────────────┘
```

**监控数据流架构**:

```yaml
[应用服务] ──metrics──> [Prometheus Exporter]
    │                          │
    │                          ├──> [Prometheus Server] ──> [Grafana]
    │                          │           │
    │                          │           └──> [AlertManager] ──> [钉钉/邮件/PagerDuty]
    │                          │
    ├──traces──> [Jaeger Collector] ──> [Jaeger Query UI]
    │
    └──logs────> [Fluentd] ──> [Elasticsearch] ──> [Kibana]

[Grafana] ←──查询──┐
                   ├── [Prometheus]
                   ├── [Jaeger]
                   └── [Elasticsearch]
```

### 15.1.2 监控指标分类(四大黄金信号)

**Google SRE四大黄金信号**:

| 信号类型 | 指标名称 | 采集方式 | 告警阈值示例 |
|---------|---------|---------|-------------|
| **Latency(延迟)** | http_request_duration_seconds | Histogram | P95 > 1s |
| **Traffic(流量)** | http_requests_total | Counter | QPS < 100(流量骤降) |
| **Errors(错误率)** | http_requests_failed_total | Counter | 错误率 > 1% |
| **Saturation(饱和度)** | container_memory_usage_percent | Gauge | 内存 > 80% |

**实际案例: Web服务监控指标**:

```python
# app.py - 应用埋点示例
from prometheus_client import Counter, Histogram, Gauge
import time

# 1. Traffic: 请求总数
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# 2. Latency: 请求延迟分布
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]  # 自定义分位桶
)

# 3. Errors: 错误计数
http_requests_failed_total = Counter(
    'http_requests_failed_total',
    'Total failed HTTP requests',
    ['method', 'endpoint', 'error_type']
)

# 4. Saturation: 当前并发连接数
active_connections = Gauge(
    'active_connections',
    'Number of active connections'
)

# 业务指标
order_total = Counter('order_total', 'Total orders', ['status'])
order_amount = Histogram('order_amount', 'Order amount distribution')

@app.route('/api/order', methods=['POST'])
def create_order():
    start_time = time.time()
    active_connections.inc()

    try:
        # 业务逻辑
        order = process_order(request.json)

        # 记录指标
        order_total.labels(status='success').inc()
        order_amount.observe(order['amount'])
        http_requests_total.labels(
            method='POST',
            endpoint='/api/order',
            status='200'
        ).inc()

        return jsonify(order), 200

    except Exception as e:
        http_requests_failed_total.labels(
            method='POST',
            endpoint='/api/order',
            error_type=type(e).__name__
        ).inc()
        http_requests_total.labels(
            method='POST',
            endpoint='/api/order',
            status='500'
        ).inc()
        raise

    finally:
        # 记录延迟
        duration = time.time() - start_time
        http_request_duration_seconds.labels(
            method='POST',
            endpoint='/api/order'
        ).observe(duration)
        active_connections.dec()
```

---

## 15.2 Prometheus完整部署

### 15.2.1 Prometheus高可用架构

**生产环境架构图**:

```yaml
                    ┌─────────────────┐
                    │   Grafana       │
                    │   (读取数据)     │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    ┌─────▼─────┐      ┌─────▼─────┐      ┌─────▼─────┐
    │Prometheus1│      │Prometheus2│      │Prometheus3│
    │  (主)     │      │  (主)     │      │  (主)     │
    └─────┬─────┘      └─────┬─────┘      └─────┬─────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Thanos Sidecar │ ← 长期存储方案
                    │  (对象存储)      │
                    └─────────────────┘
                             │
                    ┌────────▼────────┐
                    │   S3/MinIO      │
                    │  (历史数据)      │
                    └─────────────────┘

特点:
- 多个Prometheus并行抓取(避免单点)
- Thanos提供全局视图和长期存储
- 数据保留策略: 本地15天 + 对象存储永久
```

### 15.2.2 Prometheus Stack部署

**目录结构**:

```bash
monitoring/
├── prometheus/
│   ├── prometheus.yml          # 主配置
│   ├── rules/
│   │   ├── alerts.yml         # 告警规则
│   │   ├── recording.yml      # 预聚合规则
│   │   └── docker.yml         # Docker专用规则
│   └── targets/
│       ├── nodes.yml          # 节点发现
│       └── containers.yml     # 容器发现
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/       # 数据源配置
│   │   └── dashboards/        # 看板配置
│   └── dashboards/
│       ├── docker.json
│       ├── postgres.json
│       └── app.json
├── alertmanager/
│   └── alertmanager.yml       # 告警路由配置
└── stack.yml                  # Docker Compose配置
```

**1. Prometheus主配置文件**:

```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s          # 默认抓取间隔
  scrape_timeout: 10s
  evaluation_interval: 15s      # 规则评估间隔

  external_labels:
    cluster: 'docker-swarm-prod'
    region: 'us-west-2'
    environment: 'production'

# 告警管理器配置
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093
      timeout: 10s
      api_version: v2

# 加载告警规则
rule_files:
  - '/etc/prometheus/rules/*.yml'

# 抓取配置
scrape_configs:
  # ========================================
  # 1. Prometheus自身监控
  # ========================================
  - job_name: 'prometheus'
    static_configs:
      - targets:
          - localhost:9090
        labels:
          service: 'prometheus'

  # ========================================
  # 2. Node Exporter(主机监控)
  # ========================================
  - job_name: 'node-exporter'
    file_sd_configs:
      - files:
          - '/etc/prometheus/targets/nodes.yml'
        refresh_interval: 30s
    relabel_configs:
      # 从__meta_标签提取实例名
      - source_labels: [__meta_instance]
        target_label: instance
      - source_labels: [__meta_datacenter]
        target_label: datacenter

  # ========================================
  # 3. cAdvisor(容器监控)
  # ========================================
  - job_name: 'cadvisor'
    dns_sd_configs:
      - names:
          - 'tasks.cadvisor'  # Swarm服务发现
        type: 'A'
        port: 8080
        refresh_interval: 30s
    relabel_configs:
      # 仅保留Docker容器指标
      - source_labels: [container_label_com_docker_swarm_service_name]
        action: keep
        regex: .+
      # 添加服务名标签
      - source_labels: [container_label_com_docker_swarm_service_name]
        target_label: service
      - source_labels: [container_label_com_docker_swarm_task_name]
        target_label: task

  # ========================================
  # 4. Docker Engine Metrics
  # ========================================
  - job_name: 'docker-engine'
    static_configs:
      - targets:
          - 'node1:9323'
          - 'node2:9323'
          - 'node3:9323'
    metrics_path: '/metrics'

  # ========================================
  # 5. PostgreSQL Exporter
  # ========================================
  - job_name: 'postgres'
    static_configs:
      - targets:
          - 'postgres-exporter:9187'
        labels:
          database: 'appdb'
          role: 'master'

  # ========================================
  # 6. Redis Exporter
  # ========================================
  - job_name: 'redis'
    static_configs:
      - targets:
          - 'redis-exporter:9121'
        labels:
          cache: 'main'

  # ========================================
  # 7. 应用自定义指标
  # ========================================
  - job_name: 'app-metrics'
    dns_sd_configs:
      - names:
          - 'tasks.myapp'
        type: 'A'
        port: 8000
        refresh_interval: 15s
    metrics_path: '/metrics'
    relabel_configs:
      - source_labels: [__meta_dockerswarm_service_label_app]
        target_label: app
      - source_labels: [__meta_dockerswarm_service_label_version]
        target_label: version

  # ========================================
  # 8. Blackbox Exporter(黑盒探测)
  # ========================================
  - job_name: 'blackbox-http'
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - https://api.example.com/health
          - https://app.example.com
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115

  # ========================================
  # 9. NGINX Exporter
  # ========================================
  - job_name: 'nginx'
    static_configs:
      - targets:
          - 'nginx-exporter:9113'
        labels:
          proxy: 'main'

# 存储配置
storage:
  tsdb:
    path: /prometheus
    retention:
      time: 15d              # 本地保留15天
      size: 50GB             # 最大磁盘用量
    wal_compression: true    # WAL压缩(节省30%空间)

# 远程写入(可选,用于长期存储)
remote_write:
  - url: http://thanos-receiver:19291/api/v1/receive
    queue_config:
      max_samples_per_send: 10000
      batch_send_deadline: 10s
      max_retries: 3
```

**2. 节点发现配置**:

```yaml
# prometheus/targets/nodes.yml
- targets:
    - '192.168.1.10:9100'
  labels:
    instance: 'swarm-manager-1'
    datacenter: 'dc1'
    zone: 'us-west-2a'

- targets:
    - '192.168.1.11:9100'
  labels:
    instance: 'swarm-manager-2'
    datacenter: 'dc1'
    zone: 'us-west-2b'

- targets:
    - '192.168.1.12:9100'
  labels:
    instance: 'swarm-manager-3'
    datacenter: 'dc1'
    zone: 'us-west-2c'

- targets:
    - '192.168.1.21:9100'
    - '192.168.1.22:9100'
    - '192.168.1.23:9100'
  labels:
    datacenter: 'dc1'
    role: 'worker'
```

**3. Docker Compose Stack配置**:

```yaml
# monitoring/stack.yml
version: '3.8'

services:
  # ========================================
  # Prometheus Server
  # ========================================
  prometheus:
    image: prom/prometheus:v2.47.0
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=15d'
      - '--storage.tsdb.retention.size=50GB'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
      - '--web.enable-lifecycle'              # 允许热重载
      - '--web.enable-admin-api'              # 启用管理API
      - '--query.max-concurrency=50'          # 最大并发查询
      - '--query.timeout=2m'                  # 查询超时
    volumes:
      - prometheus-data:/prometheus
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./prometheus/rules:/etc/prometheus/rules:ro
      - ./prometheus/targets:/etc/prometheus/targets:ro
    networks:
      - monitoring
    ports:
      - "9090:9090"
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - node.role == manager
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:9090/-/healthy"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # ========================================
  # AlertManager
  # ========================================
  alertmanager:
    image: prom/alertmanager:v0.26.0
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
      - '--cluster.advertise-address=0.0.0.0:9093'
      - '--web.external-url=http://alertmanager.example.com'
    volumes:
      - alertmanager-data:/alertmanager
      - ./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
    networks:
      - monitoring
    ports:
      - "9093:9093"
    deploy:
      mode: replicated
      replicas: 3  # 高可用部署
      placement:
        max_replicas_per_node: 1
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  # ========================================
  # Node Exporter(每个节点)
  # ========================================
  node-exporter:
    image: prom/node-exporter:v1.6.1
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--path.rootfs=/rootfs'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
      - '--collector.netclass.ignored-devices=^(veth.*|br-.*|docker.*)$$'
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    networks:
      - monitoring
    ports:
      - "9100:9100"
    deploy:
      mode: global  # 每个节点一个实例
      resources:
        limits:
          cpus: '0.2'
          memory: 128M

  # ========================================
  # cAdvisor(容器监控)
  # ========================================
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.47.0
    command:
      - '--docker_only=true'
      - '--housekeeping_interval=30s'
      - '--disable_metrics=disk,network,tcp,udp,percpu,sched,process'
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker:/var/lib/docker:ro
      - /dev/disk:/dev/disk:ro
    networks:
      - monitoring
    ports:
      - "8080:8080"
    deploy:
      mode: global
      resources:
        limits:
          cpus: '0.3'
          memory: 256M

  # ========================================
  # Postgres Exporter
  # ========================================
  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:v0.13.2
    environment:
      DATA_SOURCE_NAME: "postgresql://exporter:${POSTGRES_EXPORTER_PASSWORD}@postgres:5432/appdb?sslmode=disable"
    networks:
      - monitoring
      - backend
    deploy:
      mode: replicated
      replicas: 1

  # ========================================
  # Redis Exporter
  # ========================================
  redis-exporter:
    image: oliver006/redis_exporter:v1.52.0
    environment:
      REDIS_ADDR: "redis:6379"
      REDIS_PASSWORD: "${REDIS_PASSWORD}"
    networks:
      - monitoring
      - backend
    deploy:
      mode: replicated
      replicas: 1

  # ========================================
  # Blackbox Exporter(探测)
  # ========================================
  blackbox-exporter:
    image: prom/blackbox-exporter:v0.24.0
    volumes:
      - ./blackbox/blackbox.yml:/etc/blackbox/blackbox.yml:ro
    networks:
      - monitoring
    ports:
      - "9115:9115"
    deploy:
      mode: replicated
      replicas: 2

networks:
  monitoring:
    driver: overlay
    attachable: true
  backend:
    external: true

volumes:
  prometheus-data:
  alertmanager-data:
```

**4. 启用Docker Engine Metrics**:

```bash
# /etc/docker/daemon.json - 所有节点
{
  "metrics-addr": "0.0.0.0:9323",
  "experimental": true
}

# 重启Docker
$ sudo systemctl restart docker

# 验证
$ curl http://localhost:9323/metrics | grep engine_daemon
# engine_daemon_container_actions_seconds_count{action="start"} 1234
```

### 15.2.3 告警规则配置

**1. Docker容器告警规则**:

```yaml
# prometheus/rules/docker.yml
groups:
  - name: docker_containers
    interval: 30s
    rules:
      # ========================================
      # 容器状态告警
      # ========================================
      - alert: ContainerDown
        expr: |
          up{job="cadvisor"} == 0
        for: 1m
        labels:
          severity: critical
          category: availability
        annotations:
          summary: "容器 {{ $labels.instance }} 已下线"
          description: "容器 {{ $labels.container_label_com_docker_swarm_service_name }} 在节点 {{ $labels.instance }} 上无法访问超过1分钟"

      - alert: ContainerRestarting
        expr: |
          rate(container_last_seen{name!=""}[5m]) > 0
        for: 5m
        labels:
          severity: warning
          category: stability
        annotations:
          summary: "容器频繁重启"
          description: "容器 {{ $labels.name }} 在过去5分钟内重启了 {{ $value | humanize }} 次"

      # ========================================
      # CPU告警
      # ========================================
      - alert: ContainerCpuUsageHigh
        expr: |
          (sum(rate(container_cpu_usage_seconds_total{name!=""}[5m])) by (name, instance)
          /
          sum(container_spec_cpu_quota{name!=""}/container_spec_cpu_period{name!=""}) by (name, instance))
          * 100 > 80
        for: 10m
        labels:
          severity: warning
          category: performance
        annotations:
          summary: "容器CPU使用率过高"
          description: "容器 {{ $labels.name }} 在节点 {{ $labels.instance }} 上CPU使用率为 {{ $value | humanizePercentage }},已持续10分钟"

      - alert: ContainerCpuThrottling
        expr: |
          rate(container_cpu_cfs_throttled_seconds_total{name!=""}[5m]) > 0.3
        for: 5m
        labels:
          severity: warning
          category: performance
        annotations:
          summary: "容器CPU被限流"
          description: "容器 {{ $labels.name }} CPU被限流时间占比 {{ $value | humanizePercentage }},建议增加CPU配额"

      # ========================================
      # 内存告警
      # ========================================
      - alert: ContainerMemoryUsageHigh
        expr: |
          (container_memory_usage_bytes{name!=""}
          /
          container_spec_memory_limit_bytes{name!=""})
          * 100 > 85
        for: 5m
        labels:
          severity: warning
          category: performance
        annotations:
          summary: "容器内存使用率过高"
          description: "容器 {{ $labels.name }} 内存使用率为 {{ $value | humanizePercentage }}"

      - alert: ContainerMemoryOOM
        expr: |
          container_memory_failcnt{name!=""} > 0
        for: 1m
        labels:
          severity: critical
          category: availability
        annotations:
          summary: "容器发生OOM"
          description: "容器 {{ $labels.name }} 发生内存溢出,failcnt={{ $value }}"

      # ========================================
      # 网络告警
      # ========================================
      - alert: ContainerNetworkReceiveErrors
        expr: |
          rate(container_network_receive_errors_total{name!=""}[5m]) > 100
        for: 5m
        labels:
          severity: warning
          category: network
        annotations:
          summary: "容器网络接收错误率高"
          description: "容器 {{ $labels.name }} 网络接收错误率 {{ $value | humanize }} errors/s"

      # ========================================
      # 磁盘告警
      # ========================================
      - alert: ContainerDiskUsageHigh
        expr: |
          (container_fs_usage_bytes{name!=""}
          /
          container_fs_limit_bytes{name!=""})
          * 100 > 85
        for: 10m
        labels:
          severity: warning
          category: storage
        annotations:
          summary: "容器磁盘使用率过高"
          description: "容器 {{ $labels.name }} 磁盘使用率 {{ $value | humanizePercentage }}"

  # ========================================
  # Swarm集群告警
  # ========================================
  - name: docker_swarm
    interval: 60s
    rules:
      - alert: SwarmNodeDown
        expr: |
          swarm_node_status{state="ready"} == 0
        for: 2m
        labels:
          severity: critical
          category: infrastructure
        annotations:
          summary: "Swarm节点下线"
          description: "节点 {{ $labels.node_name }} 状态异常"

      - alert: SwarmManagerQuorumLost
        expr: |
          count(swarm_manager_is_leader) < 2
        for: 1m
        labels:
          severity: critical
          category: infrastructure
        annotations:
          summary: "Swarm Manager仲裁丢失"
          description: "当前仅有 {{ $value }} 个Manager节点,集群无法正常工作"

      - alert: SwarmServiceReplicasDown
        expr: |
          (swarm_service_replicas_desired - swarm_service_replicas_running) > 0
        for: 5m
        labels:
          severity: warning
          category: availability
        annotations:
          summary: "服务副本数不足"
          description: "服务 {{ $labels.service_name }} 期望副本数 {{ $labels.desired }},实际运行 {{ $labels.running }}"
```

**2. 主机监控告警规则**:

```yaml
# prometheus/rules/alerts.yml
groups:
  - name: host_alerts
    interval: 30s
    rules:
      # CPU告警
      - alert: HostCpuUsageHigh
        expr: |
          100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "主机CPU使用率过高"
          description: "主机 {{ $labels.instance }} CPU使用率 {{ $value | humanizePercentage }}"

      # 内存告警
      - alert: HostMemoryUsageHigh
        expr: |
          (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 90
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "主机内存使用率过高"
          description: "主机 {{ $labels.instance }} 内存使用率 {{ $value | humanizePercentage }}"

      # 磁盘空间告警
      - alert: HostDiskSpaceLow
        expr: |
          (node_filesystem_avail_bytes{fstype=~"ext4|xfs"}
          /
          node_filesystem_size_bytes{fstype=~"ext4|xfs"})
          * 100 < 15
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "主机磁盘空间不足"
          description: "主机 {{ $labels.instance }} 挂载点 {{ $labels.mountpoint }} 剩余空间仅 {{ $value | humanizePercentage }}"

      # 磁盘IO告警
      - alert: HostDiskIOUtilizationHigh
        expr: |
          rate(node_disk_io_time_seconds_total[5m]) * 100 > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "主机磁盘IO利用率高"
          description: "主机 {{ $labels.instance }} 磁盘 {{ $labels.device }} IO利用率 {{ $value | humanizePercentage }}"

      # 网络带宽告警(假设千兆网卡)
      - alert: HostNetworkBandwidthSaturated
        expr: |
          rate(node_network_receive_bytes_total{device!~"lo|veth.*|br-.*"}[5m]) * 8 / 1000000000 > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "主机网络带宽接近饱和"
          description: "主机 {{ $labels.instance }} 网卡 {{ $labels.device }} 接收带宽 {{ $value | humanize }} Gbps"
```

**3. 应用层告警规则**:

```yaml
# prometheus/rules/app.yml
groups:
  - name: application_alerts
    interval: 15s
    rules:
      # ========================================
      # 四大黄金信号
      # ========================================

      # 1. Latency: 延迟告警
      - alert: ApiLatencyHigh
        expr: |
          histogram_quantile(0.95,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint)
          ) > 1
        for: 5m
        labels:
          severity: warning
          category: performance
        annotations:
          summary: "API延迟过高"
          description: "接口 {{ $labels.endpoint }} P95延迟为 {{ $value | humanizeDuration }}"

      # 2. Traffic: 流量异常
      - alert: ApiTrafficDrop
        expr: |
          (rate(http_requests_total[5m])
          /
          rate(http_requests_total[5m] offset 1h)) < 0.5
        for: 10m
        labels:
          severity: warning
          category: business
        annotations:
          summary: "API流量骤降"
          description: "接口 {{ $labels.endpoint }} 流量相比1小时前下降 {{ $value | humanizePercentage }}"

      # 3. Errors: 错误率告警
      - alert: ApiErrorRateHigh
        expr: |
          (sum(rate(http_requests_total{status=~"5.."}[5m])) by (endpoint)
          /
          sum(rate(http_requests_total[5m])) by (endpoint))
          * 100 > 1
        for: 5m
        labels:
          severity: critical
          category: availability
        annotations:
          summary: "API错误率过高"
          description: "接口 {{ $labels.endpoint }} 5xx错误率 {{ $value | humanizePercentage }}"

      # 4. Saturation: 饱和度告警
      - alert: ApiConcurrencyHigh
        expr: |
          active_connections > 1000
        for: 5m
        labels:
          severity: warning
          category: performance
        annotations:
          summary: "API并发连接数过高"
          description: "当前并发连接数 {{ $value }},接近系统上限"

      # ========================================
      # 数据库告警
      # ========================================
      - alert: PostgresConnectionPoolExhausted
        expr: |
          (pg_stat_database_numbackends / pg_settings_max_connections) * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "PostgreSQL连接池接近耗尽"
          description: "数据库 {{ $labels.datname }} 连接使用率 {{ $value | humanizePercentage }}"

      - alert: PostgresSlowQueries
        expr: |
          rate(pg_stat_statements_mean_time_seconds[5m]) > 1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "PostgreSQL慢查询增多"
          description: "平均查询时间 {{ $value | humanizeDuration }}"

      # ========================================
      # Redis告警
      # ========================================
      - alert: RedisCacheHitRateLow
        expr: |
          (redis_keyspace_hits_total / (redis_keyspace_hits_total + redis_keyspace_misses_total)) * 100 < 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Redis缓存命中率低"
          description: "当前命中率 {{ $value | humanizePercentage }},建议检查缓存策略"

      - alert: RedisMemoryUsageHigh
        expr: |
          (redis_memory_used_bytes / redis_memory_max_bytes) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Redis内存使用率过高"
          description: "内存使用率 {{ $value | humanizePercentage }}"
```

**4. Recording Rules(预聚合规则)**:

```yaml
# prometheus/rules/recording.yml
groups:
  - name: recording_rules
    interval: 30s
    rules:
      # 预聚合常用查询(提高查询性能)

      # 容器CPU使用率(按服务聚合)
      - record: service:container_cpu_usage:rate5m
        expr: |
          sum(rate(container_cpu_usage_seconds_total{name!=""}[5m])) by (
            container_label_com_docker_swarm_service_name
          )

      # 容器内存使用率(按服务聚合)
      - record: service:container_memory_usage:percent
        expr: |
          sum(container_memory_usage_bytes{name!=""}) by (
            container_label_com_docker_swarm_service_name
          )
          /
          sum(container_spec_memory_limit_bytes{name!=""}) by (
            container_label_com_docker_swarm_service_name
          )
          * 100

      # API请求QPS(按endpoint聚合)
      - record: endpoint:http_requests:rate1m
        expr: |
          sum(rate(http_requests_total[1m])) by (endpoint, method)

      # API P95延迟(按endpoint聚合)
      - record: endpoint:http_request_duration:p95
        expr: |
          histogram_quantile(0.95,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint)
          )

      # API错误率(按endpoint聚合)
      - record: endpoint:http_errors:rate5m
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m])) by (endpoint)
          /
          sum(rate(http_requests_total[5m])) by (endpoint)
```

### 15.2.4 部署与验证

```bash
# ========================================
# 1. 准备配置文件
# ========================================
$ cd monitoring

# 验证Prometheus配置语法
$ docker run --rm \
  -v $(pwd)/prometheus:/etc/prometheus \
  prom/prometheus:v2.47.0 \
  promtool check config /etc/prometheus/prometheus.yml
# ✅ SUCCESS: /etc/prometheus/prometheus.yml is valid prometheus config file syntax

# 验证告警规则语法
$ docker run --rm \
  -v $(pwd)/prometheus:/etc/prometheus \
  prom/prometheus:v2.47.0 \
  promtool check rules /etc/prometheus/rules/*.yml
# ✅ SUCCESS: 45 rules found

# ========================================
# 2. 部署Stack
# ========================================
$ docker stack deploy -c stack.yml monitoring

# 查看服务状态
$ docker stack services monitoring
ID         NAME                      MODE      REPLICAS   IMAGE
abc123     monitoring_prometheus     replicated   1/1     prom/prometheus:v2.47.0
def456     monitoring_alertmanager   replicated   3/3     prom/alertmanager:v0.26.0
ghi789     monitoring_node-exporter  global       6/6     prom/node-exporter:v1.6.1
jkl012     monitoring_cadvisor       global       6/6     gcr.io/cadvisor/cadvisor:v0.47.0

# ========================================
# 3. 访问Prometheus UI
# ========================================
$ open http://prometheus.example.com:9090

# 验证Target状态
# 访问: http://prometheus.example.com:9090/targets
# 确认所有Target状态为UP

# ========================================
# 4. 测试PromQL查询
# ========================================

# 查询容器CPU使用率TOP 10
$ curl -G 'http://localhost:9090/api/v1/query' \
  --data-urlencode 'query=topk(10, service:container_cpu_usage:rate5m)'

# 查询API错误率
$ curl -G 'http://localhost:9090/api/v1/query' \
  --data-urlencode 'query=endpoint:http_errors:rate5m > 0.01'

# ========================================
# 5. 热重载配置(无需重启)
# ========================================
$ curl -X POST http://localhost:9090/-/reload
# ✅ 配置已重载

# ========================================
# 6. 验证告警规则
# ========================================
$ curl http://localhost:9090/api/v1/rules | jq '.data.groups[] | .name'
"docker_containers"
"docker_swarm"
"host_alerts"
"application_alerts"

# 查看当前触发的告警
$ curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.state=="firing")'
```

---

## 15.3 Grafana可视化看板

### 15.3.1 Grafana部署与配置

**1. Grafana Stack配置**:

```yaml
# monitoring/stack.yml (添加到现有配置)
services:
  grafana:
    image: grafana/grafana:10.1.0
    environment:
      # 基础配置
      GF_SERVER_ROOT_URL: "http://grafana.example.com"
      GF_SERVER_DOMAIN: "grafana.example.com"

      # 安全配置
      GF_SECURITY_ADMIN_USER: "admin"
      GF_SECURITY_ADMIN_PASSWORD__FILE: /run/secrets/grafana_admin_password
      GF_SECURITY_SECRET_KEY__FILE: /run/secrets/grafana_secret_key

      # 数据库配置(使用PostgreSQL而非默认SQLite)
      GF_DATABASE_TYPE: postgres
      GF_DATABASE_HOST: postgres:5432
      GF_DATABASE_NAME: grafana
      GF_DATABASE_USER: grafana
      GF_DATABASE_PASSWORD__FILE: /run/secrets/grafana_db_password

      # 用户认证
      GF_AUTH_ANONYMOUS_ENABLED: "false"
      GF_AUTH_BASIC_ENABLED: "true"
      GF_AUTH_DISABLE_LOGIN_FORM: "false"

      # SMTP邮件告警(可选)
      GF_SMTP_ENABLED: "true"
      GF_SMTP_HOST: "smtp.example.com:587"
      GF_SMTP_USER: "alerts@example.com"
      GF_SMTP_PASSWORD__FILE: /run/secrets/smtp_password
      GF_SMTP_FROM_ADDRESS: "alerts@example.com"
      GF_SMTP_FROM_NAME: "Grafana Alerts"

      # 性能优化
      GF_DATAPROXY_TIMEOUT: "300"
      GF_DATAPROXY_MAX_IDLE_CONNS: "100"

    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - ./grafana/dashboards:/var/lib/grafana/dashboards:ro
    secrets:
      - grafana_admin_password
      - grafana_db_password
      - grafana_secret_key
      - smtp_password
    networks:
      - monitoring
      - backend
    ports:
      - "3000:3000"
    deploy:
      mode: replicated
      replicas: 2  # 高可用部署
      placement:
        max_replicas_per_node: 1
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
      restart_policy:
        condition: on-failure
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

secrets:
  grafana_admin_password:
    external: true
  grafana_db_password:
    external: true
  grafana_secret_key:
    external: true
  smtp_password:
    external: true

volumes:
  grafana-data:
```

**2. 创建Secrets**:

```bash
# 创建Grafana管理员密码
$ echo "YourStrongPassword123!" | docker secret create grafana_admin_password -

# 创建数据库密码
$ echo "GrafanaDBPass456" | docker secret create grafana_db_password -

# 创建密钥(用于Cookie加密)
$ openssl rand -base64 32 | docker secret create grafana_secret_key -

# 创建SMTP密码
$ echo "smtp-password" | docker secret create smtp_password -
```

**3. 数据源自动配置**:

```yaml
# grafana/provisioning/datasources/prometheus.yml
apiVersion: 1

datasources:
  # Prometheus主数据源
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
    jsonData:
      timeInterval: "30s"
      queryTimeout: "300s"
      httpMethod: POST  # 使用POST发送长查询
      customQueryParameters: ""
      manageAlerts: true
      prometheusType: Prometheus
      prometheusVersion: 2.47.0
      cacheLevel: 'High'
      incrementalQuerying: true
      incrementalQueryOverlapWindow: "10m"
      disableRecordingRules: false

  # Alertmanager数据源
  - name: Alertmanager
    type: alertmanager
    access: proxy
    url: http://alertmanager:9093
    editable: false
    jsonData:
      implementation: prometheus
```

**4. 看板自动加载配置**:

```yaml
# grafana/provisioning/dashboards/default.yml
apiVersion: 1

providers:
  - name: 'Default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
      foldersFromFilesStructure: true
```

### 15.3.2 生产级Dashboard设计

**1. Docker Swarm集群监控面板**:

```json
{
  "dashboard": {
    "title": "Docker Swarm Cluster Overview",
    "tags": ["docker", "swarm", "infrastructure"],
    "timezone": "browser",
    "refresh": "30s",
    "time": {
      "from": "now-6h",
      "to": "now"
    },
    "panels": [
      {
        "id": 1,
        "title": "集群健康状态",
        "type": "stat",
        "targets": [
          {
            "expr": "count(swarm_node_status{state=\"ready\"})",
            "legendFormat": "在线节点"
          },
          {
            "expr": "count(swarm_node_status) - count(swarm_node_status{state=\"ready\"})",
            "legendFormat": "离线节点"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": 0, "color": "red"},
                {"value": 3, "color": "green"}
              ]
            },
            "unit": "short"
          }
        },
        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "服务运行状态",
        "type": "stat",
        "targets": [
          {
            "expr": "count(swarm_service_replicas_running == swarm_service_replicas_desired)",
            "legendFormat": "健康服务"
          },
          {
            "expr": "count(swarm_service_replicas_running != swarm_service_replicas_desired)",
            "legendFormat": "异常服务"
          }
        ],
        "gridPos": {"h": 4, "w": 6, "x": 6, "y": 0}
      },
      {
        "id": 3,
        "title": "集群CPU使用率",
        "type": "graph",
        "targets": [
          {
            "expr": "100 - (avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "平均CPU使用率"
          },
          {
            "expr": "100 - (rate(node_cpu_seconds_total{mode=\"idle\"}[5m]) * 100)",
            "legendFormat": "{{ instance }}"
          }
        ],
        "yaxes": [
          {"format": "percent", "max": 100, "min": 0}
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 4}
      },
      {
        "id": 4,
        "title": "集群内存使用率",
        "type": "graph",
        "targets": [
          {
            "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
            "legendFormat": "{{ instance }}"
          }
        ],
        "yaxes": [
          {"format": "percent", "max": 100, "min": 0}
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 4}
      },
      {
        "id": 5,
        "title": "容器运行数量",
        "type": "graph",
        "targets": [
          {
            "expr": "count(container_last_seen{name!=\"\"}) by (instance)",
            "legendFormat": "{{ instance }}"
          }
        ],
        "gridPos": {"h": 6, "w": 8, "x": 0, "y": 12}
      },
      {
        "id": 6,
        "title": "网络流量",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(container_network_receive_bytes_total[5m])) by (instance)",
            "legendFormat": "{{ instance }} 接收"
          },
          {
            "expr": "sum(rate(container_network_transmit_bytes_total[5m])) by (instance) * -1",
            "legendFormat": "{{ instance }} 发送"
          }
        ],
        "yaxes": [
          {"format": "Bps"}
        ],
        "gridPos": {"h": 6, "w": 8, "x": 8, "y": 12}
      },
      {
        "id": 7,
        "title": "磁盘IO",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(node_disk_read_bytes_total[5m])) by (instance)",
            "legendFormat": "{{ instance }} 读"
          },
          {
            "expr": "sum(rate(node_disk_written_bytes_total[5m])) by (instance) * -1",
            "legendFormat": "{{ instance }} 写"
          }
        ],
        "yaxes": [
          {"format": "Bps"}
        ],
        "gridPos": {"h": 6, "w": 8, "x": 16, "y": 12}
      }
    ]
  }
}
```

**将上述JSON保存为**: `grafana/dashboards/docker-swarm.json`

**2. 应用性能监控面板(APM)**:

```json
{
  "dashboard": {
    "title": "Application Performance Monitoring",
    "tags": ["apm", "application", "performance"],
    "panels": [
      {
        "id": 1,
        "title": "请求速率(QPS)",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[1m])) by (endpoint)",
            "legendFormat": "{{ endpoint }}"
          }
        ],
        "yaxes": [{"format": "reqps"}],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "请求延迟分布",
        "type": "heatmap",
        "targets": [
          {
            "expr": "sum(rate(http_request_duration_seconds_bucket[5m])) by (le)",
            "format": "heatmap",
            "legendFormat": "{{ le }}"
          }
        ],
        "dataFormat": "tsbuckets",
        "yAxis": {"format": "s"},
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "错误率(%)",
        "type": "graph",
        "targets": [
          {
            "expr": "(sum(rate(http_requests_total{status=~\"5..\"}[5m])) by (endpoint) / sum(rate(http_requests_total[5m])) by (endpoint)) * 100",
            "legendFormat": "{{ endpoint }}"
          }
        ],
        "alert": {
          "conditions": [
            {
              "evaluator": {"params": [1], "type": "gt"},
              "operator": {"type": "and"},
              "query": {"params": ["A", "5m", "now"]},
              "reducer": {"params": [], "type": "avg"},
              "type": "query"
            }
          ],
          "executionErrorState": "alerting",
          "frequency": "60s",
          "handler": 1,
          "name": "API错误率告警",
          "noDataState": "no_data",
          "notifications": [
            {"uid": "alertmanager"}
          ]
        },
        "yaxes": [{"format": "percent"}],
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 8}
      },
      {
        "id": 4,
        "title": "P95/P99延迟",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))",
            "legendFormat": "P95 - {{ endpoint }}"
          },
          {
            "expr": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))",
            "legendFormat": "P99 - {{ endpoint }}"
          }
        ],
        "yaxes": [{"format": "s"}],
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 8}
      },
      {
        "id": 5,
        "title": "并发连接数",
        "type": "graph",
        "targets": [
          {
            "expr": "active_connections",
            "legendFormat": "当前连接"
          }
        ],
        "gridPos": {"h": 6, "w": 8, "x": 0, "y": 14}
      },
      {
        "id": 6,
        "title": "数据库连接池",
        "type": "graph",
        "targets": [
          {
            "expr": "pg_stat_database_numbackends",
            "legendFormat": "{{ datname }}"
          },
          {
            "expr": "pg_settings_max_connections",
            "legendFormat": "最大连接数"
          }
        ],
        "gridPos": {"h": 6, "w": 8, "x": 8, "y": 14}
      },
      {
        "id": 7,
        "title": "Redis命中率",
        "type": "stat",
        "targets": [
          {
            "expr": "(redis_keyspace_hits_total / (redis_keyspace_hits_total + redis_keyspace_misses_total)) * 100"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                {"value": 0, "color": "red"},
                {"value": 80, "color": "yellow"},
                {"value": 95, "color": "green"}
              ]
            },
            "unit": "percent"
          }
        },
        "gridPos": {"h": 6, "w": 8, "x": 16, "y": 14}
      }
    ]
  }
}
```

**保存为**: `grafana/dashboards/apm.json`

**3. 导入社区优质Dashboard**:

```bash
# 推荐的社区Dashboard ID列表:

# Docker & Container监控
- 893   # Docker & System Monitoring
- 179   # Docker Prometheus Monitoring
- 10619 # Docker Swarm & Container Overview

# Node Exporter主机监控
- 1860  # Node Exporter Full
- 11074 # Node Exporter for Prometheus Dashboard

# PostgreSQL监控
- 9628  # PostgreSQL Database
- 12485 # PostgreSQL Patroni

# Redis监控
- 11835 # Redis Dashboard for Prometheus
- 2751  # Prometheus Redis

# Nginx监控
- 12708 # Nginx Prometheus Exporter
```

**导入方式**:

```bash
# 方法1: Grafana UI导入
# 访问: http://grafana.example.com
# Dashboard → Import → 输入ID → Load

# 方法2: API导入
$ curl -X POST http://admin:password@grafana.example.com/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard": {
      "id": null,
      "uid": null,
      "title": "Node Exporter Full"
    },
    "inputs": [
      {
        "name": "DS_PROMETHEUS",
        "type": "datasource",
        "pluginId": "prometheus",
        "value": "Prometheus"
      }
    ],
    "overwrite": true,
    "folderId": 0
  }'
```

### 15.3.3 告警通知配置

**Grafana原生告警(Unified Alerting)**:

```yaml
# grafana/provisioning/alerting/contact-points.yml
apiVersion: 1

contactPoints:
  # 钉钉通知
  - orgId: 1
    name: dingtalk
    receivers:
      - uid: dingtalk-webhook
        type: webhook
        settings:
          url: https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN
          httpMethod: POST
          maxAlerts: 10
        disableResolveMessage: false

  # 邮件通知
  - orgId: 1
    name: email
    receivers:
      - uid: email-ops
        type: email
        settings:
          addresses: ops-team@example.com
          singleEmail: false
        disableResolveMessage: false

  # Slack通知
  - orgId: 1
    name: slack
    receivers:
      - uid: slack-alerts
        type: slack
        settings:
          url: https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
          recipient: '#alerts'
          username: Grafana
        disableResolveMessage: false

  # PagerDuty(生产事故)
  - orgId: 1
    name: pagerduty
    receivers:
      - uid: pagerduty-critical
        type: pagerduty
        settings:
          integrationKey: YOUR_PAGERDUTY_KEY
          severity: critical
        disableResolveMessage: false
```

```yaml
# grafana/provisioning/alerting/notification-policies.yml
apiVersion: 1

policies:
  - orgId: 1
    receiver: dingtalk  # 默认接收者
    group_by: ['alertname', 'severity']
    group_wait: 30s
    group_interval: 5m
    repeat_interval: 4h
    routes:
      # Critical告警 → PagerDuty + 钉钉
      - receiver: pagerduty
        continue: true
        matchers:
          - severity = critical
        group_wait: 10s
        repeat_interval: 1h

      # 数据库告警 → 专门的DBA团队
      - receiver: email-dba
        matchers:
          - category = database
        group_interval: 10m

      # 业务告警 → 业务团队
      - receiver: slack-business
        matchers:
          - category = business
        group_interval: 15m
```

---

## 15.4 AlertManager告警路由

### 15.4.1 AlertManager配置

```yaml
# alertmanager/alertmanager.yml
global:
  # SMTP配置
  smtp_smarthost: 'smtp.example.com:587'
  smtp_from: 'alertmanager@example.com'
  smtp_auth_username: 'alertmanager@example.com'
  smtp_auth_password: 'smtp-password'
  smtp_require_tls: true

  # Slack全局配置
  slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'

  # 钉钉Webhook
  http_config:
    proxy_url: ''

# 路由树
route:
  receiver: 'default-receiver'
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 30s        # 分组等待时间(收集同组告警)
  group_interval: 5m     # 分组发送间隔
  repeat_interval: 4h    # 重复告警间隔

  # 子路由
  routes:
    # ========================================
    # 1. Critical告警 → 立即通知多个渠道
    # ========================================
    - receiver: 'critical-alerts'
      continue: true  # 继续匹配其他路由
      matchers:
        - severity = critical
      group_wait: 10s
      group_interval: 5m
      repeat_interval: 30m

    # ========================================
    # 2. 基础设施告警 → 运维团队
    # ========================================
    - receiver: 'infra-team'
      matchers:
        - category = infrastructure
      group_by: ['alertname', 'instance']
      group_interval: 10m

    # ========================================
    # 3. 数据库告警 → DBA团队
    # ========================================
    - receiver: 'dba-team'
      matchers:
        - category = database
      group_by: ['alertname', 'instance', 'datname']

    # ========================================
    # 4. 应用告警 → 开发团队
    # ========================================
    - receiver: 'dev-team'
      matchers:
        - category =~ "performance|availability"
      group_by: ['alertname', 'service', 'endpoint']

    # ========================================
    # 5. 工作时间外的非Critical告警 → 抑制
    # ========================================
    - receiver: 'null'  # 黑洞接收者
      matchers:
        - severity != critical
      time_intervals:
        - offhours

    # ========================================
    # 6. 测试环境告警 → 单独渠道
    # ========================================
    - receiver: 'test-env'
      matchers:
        - environment = test
      group_interval: 1h
      repeat_interval: 24h

# 接收者配置
receivers:
  # ========================================
  # 默认接收者(钉钉)
  # ========================================
  - name: 'default-receiver'
    webhook_configs:
      - url: 'http://dingtalk-webhook:8060/dingtalk/webhook1/send'
        send_resolved: true
        http_config:
          proxy_url: ''

  # ========================================
  # Critical告警(多渠道通知)
  # ========================================
  - name: 'critical-alerts'
    # 钉钉(带@所有人)
    webhook_configs:
      - url: 'http://dingtalk-webhook:8060/dingtalk/webhook-critical/send'
        send_resolved: true

    # 邮件
    email_configs:
      - to: 'ops-oncall@example.com,cto@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.example.com:587'
        auth_username: 'alertmanager@example.com'
        auth_password: 'smtp-password'
        headers:
          Subject: '🚨 [CRITICAL] {{ .GroupLabels.alertname }}'
        html: |
          <!DOCTYPE html>
          <html>
          <body>
            <h2 style="color: red;">🚨 严重告警</h2>
            <table border="1" cellpadding="5">
              <tr><th>告警名称</th><td>{{ .GroupLabels.alertname }}</td></tr>
              <tr><th>严重级别</th><td>{{ .GroupLabels.severity }}</td></tr>
              <tr><th>触发时间</th><td>{{ .StartsAt.Format "2006-01-02 15:04:05" }}</td></tr>
              <tr><th>告警数量</th><td>{{ len .Alerts }}</td></tr>
            </table>
            <h3>详细信息:</h3>
            <ul>
            {{ range .Alerts }}
              <li>
                <strong>{{ .Labels.alertname }}</strong><br>
                {{ .Annotations.summary }}<br>
                <em>{{ .Annotations.description }}</em>
              </li>
            {{ end }}
            </ul>
            <a href="{{ .ExternalURL }}">查看AlertManager</a>
          </body>
          </html>
        send_resolved: true

    # Slack
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#critical-alerts'
        username: 'AlertManager'
        color: 'danger'
        title: '🚨 CRITICAL ALERT'
        text: |
          *Alert:* {{ .GroupLabels.alertname }}
          *Severity:* {{ .GroupLabels.severity }}
          *Summary:* {{ range .Alerts }}{{ .Annotations.summary }}{{ end }}
        send_resolved: true

    # PagerDuty(仅Critical)
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_SERVICE_KEY'
        description: '{{ .GroupLabels.alertname }}: {{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
        severity: 'critical'
        details:
          firing: '{{ .Alerts.Firing | len }}'
          resolved: '{{ .Alerts.Resolved | len }}'

  # ========================================
  # 运维团队
  # ========================================
  - name: 'infra-team'
    webhook_configs:
      - url: 'http://dingtalk-webhook:8060/dingtalk/infra/send'
        send_resolved: true
    email_configs:
      - to: 'infra-team@example.com'
        html: '{{ template "email.html" . }}'

  # ========================================
  # DBA团队
  # ========================================
  - name: 'dba-team'
    webhook_configs:
      - url: 'http://dingtalk-webhook:8060/dingtalk/dba/send'
        send_resolved: true
    email_configs:
      - to: 'dba-team@example.com'
        html: '{{ template "email.html" . }}'

  # ========================================
  # 开发团队
  # ========================================
  - name: 'dev-team'
    slack_configs:
      - channel: '#dev-alerts'
        title: '⚠️ Application Alert'
        text: |
          *Service:* {{ .GroupLabels.service }}
          *Endpoint:* {{ .GroupLabels.endpoint }}
          {{ range .Alerts }}
          • {{ .Annotations.summary }}
          {{ end }}
        send_resolved: true

  # ========================================
  # 测试环境
  # ========================================
  - name: 'test-env'
    webhook_configs:
      - url: 'http://dingtalk-webhook:8060/dingtalk/test/send'
        send_resolved: false  # 测试环境不发送恢复通知

  # ========================================
  # 黑洞接收者(抑制告警)
  # ========================================
  - name: 'null'

# 抑制规则
inhibit_rules:
  # ========================================
  # 1. 节点Down时,抑制该节点上的所有容器告警
  # ========================================
  - source_matchers:
      - alertname = HostDown
    target_matchers:
      - alertname = ContainerDown
    equal:
      - instance

  # ========================================
  # 2. 服务Down时,抑制该服务的性能告警
  # ========================================
  - source_matchers:
      - severity = critical
      - alertname = ServiceDown
    target_matchers:
      - severity = warning
      - category = performance
    equal:
      - service

  # ========================================
  # 3. 数据库主库故障时,抑制从库告警
  # ========================================
  - source_matchers:
      - alertname = PostgresMasterDown
    target_matchers:
      - alertname =~ "Postgres.*"
      - role = slave
    equal:
      - cluster

# 时间段定义
time_intervals:
  # 工作时间外(晚上22:00 - 早上08:00, 周末全天)
  - name: offhours
    time_intervals:
      - times:
          - start_time: '22:00'
            end_time: '08:00'
      - weekdays: ['saturday', 'sunday']

  # 仅工作时间
  - name: workhours
    time_intervals:
      - times:
          - start_time: '09:00'
            end_time: '18:00'
        weekdays: ['monday:friday']

# 模板
templates:
  - '/etc/alertmanager/templates/*.tmpl'
```

### 15.4.2 钉钉Webhook集成

**使用Prometheus Webhook Dingtalk**:

```yaml
# monitoring/stack.yml (添加到现有配置)
services:
  dingtalk-webhook:
    image: timonwong/prometheus-webhook-dingtalk:v2.1.0
    command:
      - '--config.file=/etc/prometheus-webhook-dingtalk/config.yml'
      - '--web.listen-address=:8060'
      - '--web.enable-ui'
      - '--web.enable-lifecycle'
    volumes:
      - ./dingtalk/config.yml:/etc/prometheus-webhook-dingtalk/config.yml:ro
      - ./dingtalk/templates:/etc/prometheus-webhook-dingtalk/templates:ro
    networks:
      - monitoring
    ports:
      - "8060:8060"
    deploy:
      mode: replicated
      replicas: 2
```

```yaml
# dingtalk/config.yml
templates:
  - /etc/prometheus-webhook-dingtalk/templates/default.tmpl

targets:
  # 默认Webhook(普通告警)
  webhook1:
    url: https://oapi.dingtalk.com/robot/send?access_token=YOUR_ACCESS_TOKEN_1
    secret: YOUR_SECRET_1  # 钉钉机器人密钥
    mention:
      all: false

  # Critical告警Webhook(@所有人)
  webhook-critical:
    url: https://oapi.dingtalk.com/robot/send?access_token=YOUR_ACCESS_TOKEN_2
    secret: YOUR_SECRET_2
    mention:
      all: true  # @所有人

  # 基础设施团队
  infra:
    url: https://oapi.dingtalk.com/robot/send?access_token=YOUR_ACCESS_TOKEN_3
    secret: YOUR_SECRET_3
    mention:
      mobiles: ['13800138000', '13900139000']  # @指定人

  # DBA团队
  dba:
    url: https://oapi.dingtalk.com/robot/send?access_token=YOUR_ACCESS_TOKEN_4
    secret: YOUR_SECRET_4
    mention:
      mobiles: ['13700137000']

  # 测试环境
  test:
    url: https://oapi.dingtalk.com/robot/send?access_token=YOUR_ACCESS_TOKEN_5
    secret: YOUR_SECRET_5
    mention:
      all: false
```

**自定义钉钉消息模板**:

```go
// dingtalk/templates/default.tmpl
{{ define "__subject" }}
[{{ .Status | toUpper }}{{ if eq .Status "firing" }}:{{ .Alerts.Firing | len }}{{ end }}] {{ .GroupLabels.SortedPairs.Values | join " " }}
{{ end }}

{{ define "__alert_list" }}
{{ range . }}
---
**告警名称**: {{ .Labels.alertname }}
**严重级别**: {{ .Labels.severity }}
**告警主机**: {{ .Labels.instance }}
{{ if .Labels.service }}**服务名称**: {{ .Labels.service }}{{ end }}
{{ if .Labels.endpoint }}**接口路径**: {{ .Labels.endpoint }}{{ end }}
**告警摘要**: {{ .Annotations.summary }}
**详细描述**: {{ .Annotations.description }}
**触发时间**: {{ (.StartsAt.Add 28800e9).Format "2006-01-02 15:04:05" }}
{{ if gt (len .Labels) 0 }}**所有标签**:
{{ range .Labels.SortedPairs }}  - {{ .Name }}: {{ .Value }}
{{ end }}{{ end }}
{{ end }}
{{ end }}

{{ define "ding.link.title" }}{{ template "__subject" . }}{{ end }}
{{ define "ding.link.content" }}
#### 📊 告警详情
{{ if gt (len .Alerts.Firing) 0 }}
**🔥 触发中的告警 ({{ .Alerts.Firing | len }})**
{{ template "__alert_list" .Alerts.Firing }}
{{ end }}

{{ if gt (len .Alerts.Resolved) 0 }}
**✅ 已恢复的告警 ({{ .Alerts.Resolved | len }})**
{{ template "__alert_list" .Alerts.Resolved }}
{{ end }}

---
[🔗 查看AlertManager]({{ .ExternalURL }})
{{ end }}
```

### 15.4.3 测试与验证

```bash
# ========================================
# 1. 验证AlertManager配置
# ========================================
$ docker run --rm \
  -v $(pwd)/alertmanager:/etc/alertmanager \
  prom/alertmanager:v0.26.0 \
  amtool check-config /etc/alertmanager/alertmanager.yml
# ✅ Checking '/etc/alertmanager/alertmanager.yml'  SUCCESS

# ========================================
# 2. 部署AlertManager
# ========================================
$ docker stack deploy -c monitoring/stack.yml monitoring

# 查看AlertManager集群状态
$ curl http://localhost:9093/api/v2/status | jq
{
  "cluster": {
    "peers": [
      {"name": "alertmanager-1", "address": "10.0.1.5:9094"},
      {"name": "alertmanager-2", "address": "10.0.1.6:9094"},
      {"name": "alertmanager-3", "address": "10.0.1.7:9094"}
    ],
    "status": "ready"
  },
  "versionInfo": {"version": "0.26.0"}
}

# ========================================
# 3. 模拟告警测试
# ========================================

# 方法1: 使用amtool手动发送测试告警
$ docker exec -it $(docker ps -q -f name=monitoring_alertmanager) sh

$ amtool alert add \
  --alertmanager.url=http://localhost:9093 \
  --annotation=summary="测试告警摘要" \
  --annotation=description="这是一条测试告警,请忽略" \
  alertname="TestAlert" \
  severity="warning" \
  instance="test-instance" \
  service="test-service"
# ✅ 告警已发送

# 方法2: 通过API发送测试告警
$ curl -X POST http://localhost:9093/api/v2/alerts \
  -H "Content-Type: application/json" \
  -d '[
    {
      "labels": {
        "alertname": "TestDatabaseAlert",
        "severity": "critical",
        "category": "database",
        "instance": "postgres-master"
      },
      "annotations": {
        "summary": "数据库连接数过高",
        "description": "当前连接数: 950, 最大连接数: 1000"
      },
      "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
      "endsAt": "'$(date -u -d '+5 minutes' +%Y-%m-%dT%H:%M:%SZ)'"
    }
  ]'

# 方法3: 触发真实告警(临时修改阈值)
# 编辑prometheus/rules/alerts.yml, 将某个阈值改得很低
- alert: ContainerCpuUsageHigh
  expr: |
    ... > 1  # 临时改为1%,触发告警
  for: 1m

# 热重载Prometheus配置
$ curl -X POST http://localhost:9090/-/reload

# 等待1-2分钟后查看告警
$ curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.state=="firing")'

# ========================================
# 4. 验证告警路由
# ========================================

# 查看告警路由树
$ curl http://localhost:9093/api/v2/status | jq '.config.route'

# 测试告警会匹配到哪个路由
$ docker exec -it $(docker ps -q -f name=monitoring_alertmanager) sh
$ amtool config routes test \
  --alertmanager.url=http://localhost:9093 \
  severity=critical \
  category=database
# dba-team  # ✅ 匹配到DBA团队路由

# ========================================
# 5. 验证抑制规则
# ========================================

# 先发送一个HostDown告警
$ curl -X POST http://localhost:9093/api/v2/alerts -d '[{
  "labels": {"alertname": "HostDown", "instance": "node1", "severity": "critical"},
  "annotations": {"summary": "节点node1下线"}
}]'

# 再发送该节点上的容器告警
$ curl -X POST http://localhost:9093/api/v2/alerts -d '[{
  "labels": {"alertname": "ContainerDown", "instance": "node1", "severity": "warning"},
  "annotations": {"summary": "容器下线"}
}]'

# 查看告警状态(ContainerDown应该被抑制)
$ curl http://localhost:9093/api/v2/alerts | jq '.[] | select(.status.state != "suppressed")'
# 应该只看到HostDown告警

# ========================================
# 6. 查看告警历史
# ========================================
$ curl http://localhost:9093/api/v2/alerts/groups | jq

# ========================================
# 7. 静默告警(Silence)
# ========================================

# 创建静默规则(静默1小时)
$ curl -X POST http://localhost:9093/api/v2/silences \
  -H "Content-Type: application/json" \
  -d '{
    "matchers": [
      {
        "name": "instance",
        "value": "test-instance",
        "isRegex": false,
        "isEqual": true
      }
    ],
    "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "endsAt": "'$(date -u -d '+1 hour' +%Y-%m-%dT%H:%M:%SZ)'",
    "createdBy": "admin",
    "comment": "维护窗口,静默test-instance的所有告警"
  }'
# {"silenceID": "abc123..."}

# 查看所有静默规则
$ curl http://localhost:9093/api/v2/silences | jq

# 删除静默规则
$ curl -X DELETE http://localhost:9093/api/v2/silence/abc123

# ========================================
# 8. 钉钉告警验证
# ========================================

# 检查钉钉Webhook服务状态
$ curl http://localhost:8060/ui
# 访问Web UI查看配置

# 发送测试告警到钉钉
$ curl -X POST http://localhost:8060/dingtalk/webhook1/send \
  -H "Content-Type: application/json" \
  -d '{
    "version": "4",
    "groupKey": "{}/{severity=\"warning\"}:{alertname=\"TestAlert\"}",
    "status": "firing",
    "receiver": "dingtalk",
    "groupLabels": {
      "alertname": "TestAlert",
      "severity": "warning"
    },
    "alerts": [
      {
        "status": "firing",
        "labels": {
          "alertname": "TestAlert",
          "severity": "warning",
          "instance": "test-instance"
        },
        "annotations": {
          "summary": "这是一条测试告警",
          "description": "用于验证钉钉Webhook集成是否正常"
        },
        "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'",
        "endsAt": "0001-01-01T00:00:00Z"
      }
    ],
    "externalURL": "http://alertmanager.example.com"
  }'
# ✅ 应该在钉钉群收到消息
```

---

## 15.5 APM应用性能监控

### 15.5.1 分布式追踪(Jaeger)

**1. Jaeger Stack部署**:

```yaml
# monitoring/jaeger-stack.yml
version: '3.8'

services:
  # ========================================
  # Jaeger All-in-One(开发/小规模生产)
  # ========================================
  jaeger:
    image: jaegertracing/all-in-one:1.49
    environment:
      # 存储后端(生产环境建议使用Elasticsearch/Cassandra)
      SPAN_STORAGE_TYPE: badger
      BADGER_DIRECTORY_VALUE: /badger/data
      BADGER_DIRECTORY_KEY: /badger/key
      BADGER_EPHEMERAL: "false"
      BADGER_SPAN_STORE_TTL: "168h"  # 保留7天

      # Collector配置
      COLLECTOR_ZIPKIN_HOST_PORT: ":9411"
      COLLECTOR_OTLP_ENABLED: "true"

      # Query配置
      QUERY_BASE_PATH: /jaeger

      # 采样配置
      SAMPLING_STRATEGIES_FILE: /etc/jaeger/sampling.json

    volumes:
      - jaeger-badger:/badger
      - ./jaeger/sampling.json:/etc/jaeger/sampling.json:ro
    networks:
      - monitoring
    ports:
      - "5775:5775/udp"   # Zipkin compact thrift (deprecated)
      - "6831:6831/udp"   # Jaeger compact thrift
      - "6832:6832/udp"   # Jaeger binary thrift
      - "5778:5778"       # Configs
      - "16686:16686"     # Jaeger UI
      - "14268:14268"     # Jaeger collector HTTP
      - "14250:14250"     # Jaeger collector gRPC
      - "9411:9411"       # Zipkin compatible endpoint
      - "4317:4317"       # OTLP gRPC
      - "4318:4318"       # OTLP HTTP
    deploy:
      mode: replicated
      replicas: 1
      resources:
        limits:
          cpus: '1'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G

  # ========================================
  # Jaeger生产环境部署(使用Elasticsearch)
  # ========================================
  jaeger-collector:
    image: jaegertracing/jaeger-collector:1.49
    environment:
      SPAN_STORAGE_TYPE: elasticsearch
      ES_SERVER_URLS: http://elasticsearch:9200
      ES_INDEX_PREFIX: jaeger
      ES_NUM_SHARDS: 5
      ES_NUM_REPLICAS: 1
      COLLECTOR_QUEUE_SIZE: 2000
      COLLECTOR_NUM_WORKERS: 50
    networks:
      - monitoring
      - backend
    ports:
      - "14250:14250"
      - "14268:14268"
    deploy:
      mode: replicated
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G

  jaeger-query:
    image: jaegertracing/jaeger-query:1.49
    environment:
      SPAN_STORAGE_TYPE: elasticsearch
      ES_SERVER_URLS: http://elasticsearch:9200
      ES_INDEX_PREFIX: jaeger
      QUERY_BASE_PATH: /jaeger
    networks:
      - monitoring
      - backend
    ports:
      - "16686:16686"
    deploy:
      mode: replicated
      replicas: 2

  jaeger-agent:
    image: jaegertracing/jaeger-agent:1.49
    command:
      - "--reporter.grpc.host-port=jaeger-collector:14250"
      - "--reporter.type=grpc"
    networks:
      - monitoring
    ports:
      - "6831:6831/udp"
      - "6832:6832/udp"
      - "5778:5778"
    deploy:
      mode: global  # 每个节点一个Agent

networks:
  monitoring:
    external: true
  backend:
    external: true

volumes:
  jaeger-badger:
```

**2. 采样策略配置**:

```json
// jaeger/sampling.json
{
  "default_strategy": {
    "type": "probabilistic",
    "param": 0.1  // 默认10%采样率
  },
  "service_strategies": [
    {
      "service": "critical-api",
      "type": "probabilistic",
      "param": 1.0  // 关键服务100%采样
    },
    {
      "service": "high-traffic-api",
      "type": "ratelimiting",
      "param": 100  // 高流量服务限速采样(100 traces/s)
    },
    {
      "service": "batch-job",
      "type": "probabilistic",
      "param": 0.01  // 批处理任务1%采样
    }
  ]
}
```

**3. 应用集成Jaeger(Python示例)**:

```python
# app/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

def init_tracer(app, service_name="myapp"):
    """初始化分布式追踪"""

    # 创建Resource(标识服务)
    resource = Resource.create({
        "service.name": service_name,
        "service.version": "1.0.0",
        "deployment.environment": "production",
        "service.namespace": "default"
    })

    # 创建TracerProvider
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    # 配置Jaeger Exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger-agent",  # Jaeger Agent地址
        agent_port=6831,
        udp_split_oversized_batches=True
    )

    # 添加Span Processor(批量发送)
    span_processor = BatchSpanProcessor(
        jaeger_exporter,
        max_queue_size=2048,
        schedule_delay_millis=5000,
        max_export_batch_size=512
    )
    tracer_provider.add_span_processor(span_processor)

    # 自动埋点Flask
    FlaskInstrumentor().instrument_app(app)

    # 自动埋点HTTP请求
    RequestsInstrumentor().instrument()

    # 自动埋点SQLAlchemy
    from app import db
    SQLAlchemyInstrumentor().instrument(
        engine=db.engine,
        enable_commenter=True,  # SQL注释中添加trace_id
        commenter_options={"db_driver": True}
    )

    return tracer_provider

# app.py
from flask import Flask, request, jsonify
from tracing import init_tracer
from opentelemetry import trace

app = Flask(__name__)
init_tracer(app)

tracer = trace.get_tracer(__name__)

@app.route('/api/order', methods=['POST'])
def create_order():
    # 自动创建的Span(由FlaskInstrumentor)
    current_span = trace.get_current_span()

    # 添加自定义属性
    current_span.set_attribute("user.id", request.json.get('user_id'))
    current_span.set_attribute("order.amount", request.json.get('amount'))

    # 手动创建子Span
    with tracer.start_as_current_span("validate_order") as span:
        span.set_attribute("validation.result", "success")
        result = validate_order(request.json)

    # 调用其他服务(自动传递trace context)
    with tracer.start_as_current_span("call_payment_service") as span:
        import requests
        response = requests.post(
            'http://payment-service/api/charge',
            json={'order_id': 123, 'amount': 99.99}
        )
        span.set_attribute("payment.status", response.status_code)

    # 数据库操作(自动追踪)
    with tracer.start_as_current_span("database_insert") as span:
        db.session.add(Order(**request.json))
        db.session.commit()

    return jsonify({"status": "success"}), 201

if __name__ == '__main__':
    app.run()
```

**4. 查询Jaeger Traces**:

```bash
# 访问Jaeger UI
$ open http://jaeger.example.com:16686

# API查询(查找慢查询)
$ curl 'http://localhost:16686/api/traces?service=myapp&limit=20&minDuration=1s' | jq

# 查找包含错误的Trace
$ curl 'http://localhost:16686/api/traces?service=myapp&tags={"error":"true"}' | jq

# 通过TraceID查询完整链路
$ curl 'http://localhost:16686/api/traces/abc123def456' | jq
```

### 15.5.2 应用性能指标采集

**Prometheus + StatsD Exporter集成**:

```yaml
# monitoring/stack.yml (添加)
services:
  statsd-exporter:
    image: prom/statsd-exporter:v0.26.0
    command:
      - '--statsd.mapping-config=/etc/statsd/statsd-mapping.yml'
      - '--statsd.listen-udp=:9125'
      - '--statsd.listen-tcp=:9125'
      - '--web.listen-address=:9102'
    volumes:
      - ./statsd/statsd-mapping.yml:/etc/statsd/statsd-mapping.yml:ro
    networks:
      - monitoring
    ports:
      - "9125:9125/udp"
      - "9102:9102"
    deploy:
      mode: global
```

```yaml
# statsd/statsd-mapping.yml
mappings:
  # HTTP请求计数
  - match: "app.http.requests.*.*.*"
    name: "http_requests_total"
    labels:
      method: "$1"
      endpoint: "$2"
      status: "$3"

  # HTTP请求延迟
  - match: "app.http.request_duration.*.*"
    name: "http_request_duration_seconds"
    timer_type: histogram
    buckets: [0.01, 0.05, 0.1, 0.5, 1, 5]
    labels:
      method: "$1"
      endpoint: "$2"

  # 数据库查询
  - match: "app.db.query_duration.*"
    name: "db_query_duration_seconds"
    timer_type: summary
    labels:
      query_type: "$1"

  # 缓存命中率
  - match: "app.cache.*.*"
    name: "cache_operations_total"
    labels:
      operation: "$1"
      result: "$2"
```

**应用代码集成StatsD**:

```python
# app.py
from statsd import StatsClient
import time

statsd = StatsClient(host='statsd-exporter', port=9125, prefix='app')

@app.route('/api/users/<int:user_id>')
def get_user(user_id):
    start_time = time.time()

    try:
        # 增加请求计数
        statsd.incr(f'http.requests.GET.api_users.200')

        # 检查缓存
        user = cache.get(f'user:{user_id}')
        if user:
            statsd.incr('cache.get.hit')
        else:
            statsd.incr('cache.get.miss')

            # 数据库查询
            query_start = time.time()
            user = User.query.get(user_id)
            statsd.timing('db.query_duration.select',
                         (time.time() - query_start) * 1000)

            cache.set(f'user:{user_id}', user, timeout=300)

        # 记录总延迟
        statsd.timing(f'http.request_duration.GET.api_users',
                     (time.time() - start_time) * 1000)

        return jsonify(user.to_dict())

    except Exception as e:
        statsd.incr(f'http.requests.GET.api_users.500')
        raise
```

---

*（第15章完成,约2650行。已完成15章,剩余4章...）*

---

📝 **下一章预告**: ELK Stack日志收集、日志解析与告警、日志查询与分析、日志归档策略

---

# 第十六章: 日志收集与分析

> **本章目标**: 掌握Docker生产环境日志收集方案,包括ELK Stack企业级部署、Fluentd日志收集、Grok模式解析、Kibana可视化分析、ElastAlert告警,以及日志归档与生命周期管理。

---

## 16.1 日志收集架构设计

### 16.1.1 日志收集架构模式

**完整的日志处理流程**:

```yaml
┌─────────────────────────────────────────────────────────────────┐
│                     日志生成层 (Source)                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ 应用日志  │  │ 系统日志  │  │ 访问日志  │  │ 审计日志  │       │
│  │  (JSON)  │  │ (Syslog) │  │ (Nginx)  │  │ (Docker) │       │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘       │
└────────┼─────────────┼─────────────┼─────────────┼────────────┘
         │             │             │             │
         ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     日志采集层 (Collector)                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐      ┌──────────────────┐                │
│  │   Fluentd/Fluent Bit    │   Filebeat       │                │
│  │  - 多源输入             │   - 轻量级        │                │
│  │  - 强大过滤             │   - 低资源消耗    │                │
│  │  - 缓冲机制             │   - 直接ES集成    │                │
│  └──────────┬───────┘      └──────────┬───────┘                │
└─────────────┼──────────────────────────┼────────────────────────┘
              │                          │
              └─────────┬────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                     日志处理层 (Processing)                      │
├─────────────────────────────────────────────────────────────────┤
│                   ┌──────────────┐                              │
│                   │   Logstash   │                              │
│                   │  - Grok解析  │                              │
│                   │  - 数据转换  │                              │
│                   │  - 多输出    │                              │
│                   └──────┬───────┘                              │
└──────────────────────────┼──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     日志存储层 (Storage)                         │
├─────────────────────────────────────────────────────────────────┤
│             ┌────────────────────────────┐                      │
│             │   Elasticsearch Cluster    │                      │
│             │  ┌──────┐ ┌──────┐ ┌──────┐│                     │
│             │  │ ES-1 │ │ ES-2 │ │ ES-3 ││                     │
│             │  │Master│ │ Data │ │ Data ││                     │
│             │  └──────┘ └──────┘ └──────┘│                     │
│             │  - 分片副本策略             │                      │
│             │  - ILM生命周期管理          │                      │
│             │  - 冷热数据分离             │                      │
│             └────────────┬───────────────┘                      │
└──────────────────────────┼──────────────────────────────────────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
┌─────────────────┐ ┌─────────────┐ ┌──────────────┐
│     Kibana      │ │ ElastAlert  │ │   Curator    │
│   可视化分析     │ │  日志告警    │ │  索引清理    │
└─────────────────┘ └─────────────┘ └──────────────┘
```

**架构选型对比**:

| 组件 | Fluentd | Filebeat | Logstash |
|------|---------|----------|----------|
| **语言** | Ruby | Go | Java |
| **资源消耗** | 中等 | 极低 | 高 |
| **插件生态** | 丰富(1000+) | 有限 | 丰富(200+) |
| **过滤能力** | 强 | 弱 | 强 |
| **缓冲机制** | 内置 | 无 | 内置 |
| **使用场景** | 复杂日志处理 | 简单日志转发 | ETL转换 |
| **CPU占用** | 50-200MB | 10-30MB | 500MB-2GB |

**推荐架构**:
- **小规模**: Filebeat → Elasticsearch → Kibana
- **中规模**: Fluentd → Elasticsearch → Kibana
- **大规模**: Fluentd → Kafka → Logstash → Elasticsearch → Kibana

### 16.1.2 Docker日志驱动

**Docker支持的日志驱动**:

```yaml
日志驱动类型:
  1. json-file (默认)
     - 优点: 简单、docker logs可用
     - 缺点: 无自动轮转、磁盘占用
     - 适用: 开发环境

  2. syslog
     - 优点: 集成系统日志
     - 缺点: 需要syslog服务
     - 适用: 传统运维环境

  3. journald
     - 优点: systemd集成
     - 缺点: 仅Linux
     - 适用: Systemd管理的系统

  4. fluentd
     - 优点: 直接集成Fluentd
     - 缺点: 需要Fluentd运行
     - 适用: 生产环境

  5. gelf (Graylog Extended Log Format)
     - 优点: 结构化日志
     - 缺点: 需要Graylog/Logstash
     - 适用: 微服务架构

  6. none
     - 优点: 无IO开销
     - 缺点: 无法查看日志
     - 适用: 性能敏感场景
```

**配置Docker日志驱动**:

```bash
# 全局配置 - /etc/docker/daemon.json
{
  "log-driver": "fluentd",
  "log-opts": {
    "fluentd-address": "fluentd.example.com:24224",
    "fluentd-async": "true",
    "fluentd-retry-wait": "1s",
    "fluentd-max-retries": "10",
    "tag": "docker.{{.Name}}.{{.ID}}"
  }
}

# 重启Docker使配置生效
$ sudo systemctl restart docker

# 单容器配置 - docker-compose.yml
version: '3.8'
services:
  app:
    image: myapp:latest
    logging:
      driver: fluentd
      options:
        fluentd-address: fluentd:24224
        fluentd-async: "true"
        tag: "docker.app.{{.ID}}"
        labels: "app,version"
        env: "ENVIRONMENT"

# 单容器配置 - docker run
$ docker run -d \
  --log-driver=fluentd \
  --log-opt fluentd-address=fluentd:24224 \
  --log-opt tag="docker.nginx.{{.ID}}" \
  nginx:latest
```

---

## 16.2 Elasticsearch集群部署

### 16.2.1 Elasticsearch集群架构

**生产环境3节点集群架构**:

```yaml
┌─────────────────────────────────────────────────────────┐
│                  Elasticsearch Cluster                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   ES-Master  │  │   ES-Data-1  │  │   ES-Data-2  │ │
│  │              │  │              │  │              │ │
│  │ Roles:       │  │ Roles:       │  │ Roles:       │ │
│  │ - master     │  │ - data       │  │ - data       │ │
│  │ - ingest     │  │ - ingest     │  │ - ingest     │ │
│  │              │  │              │  │              │ │
│  │ Heap: 2GB    │  │ Heap: 16GB   │  │ Heap: 16GB   │ │
│  │ CPU: 2核     │  │ CPU: 8核     │  │ CPU: 8核     │ │
│  │ Mem: 4GB     │  │ Mem: 32GB    │  │ Mem: 32GB    │ │
│  │ Disk: 50GB   │  │ Disk: 500GB  │  │ Disk: 500GB  │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                 │                 │          │
│         └─────────────────┼─────────────────┘          │
│                           │                            │
│                  (集群通信: 9300端口)                   │
└─────────────────────────────────────────────────────────┘
         │                  │                 │
         └──────────────────┼─────────────────┘
                            │
                     (REST API: 9200端口)
                            │
                  ┌─────────┴─────────┐
                  │   Load Balancer   │
                  │  (HAProxy/Nginx)  │
                  └───────────────────┘
```

**节点角色说明**:
- **Master Node**: 集群管理(创建/删除索引、分配分片)
- **Data Node**: 存储数据、执行查询
- **Ingest Node**: 数据预处理(Pipeline)
- **Coordinating Node**: 请求路由和结果聚合

### 16.2.2 Elasticsearch Stack部署

**目录结构**:

```bash
elk/
├── elasticsearch/
│   ├── elasticsearch.yml        # ES配置
│   ├── jvm.options             # JVM参数
│   └── log4j2.properties       # 日志配置
├── logstash/
│   ├── logstash.yml            # Logstash配置
│   ├── pipelines.yml           # Pipeline配置
│   └── pipeline/
│       ├── docker.conf         # Docker日志Pipeline
│       ├── nginx.conf          # Nginx日志Pipeline
│       └── app.conf            # 应用日志Pipeline
├── kibana/
│   └── kibana.yml              # Kibana配置
└── stack.yml                   # Docker Compose配置
```

**1. Elasticsearch集群配置**:

```yaml
# elk/stack.yml
version: '3.8'

services:
  # ========================================
  # Elasticsearch Master Node
  # ========================================
  elasticsearch-master:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: es-master
    environment:
      # 节点配置
      - node.name=es-master
      - node.roles=master,ingest

      # 集群配置
      - cluster.name=docker-elk-cluster
      - cluster.initial_master_nodes=es-master
      - discovery.seed_hosts=es-data-1,es-data-2

      # 网络配置
      - network.host=0.0.0.0
      - http.port=9200
      - transport.port=9300

      # 内存配置
      - ES_JAVA_OPTS=-Xms2g -Xmx2g
      - bootstrap.memory_lock=true

      # 安全配置(生产环境必须启用)
      - xpack.security.enabled=true
      - xpack.security.enrollment.enabled=true
      - ELASTIC_PASSWORD=${ELASTIC_PASSWORD}

      # 监控配置
      - xpack.monitoring.collection.enabled=true
    ulimits:
      memlock:
        soft: -1
        hard: -1
      nofile:
        soft: 65536
        hard: 65536
    volumes:
      - es-master-data:/usr/share/elasticsearch/data
      - ./elasticsearch/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml:ro
      - ./elasticsearch/jvm.options:/usr/share/elasticsearch/config/jvm.options:ro
    networks:
      - elk
    ports:
      - "9200:9200"
      - "9300:9300"
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - node.role == manager
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
    healthcheck:
      test: ["CMD-SHELL", "curl -s -u elastic:${ELASTIC_PASSWORD} http://localhost:9200/_cluster/health | grep -q '\"status\":\"green\\|yellow\"'"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s

  # ========================================
  # Elasticsearch Data Node 1
  # ========================================
  elasticsearch-data-1:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: es-data-1
    environment:
      - node.name=es-data-1
      - node.roles=data,ingest
      - cluster.name=docker-elk-cluster
      - discovery.seed_hosts=es-master,es-data-2
      - cluster.initial_master_nodes=es-master
      - ES_JAVA_OPTS=-Xms16g -Xmx16g
      - bootstrap.memory_lock=true
      - xpack.security.enabled=true
      - ELASTIC_PASSWORD=${ELASTIC_PASSWORD}
    ulimits:
      memlock:
        soft: -1
        hard: -1
      nofile:
        soft: 65536
        hard: 65536
    volumes:
      - es-data-1-data:/usr/share/elasticsearch/data
    networks:
      - elk
    depends_on:
      - elasticsearch-master
    deploy:
      mode: replicated
      replicas: 1
      resources:
        limits:
          cpus: '8'
          memory: 32G
        reservations:
          cpus: '4'
          memory: 16G
    healthcheck:
      test: ["CMD-SHELL", "curl -s http://localhost:9200/_cluster/health"]
      interval: 30s
      timeout: 10s
      retries: 5

  # ========================================
  # Elasticsearch Data Node 2
  # ========================================
  elasticsearch-data-2:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: es-data-2
    environment:
      - node.name=es-data-2
      - node.roles=data,ingest
      - cluster.name=docker-elk-cluster
      - discovery.seed_hosts=es-master,es-data-1
      - cluster.initial_master_nodes=es-master
      - ES_JAVA_OPTS=-Xms16g -Xmx16g
      - bootstrap.memory_lock=true
      - xpack.security.enabled=true
      - ELASTIC_PASSWORD=${ELASTIC_PASSWORD}
    ulimits:
      memlock:
        soft: -1
        hard: -1
      nofile:
        soft: 65536
        hard: 65536
    volumes:
      - es-data-2-data:/usr/share/elasticsearch/data
    networks:
      - elk
    depends_on:
      - elasticsearch-master
    deploy:
      mode: replicated
      replicas: 1
      resources:
        limits:
          cpus: '8'
          memory: 32G
        reservations:
          cpus: '4'
          memory: 16G

  # ========================================
  # Kibana
  # ========================================
  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: kibana
    environment:
      # Elasticsearch连接
      - ELASTICSEARCH_HOSTS=http://elasticsearch-master:9200
      - ELASTICSEARCH_USERNAME=elastic
      - ELASTICSEARCH_PASSWORD=${ELASTIC_PASSWORD}

      # Kibana配置
      - SERVER_NAME=kibana
      - SERVER_HOST=0.0.0.0
      - SERVER_PORT=5601

      # 中文支持
      - I18N_LOCALE=zh-CN

      # 监控配置
      - MONITORING_ENABLED=true
      - XPACK_MONITORING_UI_CONTAINER_ELASTICSEARCH_ENABLED=true
    volumes:
      - kibana-data:/usr/share/kibana/data
      - ./kibana/kibana.yml:/usr/share/kibana/config/kibana.yml:ro
    networks:
      - elk
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch-master
    deploy:
      mode: replicated
      replicas: 2
      placement:
        max_replicas_per_node: 1
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
    healthcheck:
      test: ["CMD-SHELL", "curl -s http://localhost:5601/api/status | grep -q '\"state\":\"green\"'"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s

  # ========================================
  # Logstash
  # ========================================
  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    container_name: logstash
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch-master:9200
      - ELASTICSEARCH_USERNAME=elastic
      - ELASTICSEARCH_PASSWORD=${ELASTIC_PASSWORD}
      - LS_JAVA_OPTS=-Xms2g -Xmx2g
      - XPACK_MONITORING_ENABLED=true
      - XPACK_MONITORING_ELASTICSEARCH_HOSTS=http://elasticsearch-master:9200
    volumes:
      - ./logstash/logstash.yml:/usr/share/logstash/config/logstash.yml:ro
      - ./logstash/pipelines.yml:/usr/share/logstash/config/pipelines.yml:ro
      - ./logstash/pipeline:/usr/share/logstash/pipeline:ro
    networks:
      - elk
    ports:
      - "5044:5044"  # Beats input
      - "9600:9600"  # Logstash monitoring API
    depends_on:
      - elasticsearch-master
    deploy:
      mode: replicated
      replicas: 2
      resources:
        limits:
          cpus: '4'
          memory: 4G
        reservations:
          cpus: '2'
          memory: 2G
    healthcheck:
      test: ["CMD-SHELL", "curl -s http://localhost:9600/_node/stats"]
      interval: 30s
      timeout: 10s
      retries: 5

networks:
  elk:
    driver: overlay
    attachable: true

volumes:
  es-master-data:
  es-data-1-data:
  es-data-2-data:
  kibana-data:
```

**2. Elasticsearch配置文件**:

```yaml
# elk/elasticsearch/elasticsearch.yml
# ========================================
# 集群配置
# ========================================
cluster.name: docker-elk-cluster

# ========================================
# 节点配置
# ========================================
node.name: ${HOSTNAME}
node.roles: [ master, data, ingest ]

# ========================================
# 路径配置
# ========================================
path.data: /usr/share/elasticsearch/data
path.logs: /usr/share/elasticsearch/logs

# ========================================
# 网络配置
# ========================================
network.host: 0.0.0.0
http.port: 9200
transport.port: 9300

# ========================================
# 发现配置
# ========================================
discovery.seed_hosts:
  - es-master
  - es-data-1
  - es-data-2

cluster.initial_master_nodes:
  - es-master

# ========================================
# 内存配置
# ========================================
bootstrap.memory_lock: true

# ========================================
# 安全配置
# ========================================
xpack.security.enabled: true
xpack.security.transport.ssl.enabled: false  # 生产环境建议启用
xpack.security.http.ssl.enabled: false       # 生产环境建议启用

# ========================================
# 索引配置
# ========================================
# 默认分片和副本
index.number_of_shards: 3
index.number_of_replicas: 1

# 慢查询日志
index.search.slowlog.threshold.query.warn: 10s
index.search.slowlog.threshold.query.info: 5s
index.indexing.slowlog.threshold.index.warn: 10s

# ========================================
# 线程池配置
# ========================================
thread_pool.write.queue_size: 1000
thread_pool.search.queue_size: 1000

# ========================================
# 缓存配置
# ========================================
indices.queries.cache.size: 10%
indices.fielddata.cache.size: 20%
indices.requests.cache.size: 2%

# ========================================
# 生命周期管理
# ========================================
xpack.ilm.enabled: true
```

**3. JVM配置**:

```bash
# elk/elasticsearch/jvm.options
# ========================================
# Heap Size (根据节点类型调整)
# ========================================
# Master节点
-Xms2g
-Xmx2g

# Data节点(建议物理内存的50%, 最大32GB)
# -Xms16g
# -Xmx16g

# ========================================
# GC配置 (使用G1 GC)
# ========================================
-XX:+UseG1GC
-XX:G1ReservePercent=25
-XX:InitiatingHeapOccupancyPercent=30

# ========================================
# GC日志
# ========================================
-Xlog:gc*,gc+age=trace,safepoint:file=/usr/share/elasticsearch/logs/gc.log:utctime,pid,tags:filecount=32,filesize=64m

# ========================================
# 堆转储
# ========================================
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/usr/share/elasticsearch/logs/heapdump.hprof

# ========================================
# 错误日志
# ========================================
-XX:ErrorFile=/usr/share/elasticsearch/logs/hs_err_pid%p.log
```

### 16.2.3 索引生命周期管理(ILM)

**ILM策略配置**:

```bash
# 创建日志索引ILM策略
PUT _ilm/policy/logs-policy
{
  "policy": {
    "phases": {
      # ========================================
      # Hot阶段: 活跃写入(0-3天)
      # ========================================
      "hot": {
        "min_age": "0ms",
        "actions": {
          "rollover": {
            "max_size": "50GB",       # 索引大小超过50GB则滚动
            "max_age": "1d",          # 索引创建1天后滚动
            "max_docs": 100000000     # 索引文档数超过1亿则滚动
          },
          "set_priority": {
            "priority": 100           # 高优先级
          }
        }
      },

      # ========================================
      # Warm阶段: 只读,可查询(3-7天)
      # ========================================
      "warm": {
        "min_age": "3d",
        "actions": {
          "readonly": {},             # 设置为只读
          "forcemerge": {
            "max_num_segments": 1     # 强制合并为1个段(提高查询性能)
          },
          "shrink": {
            "number_of_shards": 1     # 缩减分片数(节省资源)
          },
          "allocate": {
            "number_of_replicas": 1   # 保留1个副本
          },
          "set_priority": {
            "priority": 50            # 中等优先级
          }
        }
      },

      # ========================================
      # Cold阶段: 归档存储(7-30天)
      # ========================================
      "cold": {
        "min_age": "7d",
        "actions": {
          "allocate": {
            "require": {
              "data": "cold"          # 迁移到冷数据节点
            },
            "number_of_replicas": 0   # 不保留副本(节省空间)
          },
          "freeze": {},               # 冻结索引(极少查询)
          "set_priority": {
            "priority": 0             # 低优先级
          }
        }
      },

      # ========================================
      # Delete阶段: 删除(30天后)
      # ========================================
      "delete": {
        "min_age": "30d",
        "actions": {
          "delete": {}                # 删除索引
        }
      }
    }
  }
}

# 创建索引模板并应用ILM策略
PUT _index_template/logs-template
{
  "index_patterns": ["logs-*"],
  "template": {
    "settings": {
      "number_of_shards": 3,
      "number_of_replicas": 1,
      "index.lifecycle.name": "logs-policy",
      "index.lifecycle.rollover_alias": "logs"
    },
    "mappings": {
      "properties": {
        "@timestamp": {
          "type": "date"
        },
        "level": {
          "type": "keyword"
        },
        "message": {
          "type": "text",
          "fields": {
            "keyword": {
              "type": "keyword",
              "ignore_above": 256
            }
          }
        },
        "container_name": {
          "type": "keyword"
        },
        "service_name": {
          "type": "keyword"
        },
        "host": {
          "type": "keyword"
        }
      }
    }
  }
}

# 创建初始索引
PUT logs-000001
{
  "aliases": {
    "logs": {
      "is_write_index": true
    }
  }
}
```

**验证ILM策略**:

```bash
# 查看ILM策略
GET _ilm/policy/logs-policy

# 查看索引的ILM状态
GET logs-*/_ilm/explain

# 手动触发rollover(测试用)
POST logs/_rollover

# 查看ILM统计信息
GET _ilm/status
```

---

## 16.3 Fluentd日志收集

### 16.3.1 Fluentd部署配置

**Fluentd Stack配置**:

```yaml
# elk/stack.yml (添加到现有配置)
services:
  # ========================================
  # Fluentd Aggregator(汇聚节点)
  # ========================================
  fluentd:
    image: fluent/fluentd:v1.16-1
    container_name: fluentd
    volumes:
      - ./fluentd/fluent.conf:/fluentd/etc/fluent.conf:ro
      - ./fluentd/plugins:/fluentd/plugins:ro
      - fluentd-buffer:/fluentd/buffer
    networks:
      - elk
    ports:
      - "24224:24224"   # Forward input
      - "24224:24224/udp"
      - "9880:9880"     # HTTP input
    environment:
      - FLUENTD_CONF=fluent.conf
      - ELASTICSEARCH_HOST=elasticsearch-master
      - ELASTICSEARCH_PORT=9200
      - ELASTICSEARCH_USER=elastic
      - ELASTICSEARCH_PASSWORD=${ELASTIC_PASSWORD}
    depends_on:
      - elasticsearch-master
    deploy:
      mode: replicated
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 512M
    healthcheck:
      test: ["CMD-SHELL", "curl -s http://localhost:9880/api/plugins.json"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ========================================
  # Fluent Bit (轻量级采集器,每个节点)
  # ========================================
  fluent-bit:
    image: fluent/fluent-bit:2.2
    volumes:
      - ./fluent-bit/fluent-bit.conf:/fluent-bit/etc/fluent-bit.conf:ro
      - ./fluent-bit/parsers.conf:/fluent-bit/etc/parsers.conf:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/log:/var/log:ro
    networks:
      - elk
    deploy:
      mode: global  # 每个节点一个实例
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.1'
          memory: 64M

volumes:
  fluentd-buffer:
```

**Fluentd配置文件**:

```ruby
# elk/fluentd/fluent.conf
# ========================================
# Source: 接收Docker日志
# ========================================
<source>
  @type forward
  @id docker_forward
  @label @docker
  port 24224
  bind 0.0.0.0

  # 安全配置
  <security>
    self_hostname fluentd
    shared_key ${FLUENTD_SHARED_KEY}
  </security>

  # 缓冲配置
  <transport tls>
    cert_path /fluentd/certs/fluentd.crt
    private_key_path /fluentd/certs/fluentd.key
  </transport>
</source>

# ========================================
# Source: HTTP输入(应用直接发送日志)
# ========================================
<source>
  @type http
  @id http_input
  @label @app
  port 9880
  bind 0.0.0.0

  # 解析JSON
  <parse>
    @type json
    time_key timestamp
    time_format %iso8601
  </parse>
</source>

# ========================================
# Source: Syslog输入
# ========================================
<source>
  @type syslog
  @id syslog_input
  @label @syslog
  port 5140
  bind 0.0.0.0
  tag system

  <parse>
    message_format rfc5424
  </parse>
</source>

# ========================================
# Label: Docker日志处理
# ========================================
<label @docker>
  # Filter: 解析Docker日志
  <filter docker.**>
    @type parser
    key_name log
    reserve_data true
    remove_key_name_field false

    <parse>
      @type json
      time_key timestamp
      time_format %iso8601
      keep_time_key true
    </parse>
  </filter>

  # Filter: 添加Kubernetes元数据(如果使用K8s)
  <filter docker.**>
    @type record_transformer
    enable_ruby true

    <record>
      # 提取容器名称
      container_name ${record["container_name"] || "unknown"}

      # 提取容器ID
      container_id ${record["container_id"] || "unknown"}

      # 添加主机名
      hostname "#{Socket.gethostname}"

      # 添加时间戳(如果不存在)
      timestamp ${record["timestamp"] || Time.now.iso8601}
    </record>
  </filter>

  # Filter: 删除敏感信息
  <filter docker.**>
    @type grep
    <exclude>
      key message
      pattern /(password|secret|token|key)=/i
    </exclude>
  </filter>

  # Filter: 多行日志合并(Java堆栈跟踪)
  <filter docker.app.**>
    @type concat
    key message
    multiline_start_regexp /^(\d{4}-\d{2}-\d{2}|Exception|Error)/
    multiline_end_regexp /^\s*at\s+/
    flush_interval 5s
    timeout_label @output
  </filter>

  # Match: 输出到Elasticsearch
  <match docker.**>
    @type elasticsearch
    @id elasticsearch_docker
    @log_level info

    # Elasticsearch连接
    host "#{ENV['ELASTICSEARCH_HOST']}"
    port "#{ENV['ELASTICSEARCH_PORT']}"
    user "#{ENV['ELASTICSEARCH_USER']}"
    password "#{ENV['ELASTICSEARCH_PASSWORD']}"
    scheme http

    # 索引配置
    index_name logs-docker-%Y.%m.%d
    logstash_format true
    logstash_prefix logs-docker
    logstash_dateformat %Y.%m.%d

    # 类型映射
    type_name _doc

    # 缓冲配置
    <buffer tag, time>
      @type file
      path /fluentd/buffer/docker

      # 缓冲块配置
      chunk_limit_size 16MB
      chunk_limit_records 10000

      # 刷新配置
      flush_mode interval
      flush_interval 10s
      flush_at_shutdown true

      # 重试配置
      retry_type exponential_backoff
      retry_wait 1s
      retry_max_interval 60s
      retry_timeout 1h
      retry_max_times 10

      # 溢出配置
      overflow_action drop_oldest_chunk

      # 队列配置
      total_limit_size 1GB
    </buffer>

    # 批量写入配置
    bulk_message_request_threshold 20MB

    # 健康检查
    health_check_uri /
    health_check_interval 30s

    # 模板配置
    template_name logs-docker
    template_file /fluentd/etc/docker-template.json
    template_overwrite true

    # 错误处理
    <secondary>
      @type file
      path /fluentd/buffer/failed/docker
      compress gzip
    </secondary>
  </match>
</label>

# ========================================
# Label: 应用日志处理
# ========================================
<label @app>
  # Filter: 添加标准字段
  <filter app.**>
    @type record_transformer
    <record>
      source application
      environment production
      timestamp ${time.iso8601}
    </record>
  </filter>

  # Match: 根据日志级别路由
  <match app.**>
    @type rewrite_tag_filter

    <rule>
      key level
      pattern /^(ERROR|FATAL)$/
      tag app.error.${tag}
    </rule>

    <rule>
      key level
      pattern /^WARN$/
      tag app.warn.${tag}
    </rule>

    <rule>
      key level
      pattern /.*/
      tag app.info.${tag}
    </rule>
  </match>

  # Match: Error级别日志
  <match app.error.**>
    @type copy

    # 发送到Elasticsearch
    <store>
      @type elasticsearch
      host "#{ENV['ELASTICSEARCH_HOST']}"
      port "#{ENV['ELASTICSEARCH_PORT']}"
      user "#{ENV['ELASTICSEARCH_USER']}"
      password "#{ENV['ELASTICSEARCH_PASSWORD']}"
      index_name logs-app-error-%Y.%m.%d

      <buffer>
        @type file
        path /fluentd/buffer/app-error
        flush_interval 5s
      </buffer>
    </store>

    # 发送告警
    <store>
      @type http
      endpoint http://alertmanager:9093/api/v1/alerts
      open_timeout 2
      json_array true

      <format>
        @type json
      </format>

      <buffer>
        flush_interval 1s
      </buffer>
    </store>
  </match>

  # Match: 其他级别日志
  <match app.**>
    @type elasticsearch
    host "#{ENV['ELASTICSEARCH_HOST']}"
    port "#{ENV['ELASTICSEARCH_PORT']}"
    user "#{ENV['ELASTICSEARCH_USER']}"
    password "#{ENV['ELASTICSEARCH_PASSWORD']}"
    index_name logs-app-%Y.%m.%d

    <buffer>
      @type file
      path /fluentd/buffer/app
      flush_interval 10s
    </buffer>
  </match>
</label>

# ========================================
# 系统监控
# ========================================
<source>
  @type monitor_agent
  bind 0.0.0.0
  port 24220
</source>

# ========================================
# Prometheus监控指标
# ========================================
<source>
  @type prometheus
  bind 0.0.0.0
  port 24231
  metrics_path /metrics
</source>

<source>
  @type prometheus_monitor
  <labels>
    host #{Socket.gethostname}
  </labels>
</source>

<source>
  @type prometheus_output_monitor
  <labels>
    host #{Socket.gethostname}
  </labels>
</source>
```

**Elasticsearch索引模板**:

```json
// elk/fluentd/docker-template.json
{
  "index_patterns": ["logs-docker-*"],
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "index.lifecycle.name": "logs-policy",
    "index.lifecycle.rollover_alias": "logs-docker",
    "index.refresh_interval": "5s",
    "index.translog.durability": "async",
    "index.translog.sync_interval": "30s"
  },
  "mappings": {
    "properties": {
      "@timestamp": {
        "type": "date"
      },
      "container_name": {
        "type": "keyword"
      },
      "container_id": {
        "type": "keyword"
      },
      "source": {
        "type": "keyword"
      },
      "level": {
        "type": "keyword"
      },
      "message": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 512
          }
        },
        "norms": false
      },
      "hostname": {
        "type": "keyword"
      },
      "tags": {
        "type": "keyword"
      }
    }
  }
}
```

### 16.3.2 Fluent Bit配置(轻量级采集)

```ini
# elk/fluent-bit/fluent-bit.conf
[SERVICE]
    Flush        5
    Daemon       Off
    Log_Level    info
    Parsers_File parsers.conf

# ========================================
# Input: Docker容器日志
# ========================================
[INPUT]
    Name              tail
    Path              /var/lib/docker/containers/*/*.log
    Parser            docker
    Tag               docker.*
    Refresh_Interval  5
    Mem_Buf_Limit     50MB
    Skip_Long_Lines   On
    DB                /fluent-bit/tail-docker.db

# ========================================
# Input: 系统日志
# ========================================
[INPUT]
    Name   systemd
    Tag    systemd.*
    Read_From_Tail On

# ========================================
# Filter: 解析Docker JSON
# ========================================
[FILTER]
    Name                parser
    Match               docker.*
    Key_Name            log
    Parser              docker-json
    Reserve_Data        True
    Preserve_Key        True

# ========================================
# Filter: 添加Kubernetes元数据(可选)
# ========================================
[FILTER]
    Name                kubernetes
    Match               docker.*
    Kube_URL            https://kubernetes.default.svc:443
    Kube_CA_File        /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    Kube_Token_File     /var/run/secrets/kubernetes.io/serviceaccount/token
    Kube_Tag_Prefix     docker.var.log.containers.
    Merge_Log           On
    Keep_Log            Off

# ========================================
# Output: 转发到Fluentd
# ========================================
[OUTPUT]
    Name          forward
    Match         *
    Host          fluentd
    Port          24224
    Retry_Limit   10

    # TLS配置
    tls           on
    tls_verify    off

    # 共享密钥
    Shared_Key    ${FLUENTD_SHARED_KEY}
```

**Parser配置**:

```ini
# elk/fluent-bit/parsers.conf
[PARSER]
    Name   docker
    Format json
    Time_Key time
    Time_Format %Y-%m-%dT%H:%M:%S.%LZ
    Time_Keep On

[PARSER]
    Name   docker-json
    Format json
    Time_Key timestamp
    Time_Format %Y-%m-%dT%H:%M:%S.%LZ

[PARSER]
    Name   nginx
    Format regex
    Regex ^(?<remote>[^ ]*) - (?<user>[^ ]*) \[(?<time>[^\]]*)\] "(?<method>\S+)(?: +(?<path>[^\"]*?)(?: +\S*)?)?" (?<code>[^ ]*) (?<size>[^ ]*)(?: "(?<referer>[^\"]*)" "(?<agent>[^\"]*)")?$
    Time_Key time
    Time_Format %d/%b/%Y:%H:%M:%S %z

[PARSER]
    Name   syslog
    Format regex
    Regex ^\<(?<pri>[0-9]+)\>(?<time>[^ ]* {1,2}[^ ]* [^ ]*) (?<host>[^ ]*) (?<ident>[a-zA-Z0-9_\/\.\-]*)(?:\[(?<pid>[0-9]+)\])?(?:[^\:]*\:)? *(?<message>.*)$
    Time_Key time
    Time_Format %b %d %H:%M:%S
```

---

*（第16章完成,约2500行。已完成16章,剩余3章...）*

---

# 第17章: 性能优化

## 17.1 容器性能分析基础

### 17.1.1 性能分析方法论

**USE方法（Utilization, Saturation, Errors）**
```
┌─────────────────────────────────────────────────────────┐
│           容器性能分析USE方法                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [1] Utilization (利用率)                                │
│      ├─ CPU利用率                                         │
│      ├─ 内存利用率                                         │
│      ├─ 网络带宽利用率                                      │
│      └─ 磁盘IO利用率                                       │
│                                                         │
│  [2] Saturation (饱和度)                                 │
│      ├─ CPU运行队列长度                                    │
│      ├─ 内存页面交换                                       │
│      ├─ 网络数据包队列                                      │
│      └─ 磁盘IO等待队列                                     │
│                                                         │
│  [3] Errors (错误率)                                     │
│      ├─ 网络丢包率                                         │
│      ├─ 磁盘读写错误                                       │
│      ├─ OOM Killer事件                                   │
│      └─ 容器重启次数                                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**RED方法（Rate, Errors, Duration）- 应用层**
```yaml
# 服务级别性能指标
RED方法:
  Rate (请求率):
    - 每秒请求数 (RPS)
    - 每分钟事务数 (TPM)

  Errors (错误率):
    - HTTP 5xx错误率
    - 超时错误率
    - 业务逻辑错误率

  Duration (响应时间):
    - P50延迟 (中位数)
    - P95延迟
    - P99延迟
    - 最大延迟
```

### 17.1.2 性能分析工具栈

**工具选择矩阵**
```
┌──────────────┬─────────────┬──────────────┬─────────────┐
│   分析层次     │   主要工具   │   适用场景    │   开销等级   │
├──────────────┼─────────────┼──────────────┼─────────────┤
│ 系统级       │ top/htop    │ 实时监控      │ 低          │
│ 系统级       │ vmstat      │ 内存/CPU分析  │ 低          │
│ 系统级       │ iostat      │ 磁盘IO分析    │ 低          │
│ 系统级       │ netstat     │ 网络连接分析  │ 低          │
├──────────────┼─────────────┼──────────────┼─────────────┤
│ 容器级       │ docker stats│ 容器资源监控  │ 低          │
│ 容器级       │ cAdvisor    │ 详细指标采集  │ 中          │
│ 容器级       │ ctop        │ 交互式监控    │ 低          │
├──────────────┼─────────────┼──────────────┼─────────────┤
│ 进程级       │ strace      │ 系统调用追踪  │ 高          │
│ 进程级       │ lsof        │ 文件句柄分析  │ 低          │
│ 进程级       │ pmap        │ 内存映射分析  │ 低          │
│ 进程级       │ perf        │ CPU性能分析   │ 中-高       │
├──────────────┼─────────────┼──────────────┼─────────────┤
│ 应用级       │ JProfiler   │ Java性能分析  │ 高          │
│ 应用级       │ py-spy      │ Python性能分析│ 中          │
│ 应用级       │ pprof       │ Go性能分析    │ 中          │
└──────────────┴─────────────┴──────────────┴─────────────┘
```

**cAdvisor容器监控部署**
```yaml
# docker-stack-cadvisor.yml
version: '3.8'

services:
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.47.0
    hostname: '{{.Node.Hostname}}'
    command:
      - '--housekeeping_interval=10s'
      - '--docker_only=true'
      - '--storage_duration=1m0s'
      - '--disable_metrics=disk,network,tcp,udp,percpu,sched,process'
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    deploy:
      mode: global  # 每个节点运行一个实例
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.1'
          memory: 128M
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
```

**部署cAdvisor**
```bash
# 部署cAdvisor到所有节点
docker stack deploy -c docker-stack-cadvisor.yml monitoring

# 验证部署
docker service ls | grep cadvisor

# 查看指标（选择任一节点）
curl http://localhost:8080/metrics | grep container_cpu

# 示例输出
container_cpu_usage_seconds_total{id="/docker/abc123"} 124.5
container_memory_usage_bytes{id="/docker/abc123"} 524288000
```

### 17.1.3 性能基准测试

**容器启动性能测试**
```bash
#!/bin/bash
# benchmark-container-startup.sh - 容器启动性能基准测试

IMAGE="nginx:alpine"
ITERATIONS=100

echo "容器启动性能测试 - 迭代次数: $ITERATIONS"
echo "镜像: $IMAGE"
echo "----------------------------------------"

# 测试1: 冷启动（每次删除容器）
total_time=0
for i in $(seq 1 $ITERATIONS); do
    start=$(date +%s%N)

    docker run -d --name test-$i $IMAGE >/dev/null
    docker wait test-$i >/dev/null 2>&1 &
    sleep 0.1
    docker rm -f test-$i >/dev/null

    end=$(date +%s%N)
    elapsed=$(( (end - start) / 1000000 ))  # 转换为毫秒
    total_time=$(( total_time + elapsed ))

    if [ $(( i % 10 )) -eq 0 ]; then
        echo "进度: $i/$ITERATIONS"
    fi
done

avg_time=$(( total_time / ITERATIONS ))
echo ""
echo "冷启动平均时间: ${avg_time}ms"

# 测试2: 热启动（复用容器）
echo ""
echo "测试热启动（start/stop）..."

docker run -d --name test-hot $IMAGE >/dev/null
sleep 1

total_time=0
for i in $(seq 1 $ITERATIONS); do
    docker stop test-hot >/dev/null

    start=$(date +%s%N)
    docker start test-hot >/dev/null
    end=$(date +%s%N)

    elapsed=$(( (end - start) / 1000000 ))
    total_time=$(( total_time + elapsed ))
done

docker rm -f test-hot >/dev/null

avg_hot_time=$(( total_time / ITERATIONS ))
echo "热启动平均时间: ${avg_hot_time}ms"
echo ""
echo "性能提升: $(( (avg_time - avg_hot_time) * 100 / avg_time ))%"
```

**执行基准测试**
```bash
chmod +x benchmark-container-startup.sh
./benchmark-container-startup.sh

# 预期输出
容器启动性能测试 - 迭代次数: 100
镜像: nginx:alpine
----------------------------------------
进度: 10/100
进度: 20/100
...
冷启动平均时间: 523ms

测试热启动（start/stop）...
热启动平均时间: 145ms

性能提升: 72%
```

## 17.2 CPU性能优化

### 17.2.1 CPU限制与配额

**CPU资源限制策略**
```yaml
# CPU限制配置示例
services:
  web:
    image: myapp:latest
    deploy:
      resources:
        limits:
          cpus: '2.0'        # 最多使用2个CPU核心
        reservations:
          cpus: '0.5'        # 保证至少0.5个核心

  # 实时应用 - 严格CPU配额
  realtime-processor:
    image: processor:latest
    deploy:
      resources:
        limits:
          cpus: '4.0'
        reservations:
          cpus: '4.0'        # 预留等于限制 - 确保独占资源

  # 批处理任务 - 弹性CPU配额
  batch-job:
    image: batch:latest
    deploy:
      resources:
        limits:
          cpus: '8.0'        # 峰值可用8核
        reservations:
          cpus: '1.0'        # 基础保证1核
```

**CPU亲和性（CPU Pinning）**
```yaml
# docker-compose-cpu-pinning.yml
version: '3.8'

services:
  # 场景1: 绑定到特定CPU核心
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    cpuset: "0,1"  # 仅使用CPU 0和1
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
    volumes:
      - redis-data:/data

  # 场景2: NUMA节点优化
  database:
    image: postgres:15-alpine
    cpuset: "0-7"   # 使用NUMA节点0的CPU (假设0-7是节点0)
    mem_limit: 16G
    environment:
      - POSTGRES_SHARED_BUFFERS=4GB
    deploy:
      placement:
        constraints:
          - node.labels.numa_node == 0

  # 场景3: 避免CPU0（系统中断处理）
  app:
    image: myapp:latest
    cpuset: "2-15"  # 避开CPU 0-1,留给系统和关键服务
    deploy:
      replicas: 4
      resources:
        limits:
          cpus: '2.0'

volumes:
  redis-data:
```

**查看NUMA拓扑**
```bash
# 安装numactl工具
apt-get update && apt-get install -y numactl

# 查看NUMA节点信息
numactl --hardware

# 示例输出
available: 2 nodes (0-1)
node 0 cpus: 0 1 2 3 4 5 6 7 16 17 18 19 20 21 22 23
node 0 size: 65536 MB
node 0 free: 32768 MB
node 1 cpus: 8 9 10 11 12 13 14 15 24 25 26 27 28 29 30 31
node 1 size: 65536 MB
node 1 free: 45678 MB

# 查看进程NUMA分配
numastat -p $(docker inspect -f '{{.State.Pid}}' container_name)
```

**运行时修改CPU配额**
```bash
# 动态调整CPU限制（无需重启容器）
docker update --cpus="4.0" --cpuset-cpus="0-3" my-container

# 查看当前CPU配置
docker inspect my-container | jq '.[0].HostConfig.CpuQuota'
docker inspect my-container | jq '.[0].HostConfig.CpusetCpus'

# 验证生效
docker stats my-container --no-stream
```

### 17.2.2 CPU性能分析与调优

**使用perf进行CPU性能分析**
```bash
# 安装perf工具
apt-get install -y linux-tools-common linux-tools-$(uname -r)

# 获取容器PID
CONTAINER_PID=$(docker inspect -f '{{.State.Pid}}' my-app)

# 方法1: 记录30秒的CPU性能数据
perf record -F 99 -p $CONTAINER_PID -g -- sleep 30

# 生成火焰图可视化数据
perf script | ./FlameGraph/stackcollapse-perf.pl | \
  ./FlameGraph/flamegraph.pl > cpu-flamegraph.svg

# 方法2: 实时查看热点函数
perf top -p $CONTAINER_PID

# 方法3: 统计CPU事件
perf stat -p $CONTAINER_PID sleep 10

# 示例输出
 Performance counter stats for process id '12345':

      8,234.56 msec task-clock                #    0.823 CPUs utilized
         1,234      context-switches          #    0.150 K/sec
            12      cpu-migrations            #    0.001 K/sec
         5,678      page-faults               #    0.689 K/sec
23,456,789,012      cycles                    #    2.848 GHz
15,678,901,234      instructions              #    0.67  insn per cycle
 3,456,789,012      branches                  #  419.876 M/sec
    12,345,678      branch-misses             #    0.36% of all branches
```

**CPU上下文切换分析**
```bash
# 监控容器的上下文切换
docker stats --format "table {{.Container}}\t{{.CPUPerc}}" --no-stream

# 使用pidstat查看详细上下文切换
apt-get install -y sysstat

# 每秒采样一次,显示5次
pidstat -w -p $CONTAINER_PID 1 5

# 示例输出 - 高上下文切换示例
12:00:01      PID   cswch/s nvcswch/s  Command
12:00:02    12345    523.00   1234.00  java
12:00:03    12345    567.00   1456.00  java
# cswch/s: 自愿上下文切换（IO等待）
# nvcswch/s: 非自愿上下文切换（时间片用完）

# 如果nvcswch/s很高,说明CPU竞争严重,需要:
# 1. 增加CPU配额
# 2. 减少线程数
# 3. 优化应用逻辑
```

**CPU中断分析**
```bash
# 查看中断分布
watch -n 1 'cat /proc/interrupts | head -20'

# 查看软中断
watch -n 1 'cat /proc/softirqs'

# 将网络中断绑定到特定CPU（避免干扰应用）
# 查找网卡中断号
grep eth0 /proc/interrupts

# 设置CPU亲和性（示例：绑定到CPU 0）
echo 1 > /proc/irq/123/smp_affinity_list  # 123是中断号
```

### 17.2.3 CPU调度优化

**CFS调度器参数调优**
```bash
# 调整容器CPU权重（shares）
# 默认值1024,值越大获得的CPU时间越多

# 示例:关键服务获得更多CPU时间
docker run -d \
  --name critical-service \
  --cpu-shares 2048 \    # 2倍权重
  myapp:latest

docker run -d \
  --name background-task \
  --cpu-shares 512 \     # 0.5倍权重
  batch:latest

# 验证:在CPU竞争时,critical-service获得的CPU时间是background-task的4倍
```

**实时调度策略（谨慎使用）**
```yaml
# docker-compose-realtime.yml
version: '3.8'

services:
  realtime-app:
    image: realtime:latest
    # 需要宿主机内核支持CONFIG_RT_GROUP_SCHED
    cap_add:
      - SYS_NICE      # 允许修改进程优先级
    security_opt:
      - apparmor=unconfined
    deploy:
      resources:
        limits:
          cpus: '2.0'
        reservations:
          cpus: '2.0'  # 确保独占CPU
```

**进程优先级调整**
```bash
# 在容器内调整进程优先级
docker exec my-container bash -c '
  # 查看当前nice值
  ps -eo pid,ni,comm | grep myapp

  # 降低优先级（提高nice值:0到19）
  renice +10 -p $(pgrep myapp)

  # 提高优先级（降低nice值:-20到0,需要root）
  renice -5 -p $(pgrep myapp)
'

# 使用chrt设置实时优先级（需要CAP_SYS_NICE）
docker exec my-container chrt -f -p 50 $(pgrep myapp)
# -f: FIFO调度策略
# -p 50: 实时优先级50（1-99）
```

## 17.3 内存性能优化

### 17.3.1 内存限制与预留

**内存限制最佳实践**
```yaml
version: '3.8'

services:
  # 场景1: Java应用 - 堆内存+元空间+堆外内存
  java-app:
    image: openjdk:17-slim
    environment:
      # JVM堆内存=容器内存的75%
      - JAVA_OPTS=-Xms2g -Xmx2g -XX:MaxMetaspaceSize=256m
    deploy:
      resources:
        limits:
          memory: 3G      # 2G堆+256M元空间+768M堆外+OS开销
        reservations:
          memory: 2G

  # 场景2: Redis - 内存+持久化缓冲
  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 7gb --maxmemory-policy allkeys-lru
    deploy:
      resources:
        limits:
          memory: 8G      # 7G数据+1G持久化缓冲
        reservations:
          memory: 4G

  # 场景3: Nginx - 最小内存占用
  nginx:
    image: nginx:alpine
    deploy:
      resources:
        limits:
          memory: 128M
        reservations:
          memory: 64M

  # 场景4: 数据库 - 大内存+Swap
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_SHARED_BUFFERS=8GB
      - POSTGRES_EFFECTIVE_CACHE_SIZE=24GB
    deploy:
      resources:
        limits:
          memory: 32G
        reservations:
          memory: 16G
    # 允许使用Swap作为缓冲
    mem_swappiness: 10
```

**内存预留与OOM优先级**
```yaml
services:
  # 关键服务 - 最低OOM优先级
  critical-db:
    image: postgres:15
    deploy:
      resources:
        limits:
          memory: 16G
        reservations:
          memory: 16G    # 预留等于限制
    # OOM Score Adj: -1000到1000
    # 越低越不容易被OOM Killer杀死
    oom_score_adj: -500

  # 普通服务 - 默认OOM优先级
  web-app:
    image: webapp:latest
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
    # 默认oom_score_adj: 0

  # 批处理任务 - 高OOM优先级（优先牺牲）
  batch-worker:
    image: worker:latest
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 2G
    oom_score_adj: 500
```

### 17.3.2 内存性能分析

**内存使用分析脚本**
```bash
#!/bin/bash
# analyze-memory.sh - 容器内存详细分析

CONTAINER=$1

if [ -z "$CONTAINER" ]; then
    echo "用法: $0 <容器名称>"
    exit 1
fi

echo "=========================================="
echo "容器内存分析: $CONTAINER"
echo "=========================================="

# 1. Docker Stats内存统计
echo -e "\n[1] Docker Stats内存使用:"
docker stats $CONTAINER --no-stream --format \
  "table {{.MemUsage}}\t{{.MemPerc}}"

# 2. Cgroup内存详细信息
CONTAINER_ID=$(docker inspect -f '{{.Id}}' $CONTAINER)
CGROUP_PATH="/sys/fs/cgroup/memory/docker/$CONTAINER_ID"

if [ -d "$CGROUP_PATH" ]; then
    echo -e "\n[2] Cgroup内存详细:"
    echo "内存限制: $(cat $CGROUP_PATH/memory.limit_in_bytes | \
      awk '{print $1/1024/1024 " MB"}')"
    echo "当前使用: $(cat $CGROUP_PATH/memory.usage_in_bytes | \
      awk '{print $1/1024/1024 " MB"}')"
    echo "缓存内存: $(cat $CGROUP_PATH/memory.stat | \
      grep ^cache | awk '{print $2/1024/1024 " MB"}')"
    echo "RSS内存: $(cat $CGROUP_PATH/memory.stat | \
      grep ^rss | head -1 | awk '{print $2/1024/1024 " MB"}')"
    echo "Swap使用: $(cat $CGROUP_PATH/memory.memsw.usage_in_bytes | \
      awk '{print $1/1024/1024 " MB"}')"
fi

# 3. 容器内进程内存排行
echo -e "\n[3] 容器内TOP 5进程内存使用:"
docker exec $CONTAINER sh -c '
  ps aux --sort=-%mem | head -6 | \
  awk "{printf \"%-15s %6s %6s %s\n\", \$1, \$3, \$4, \$11}"
'

# 4. 检查OOM事件
echo -e "\n[4] OOM Killer事件:"
docker inspect $CONTAINER | \
  jq '.[0].State.OOMKilled'

# 5. 内存统计历史（如果有cAdvisor）
echo -e "\n[5] 内存趋势（最近1小时）:"
if command -v curl &> /dev/null; then
    curl -s "http://localhost:8080/api/v1.3/docker/$CONTAINER" | \
      jq -r '.stats[-60:] | .[] |
        "\(.timestamp) \(.memory_stats.usage / 1024 / 1024 | floor) MB"' | \
      tail -10 2>/dev/null || echo "cAdvisor未运行"
fi

echo -e "\n=========================================="
```

**执行内存分析**
```bash
chmod +x analyze-memory.sh
./analyze-memory.sh my-app

# 示例输出
==========================================
容器内存分析: my-app
==========================================

[1] Docker Stats内存使用:
MEM USAGE / LIMIT   MEM %
1.234GiB / 2GiB     61.7%

[2] Cgroup内存详细:
内存限制: 2048 MB
当前使用: 1264 MB
缓存内存: 234 MB
RSS内存: 1030 MB
Swap使用: 0 MB

[3] 容器内TOP 5进程内存使用:
USER            CPU%   MEM%  COMMAND
app             45.2   58.3  /usr/bin/java
app             2.1    3.2   node
root            0.1    0.5   nginx
```

**Java堆内存分析**
```bash
# 容器内执行jmap分析
docker exec my-java-app jmap -heap 1

# 示例输出
Heap Configuration:
   MinHeapFreeRatio         = 40
   MaxHeapFreeRatio         = 70
   MaxHeapSize              = 2147483648 (2048.0MB)
   NewSize                  = 715653120 (682.5MB)
   MaxNewSize               = 715653120 (682.5MB)
   OldSize                  = 1431830528 (1365.5MB)

Heap Usage:
New Generation (Eden + 1 Survivor Space):
   capacity = 644349952 (614.5MB)
   used     = 523678432 (499.3MB)    # 81.2%使用率
   free     = 120671520 (115.2MB)

Eden Space:
   capacity = 572653568 (546.0MB)
   used     = 512345678 (488.6MB)    # 89.5%使用率

Old Generation:
   capacity = 1431830528 (1365.5MB)
   used     = 834567890 (796.2MB)    # 58.3%使用率

# 生成堆转储文件
docker exec my-java-app jmap -dump:format=b,file=/tmp/heap.hprof 1

# 复制到宿主机分析
docker cp my-java-app:/tmp/heap.hprof ./
# 使用MAT (Memory Analyzer Tool)分析
```

### 17.3.3 Huge Pages优化

**Huge Pages配置**
```bash
# 宿主机配置Huge Pages
# 查看当前配置
cat /proc/meminfo | grep Huge

# 示例输出
HugePages_Total:       0
HugePages_Free:        0
HugePages_Rsvd:        0
HugePages_Surp:        0
Hugepagesize:       2048 kB

# 分配1024个2MB的Huge Pages (共2GB)
echo 1024 > /proc/sys/vm/nr_hugepages

# 持久化配置
cat >> /etc/sysctl.conf <<EOF
vm.nr_hugepages = 1024
vm.hugetlb_shm_group = 0
EOF

sysctl -p

# 验证
cat /proc/meminfo | grep HugePages_Total
# HugePages_Total:    1024
```

**Docker容器使用Huge Pages**
```yaml
# docker-compose-hugepages.yml
version: '3.8'

services:
  # 数据库使用Huge Pages
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_SHARED_BUFFERS=1GB
      # PostgreSQL使用Huge Pages
      - POSTGRES_HUGE_PAGES=try
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - type: tmpfs
        target: /dev/hugepages
        tmpfs:
          size: 2G
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
          hugepages-2MB: 1GB  # 预留1GB Huge Pages

  # Redis使用Huge Pages
  redis:
    image: redis:7-alpine
    command: >
      sh -c "
        echo never > /sys/kernel/mm/transparent_hugepage/enabled &&
        redis-server
          --maxmemory 2gb
          --maxmemory-policy allkeys-lru
      "
    privileged: true  # 需要修改THP设置
    deploy:
      resources:
        limits:
          memory: 3G
        reservations:
          hugepages-2MB: 512M

volumes:
  postgres-data:
```

**验证Huge Pages使用**
```bash
# 查看容器Huge Pages使用情况
docker exec postgres grep Huge /proc/meminfo

# 示例输出
HugePages_Total:    1024
HugePages_Free:      512  # 已使用512个(1GB)
HugePages_Rsvd:      256
Hugepagesize:       2048 kB

# 监控Huge Pages效果
# 对比使用前后的性能指标:
# 1. 内存访问延迟降低
# 2. TLB缓存命中率提升
# 3. CPU利用率可能略微下降
```

## 17.4 网络性能优化

### 17.4.1 网络模式选择

**网络模式性能对比**
```
┌──────────────┬──────────┬──────────┬──────────┬──────────┐
│   网络模式    │ 吞吐量    │ 延迟     │ 隔离性    │ 适用场景  │
├──────────────┼──────────┼──────────┼──────────┼──────────┤
│ host         │ ★★★★★   │ ★★★★★   │ ☆☆☆☆☆   │ 高性能    │
│ bridge       │ ★★★☆☆   │ ★★★☆☆   │ ★★★★☆   │ 通用      │
│ overlay      │ ★★☆☆☆   │ ★★☆☆☆   │ ★★★★★   │ 多主机    │
│ macvlan      │ ★★★★☆   │ ★★★★☆   │ ★★★★★   │ 物理网络  │
│ ipvlan       │ ★★★★☆   │ ★★★★☆   │ ★★★★★   │ 虚拟网络  │
└──────────────┴──────────┴──────────┴──────────┴──────────┘
```

**高性能网络配置 - Host模式**
```yaml
# 适用于高吞吐量应用（如负载均衡器、缓存）
version: '3.8'

services:
  haproxy:
    image: haproxy:2.8-alpine
    network_mode: host  # 直接使用宿主机网络
    volumes:
      - ./haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro
    deploy:
      placement:
        constraints:
          - node.role == worker
          - node.labels.network == high-performance
```

**高性能网络配置 - Macvlan**
```bash
# 创建macvlan网络
docker network create -d macvlan \
  --subnet=192.168.1.0/24 \
  --gateway=192.168.1.1 \
  --ip-range=192.168.1.192/27 \
  -o parent=eth0 \
  macvlan-net

# 使用macvlan网络
docker run -d \
  --name high-perf-app \
  --network macvlan-net \
  --ip 192.168.1.200 \
  myapp:latest

# 验证网络性能
docker exec high-perf-app iperf3 -c 192.168.1.1 -t 30

# 预期结果:接近物理网卡性能
# [ ID] Interval           Transfer     Bandwidth
# [  4]   0.00-30.00  sec  33.2 GBytes  9.50 Gbits/sec
```

### 17.4.2 网络内核参数调优

**系统级网络优化**
```bash
# /etc/sysctl.d/99-docker-network.conf

# ============ TCP连接优化 ============
# 增大连接队列
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 8192

# 快速回收TIME_WAIT连接
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15

# ============ TCP缓冲优化 ============
# 增大TCP接收/发送缓冲区
net.core.rmem_max = 134217728        # 128MB
net.core.wmem_max = 134217728
net.core.rmem_default = 16777216     # 16MB
net.core.wmem_default = 16777216

# TCP自动调优
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
net.ipv4.tcp_mem = 786432 1048576 26777216

# ============ 网络设备队列 ============
# 增大网络设备接收队列
net.core.netdev_max_backlog = 30000

# ============ TCP拥塞控制 ============
# 使用BBR拥塞控制算法
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr

# ============ 连接追踪优化 ============
# 增大conntrack表大小
net.netfilter.nf_conntrack_max = 1048576
net.netfilter.nf_conntrack_tcp_timeout_established = 600

# ============ 其他优化 ============
# 启用TCP Fast Open
net.ipv4.tcp_fastopen = 3

# 禁用TCP时间戳（减少开销）
net.ipv4.tcp_timestamps = 0

# MTU探测
net.ipv4.tcp_mtu_probing = 1
```

**应用配置**
```bash
# 应用到系统
sysctl -p /etc/sysctl.d/99-docker-network.conf

# 验证配置
sysctl net.ipv4.tcp_congestion_control
# net.ipv4.tcp_congestion_control = bbr

sysctl net.core.somaxconn
# net.core.somaxconn = 65535

# 查看TCP连接状态统计
ss -s

# 示例输出
Total: 234
TCP:   180 (estab 95, closed 45, orphaned 2, timewait 40)
```

### 17.4.3 容器网络性能测试

**iperf3网络性能测试**
```bash
# 部署iperf3服务端和客户端
cat > docker-compose-iperf3.yml <<'EOF'
version: '3.8'

services:
  iperf3-server:
    image: networkstatic/iperf3
    command: -s
    networks:
      - perf-test
    ports:
      - "5201:5201"
    deploy:
      replicas: 1

  iperf3-client:
    image: networkstatic/iperf3
    depends_on:
      - iperf3-server
    networks:
      - perf-test
    deploy:
      replicas: 0  # 手动运行

networks:
  perf-test:
    driver: bridge
EOF

docker stack deploy -c docker-compose-iperf3.yml perftest

# 测试1: TCP吞吐量（单线程）
docker run --rm --network perftest_perf-test \
  networkstatic/iperf3 -c iperf3-server -t 30

# 示例输出
[ ID] Interval           Transfer     Bandwidth
[  4]   0.00-30.00  sec  10.2 GBytes  2.92 Gbits/sec

# 测试2: TCP吞吐量（10并发流）
docker run --rm --network perftest_perf-test \
  networkstatic/iperf3 -c iperf3-server -P 10 -t 30

# 测试3: UDP吞吐量
docker run --rm --network perftest_perf-test \
  networkstatic/iperf3 -c iperf3-server -u -b 10G -t 30

# 测试4: 测试延迟
docker run --rm --network perftest_perf-test \
  alpine ping -c 100 iperf3-server

# 计算平均延迟
# rtt min/avg/max/mdev = 0.123/0.156/0.234/0.023 ms
```

**不同网络模式性能对比脚本**
```bash
#!/bin/bash
# network-benchmark.sh - 对比不同网络模式性能

echo "Docker网络模式性能对比测试"
echo "======================================"

# 测试函数
test_network() {
    local mode=$1
    local server_name="iperf-server-$mode"
    local client_cmd="docker run --rm --name iperf-client-$mode"

    echo ""
    echo "测试模式: $mode"
    echo "--------------------------------------"

    # 启动服务端
    case $mode in
        "host")
            docker run -d --name $server_name --network host \
              networkstatic/iperf3 -s
            sleep 2
            $client_cmd --network host \
              networkstatic/iperf3 -c localhost -t 10 | grep receiver
            ;;
        "bridge")
            docker run -d --name $server_name \
              networkstatic/iperf3 -s
            sleep 2
            SERVER_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $server_name)
            $client_cmd --link $server_name \
              networkstatic/iperf3 -c $SERVER_IP -t 10 | grep receiver
            ;;
        "overlay")
            docker network create -d overlay test-overlay
            docker service create --name $server_name \
              --network test-overlay networkstatic/iperf3 -s
            sleep 5
            docker run --rm --network test-overlay \
              networkstatic/iperf3 -c $server_name -t 10 | grep receiver
            docker service rm $server_name
            docker network rm test-overlay
            return
            ;;
    esac

    # 清理
    docker rm -f $server_name >/dev/null 2>&1
}

# 执行测试
test_network "host"
test_network "bridge"
test_network "overlay"

echo ""
echo "======================================"
echo "测试完成"
```

**执行对比测试**
```bash
chmod +x network-benchmark.sh
./network-benchmark.sh

# 预期输出示例
Docker网络模式性能对比测试
======================================

测试模式: host
--------------------------------------
[  4]   0.00-10.00  sec  11.2 GBytes  9.62 Gbits/sec    receiver

测试模式: bridge
--------------------------------------
[  4]   0.00-10.00  sec   3.5 GBytes  3.01 Gbits/sec    receiver

测试模式: overlay
--------------------------------------
[  4]   0.00-10.00  sec   2.1 GBytes  1.80 Gbits/sec    receiver

======================================
结论:
- host模式:    9.62 Gbps (基准)
- bridge模式:  3.01 Gbps (31%性能)
- overlay模式: 1.80 Gbps (19%性能)
```

### 17.4.4 连接池与Keep-Alive优化

**Nginx连接优化**
```nginx
# nginx.conf - 高性能配置

user nginx;
worker_processes auto;  # 自动匹配CPU核心数
worker_rlimit_nofile 65535;

events {
    worker_connections 16384;  # 每个worker最大连接数
    use epoll;                 # 使用epoll事件模型
    multi_accept on;           # 一次接受多个连接
}

http {
    # ============ 连接优化 ============
    keepalive_timeout 65;
    keepalive_requests 1000;   # 单个keep-alive连接最大请求数

    # ============ 上游连接池 ============
    upstream backend {
        server backend1:8080 max_fails=3 fail_timeout=30s;
        server backend2:8080 max_fails=3 fail_timeout=30s;

        # 连接池配置
        keepalive 256;          # 保持256个空闲连接
        keepalive_requests 1000;
        keepalive_timeout 60s;
    }

    server {
        listen 80 reuseport;    # 端口复用

        location / {
            proxy_pass http://backend;

            # 启用HTTP/1.1和Keep-Alive
            proxy_http_version 1.1;
            proxy_set_header Connection "";

            # 连接超时
            proxy_connect_timeout 5s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;

            # 缓冲优化
            proxy_buffering on;
            proxy_buffer_size 8k;
            proxy_buffers 32 8k;
        }
    }
}
```

**数据库连接池配置**
```python
# Python - SQLAlchemy连接池优化

from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# 高并发场景连接池配置
engine = create_engine(
    'postgresql://user:pass@db:5432/mydb',

    # 连接池参数
    poolclass=QueuePool,
    pool_size=20,              # 常驻连接数
    max_overflow=40,           # 峰值额外连接数（总共60）
    pool_pre_ping=True,        # 连接健康检查
    pool_recycle=3600,         # 1小时回收连接
    pool_timeout=30,           # 获取连接超时

    # 连接参数
    connect_args={
        'connect_timeout': 10,
        'application_name': 'myapp',
        'options': '-c statement_timeout=30000'  # 30秒查询超时
    }
)

# 监控连接池状态
from sqlalchemy import event

@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    print(f"新连接建立: {id(dbapi_conn)}")

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    pool = engine.pool
    print(f"连接池状态 - 使用:{pool.checkedout()} 空闲:{pool.size() - pool.checkedout()}")
```

**Redis连接池配置**
```python
# Python - Redis连接池优化

import redis
from redis import ConnectionPool

# 高性能连接池配置
pool = ConnectionPool(
    host='redis',
    port=6379,
    db=0,

    # 连接池参数
    max_connections=100,       # 最大连接数
    socket_timeout=5,          # Socket超时
    socket_connect_timeout=5,  # 连接超时
    socket_keepalive=True,     # 启用TCP Keep-Alive
    socket_keepalive_options={
        socket.TCP_KEEPIDLE: 60,    # 60秒后发送keepalive探测
        socket.TCP_KEEPINTVL: 10,   # 探测间隔10秒
        socket.TCP_KEEPCNT: 3       # 探测3次失败后断开
    },

    # 重试配置
    retry_on_timeout=True,
    health_check_interval=30,  # 30秒健康检查
)

redis_client = redis.Redis(connection_pool=pool)

# 监控连接池
def monitor_redis_pool():
    pool_info = pool.get_connection('_').pool._available_connections
    print(f"Redis连接池 - 可用连接: {len(pool_info)}/{pool.max_connections}")
```

## 17.5 存储性能优化

### 17.5.1 存储驱动选择

**存储驱动性能对比**
```
┌──────────────┬──────────┬──────────┬──────────┬──────────┐
│  存储驱动     │ 读性能    │ 写性能    │ 稳定性    │ 推荐场景  │
├──────────────┼──────────┼──────────┼──────────┼──────────┤
│ overlay2     │ ★★★★☆   │ ★★★★☆   │ ★★★★★   │ 通用      │
│ aufs         │ ★★★☆☆   │ ★★☆☆☆   │ ★★★☆☆   │ 旧内核    │
│ btrfs        │ ★★★☆☆   │ ★★★☆☆   │ ★★★☆☆   │ 快照      │
│ zfs          │ ★★★★☆   │ ★★★★☆   │ ★★★★★   │ 企业级    │
│ devicemapper │ ★★☆☆☆   │ ★★☆☆☆   │ ★★☆☆☆   │ 不推荐    │
└──────────────┴──────────┴──────────┴──────────┴──────────┘
```

**overlay2优化配置**
```json
// /etc/docker/daemon.json

{
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true",
    "overlay2.size=20G"  // 限制单个容器rootfs大小
  ],

  // 数据根目录(选择高性能SSD)
  "data-root": "/mnt/ssd/docker",

  // 日志优化
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

**验证存储驱动**
```bash
# 查看当前存储驱动
docker info | grep "Storage Driver"

# 查看overlay2详细信息
docker info | grep -A 10 "Storage Driver"

# 示例输出
Storage Driver: overlay2
  Backing Filesystem: extfs
  Supports d_type: true
  Native Overlay Diff: true
  userxattr: false
```

### 17.5.2 卷性能优化

**卷类型性能对比**
```yaml
version: '3.8'

services:
  # 场景1: 高性能读写 - 本地卷
  database:
    image: postgres:15
    volumes:
      # 直接挂载宿主机目录(性能最优)
      - type: bind
        source: /mnt/nvme/postgres
        target: /var/lib/postgresql/data
        bind:
          propagation: rprivate
    deploy:
      placement:
        constraints:
          - node.labels.storage == nvme

  # 场景2: 持久化存储 - Docker卷
  app-data:
    image: myapp:latest
    volumes:
      # Docker管理的卷(平衡性能和管理)
      - type: volume
        source: app-data
        target: /data
        volume:
          nocopy: false

  # 场景3: 临时高性能 - tmpfs
  cache:
    image: redis:7-alpine
    volumes:
      # 内存文件系统(最快,但重启丢失)
      - type: tmpfs
        target: /data
        tmpfs:
          size: 4G
          mode: 1777

volumes:
  app-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/ssd/app-data
```

**卷性能测试脚本**
```bash
#!/bin/bash
# benchmark-storage.sh - 存储性能基准测试

IMAGE="alpine:latest"

echo "Docker存储性能测试"
echo "=========================================="

# 测试函数
test_storage() {
    local mount_type=$1
    local mount_opts=$2
    local test_name=$3

    echo ""
    echo "测试: $test_name"
    echo "----------------------------------------"

    # 创建测试容器
    docker run --rm $mount_opts $IMAGE sh -c '
        # 测试1: 顺序写入
        echo "顺序写入 1GB..."
        time dd if=/dev/zero of=/data/test.img bs=1M count=1024 conv=fdatasync

        # 测试2: 随机写入
        echo "随机写入..."
        time dd if=/dev/urandom of=/data/random.img bs=4K count=10000 conv=fdatasync

        # 测试3: 顺序读取
        echo "顺序读取..."
        time dd if=/data/test.img of=/dev/null bs=1M

        # 清理
        rm -f /data/*.img
    ' 2>&1 | grep -E "copied|real"
}

# 测试1: tmpfs (内存)
test_storage "tmpfs" \
  "--tmpfs /data:rw,size=2G,mode=1777" \
  "tmpfs (内存文件系统)"

# 测试2: Docker卷
docker volume create test-vol
test_storage "volume" \
  "-v test-vol:/data" \
  "Docker Volume"
docker volume rm test-vol

# 测试3: Bind挂载
mkdir -p /tmp/docker-bench
test_storage "bind" \
  "-v /tmp/docker-bench:/data" \
  "Bind Mount"
rm -rf /tmp/docker-bench

echo ""
echo "=========================================="
echo "测试完成"
```

**执行存储基准测试**
```bash
chmod +x benchmark-storage.sh
./benchmark-storage.sh

# 预期输出示例
Docker存储性能测试
==========================================

测试: tmpfs (内存文件系统)
----------------------------------------
顺序写入 1GB...
1073741824 bytes (1.1 GB) copied, 0.523 s, 2.1 GB/s
随机写入...
40960000 bytes (41 MB) copied, 0.156 s, 263 MB/s
顺序读取...
1073741824 bytes (1.1 GB) copied, 0.234 s, 4.6 GB/s

测试: Docker Volume
----------------------------------------
顺序写入 1GB...
1073741824 bytes (1.1 GB) copied, 2.345 s, 458 MB/s
随机写入...
40960000 bytes (41 MB) copied, 0.678 s, 60.4 MB/s
顺序读取...
1073741824 bytes (1.1 GB) copied, 1.234 s, 870 MB/s

测试: Bind Mount
----------------------------------------
顺序写入 1GB...
1073741824 bytes (1.1 GB) copied, 2.123 s, 506 MB/s
随机写入...
40960000 bytes (41 MB) copied, 0.589 s, 69.5 MB/s
顺序读取...
1073741824 bytes (1.1 GB) copied, 1.123 s, 956 MB/s
```

### 17.5.3 I/O调度器优化

**查看和设置I/O调度器**
```bash
# 查看当前I/O调度器
cat /sys/block/sda/queue/scheduler
# 输出: [mq-deadline] kyber bfq none

# 不同调度器特点:
# - mq-deadline: 默认,平衡性能和延迟
# - kyber: 优化延迟,适合SSD
# - bfq: 公平队列,适合桌面
# - none: 无调度,适合NVMe SSD

# 为NVMe SSD设置none调度器
echo none > /sys/block/nvme0n1/queue/scheduler

# 为SATA SSD设置kyber调度器
echo kyber > /sys/block/sda/queue/scheduler

# 持久化配置
cat > /etc/udev/rules.d/60-scheduler.rules <<'EOF'
# NVMe设备使用none调度器
ACTION=="add|change", KERNEL=="nvme[0-9]n[0-9]", ATTR{queue/scheduler}="none"

# SSD设备使用kyber调度器
ACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/rotational}=="0", ATTR{queue/scheduler}="kyber"

# HDD设备使用mq-deadline调度器
ACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/rotational}=="1", ATTR{queue/scheduler}="mq-deadline"
EOF

# 应用udev规则
udevadm control --reload-rules
udevadm trigger
```

**I/O队列深度优化**
```bash
# 查看当前队列深度
cat /sys/block/nvme0n1/queue/nr_requests
# 默认: 128

# 增大队列深度(提高吞吐量,略增延迟)
echo 1024 > /sys/block/nvme0n1/queue/nr_requests

# 减小队列深度(降低延迟,略降吞吐量)
echo 64 > /sys/block/nvme0n1/queue/nr_requests

# 查看设备队列统计
cat /sys/block/nvme0n1/queue/iostats
```

### 17.5.4 数据库存储优化案例

**PostgreSQL存储优化**
```yaml
# docker-stack-postgres-optimized.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine

    environment:
      # ============ 内存配置 ============
      POSTGRES_SHARED_BUFFERS: 8GB          # 25%的系统内存
      POSTGRES_EFFECTIVE_CACHE_SIZE: 24GB  # 75%的系统内存
      POSTGRES_WORK_MEM: 64MB               # 每个查询操作内存
      POSTGRES_MAINTENANCE_WORK_MEM: 2GB   # 维护操作内存

      # ============ WAL配置 ============
      POSTGRES_WAL_BUFFERS: 16MB
      POSTGRES_MAX_WAL_SIZE: 4GB
      POSTGRES_MIN_WAL_SIZE: 1GB
      POSTGRES_WAL_COMPRESSION: on

      # ============ 检查点配置 ============
      POSTGRES_CHECKPOINT_COMPLETION_TARGET: 0.9
      POSTGRES_CHECKPOINT_TIMEOUT: 15min

      # ============ I/O优化 ============
      POSTGRES_EFFECTIVE_IO_CONCURRENCY: 200  # SSD推荐值
      POSTGRES_RANDOM_PAGE_COST: 1.1          # SSD推荐1.1

    volumes:
      # 数据目录 - NVMe SSD
      - type: bind
        source: /mnt/nvme/postgres/data
        target: /var/lib/postgresql/data

      # WAL目录 - 单独的高速磁盘
      - type: bind
        source: /mnt/ssd/postgres/wal
        target: /var/lib/postgresql/wal

      # 临时文件 - tmpfs
      - type: tmpfs
        target: /var/lib/postgresql/tmp
        tmpfs:
          size: 4G

    deploy:
      resources:
        limits:
          cpus: '16'
          memory: 32G
        reservations:
          cpus: '8'
          memory: 16G

      placement:
        constraints:
          - node.labels.storage == nvme
          - node.labels.role == database
```

**PostgreSQL自定义配置**
```bash
# custom-postgres.conf - 进一步优化

# ============ 查询规划器 ============
effective_cache_size = '24GB'
random_page_cost = 1.1              # SSD
seq_page_cost = 1.0
cpu_tuple_cost = 0.01
cpu_index_tuple_cost = 0.005
cpu_operator_cost = 0.0025

# ============ 并发配置 ============
max_connections = 200
max_worker_processes = 16
max_parallel_workers_per_gather = 4
max_parallel_workers = 16
max_parallel_maintenance_workers = 4

# ============ WAL性能 ============
wal_level = replica
synchronous_commit = off            # 异步提交,提高性能(可能丢失少量数据)
wal_writer_delay = 200ms
commit_delay = 100
commit_siblings = 5

# ============ 自动清理 ============
autovacuum = on
autovacuum_max_workers = 4
autovacuum_naptime = 10s
autovacuum_vacuum_cost_limit = 1000

# ============ 日志配置 ============
logging_collector = on
log_destination = 'csvlog'
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d.log'
log_min_duration_statement = 100    # 记录>100ms的查询
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
log_temp_files = 0
```

**挂载配置文件**
```yaml
services:
  postgres:
    volumes:
      - ./custom-postgres.conf:/etc/postgresql/postgresql.conf:ro
    command: postgres -c config_file=/etc/postgresql/postgresql.conf
```

## 17.6 应用层优化

### 17.6.1 应用容器化最佳实践

**多阶段构建优化**
```dockerfile
# Dockerfile.optimized - Python Flask应用优化示例

# ============ 阶段1: 构建依赖 ============
FROM python:3.11-slim AS builder

WORKDIR /build

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件(利用缓存)
COPY requirements.txt .

# 安装Python包到独立目录
RUN pip install --user --no-cache-dir --no-warn-script-location \
    -r requirements.txt

# ============ 阶段2: 运行时镜像 ============
FROM python:3.11-slim

# 创建非root用户
RUN groupadd -r app && useradd -r -g app app

WORKDIR /app

# 仅安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制Python包
COPY --from=builder /root/.local /home/app/.local

# 复制应用代码
COPY --chown=app:app . .

# 设置环境变量
ENV PATH=/home/app/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# 切换到非root用户
USER app

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=2)"

# 启动应用
CMD ["gunicorn", "--config", "gunicorn_config.py", "app:app"]
```

**Gunicorn高性能配置**
```python
# gunicorn_config.py

import multiprocessing
import os

# ============ Server Socket ============
bind = "0.0.0.0:8000"
backlog = 2048

# ============ Worker进程 ============
# CPU密集型: workers = CPU核心数
# I/O密集型: workers = 2-4 * CPU核心数
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))

# Worker类型
worker_class = "gevent"  # 或 "sync" / "gthread" / "eventlet"
worker_connections = 1000

# ============ Worker超时 ============
timeout = 30
graceful_timeout = 30
keepalive = 5

# ============ 进程管理 ============
max_requests = 10000        # 处理N个请求后重启worker(防止内存泄漏)
max_requests_jitter = 1000  # 随机抖动
worker_tmp_dir = "/dev/shm" # 使用共享内存

# ============ 日志 ============
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# ============ 性能优化 ============
preload_app = True  # 预加载应用(减少内存,加快启动)

def on_starting(server):
    """服务器启动时"""
    print("Gunicorn正在启动...")

def when_ready(server):
    """服务器就绪时"""
    print(f"Gunicorn已就绪 - Workers: {workers}")

def on_reload(server):
    """代码重载时"""
    print("检测到代码变更,重新加载...")
```

### 17.6.2 缓存策略优化

**多层缓存架构**
```yaml
version: '3.8'

services:
  # ============ L1缓存: 应用内存缓存 ============
  app:
    image: myapp:latest
    environment:
      # Python缓存配置
      CACHE_TYPE: "simple"
      CACHE_DEFAULT_TIMEOUT: 300
    deploy:
      replicas: 4
      resources:
        limits:
          memory: 2G        # 应用内存包含缓存

  # ============ L2缓存: Redis ============
  redis:
    image: redis:7-alpine
    command: >
      redis-server
        --maxmemory 4gb
        --maxmemory-policy allkeys-lru
        --save ""                      # 禁用RDB持久化(纯缓存)
        --appendonly no                # 禁用AOF
        --tcp-backlog 511
        --timeout 0
        --tcp-keepalive 300
        --hz 10                        # 降低内部任务频率
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 5G                   # 4G数据+1G开销
        reservations:
          memory: 4G

  # ============ L3缓存: Nginx缓存 ============
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx-cache.conf:/etc/nginx/conf.d/default.conf:ro
      - nginx-cache:/var/cache/nginx
    deploy:
      resources:
        limits:
          memory: 256M

volumes:
  nginx-cache:
    driver: local
    driver_opts:
      type: tmpfs
      device: tmpfs
      o: size=1G
```

**Nginx缓存配置**
```nginx
# nginx-cache.conf

# 缓存路径配置
proxy_cache_path /var/cache/nginx/api
    levels=1:2
    keys_zone=api_cache:100m
    max_size=1g
    inactive=60m
    use_temp_path=off;

proxy_cache_path /var/cache/nginx/static
    levels=1:2
    keys_zone=static_cache:50m
    max_size=5g
    inactive=7d
    use_temp_path=off;

# 缓存键定义
map $request_method $skip_cache {
    default 1;
    GET 0;
    HEAD 0;
}

server {
    listen 80;

    # ============ API缓存 ============
    location /api/ {
        proxy_pass http://app:8000;

        proxy_cache api_cache;
        proxy_cache_key "$scheme$request_method$host$request_uri";
        proxy_cache_valid 200 5m;
        proxy_cache_valid 404 1m;
        proxy_cache_bypass $skip_cache;
        proxy_no_cache $skip_cache;

        # 缓存头
        add_header X-Cache-Status $upstream_cache_status;

        # 并发控制
        proxy_cache_lock on;
        proxy_cache_lock_timeout 5s;
        proxy_cache_lock_age 10s;

        # 陈旧缓存策略
        proxy_cache_use_stale error timeout updating http_500 http_502 http_503;
        proxy_cache_background_update on;
    }

    # ============ 静态文件缓存 ============
    location /static/ {
        proxy_pass http://app:8000;

        proxy_cache static_cache;
        proxy_cache_valid 200 7d;
        proxy_cache_valid 404 1h;

        add_header X-Cache-Status $upstream_cache_status;
        add_header Cache-Control "public, max-age=604800";
    }
}
```

**Redis缓存模式**
```python
# cache_patterns.py - Redis缓存模式

import redis
import hashlib
import json
from functools import wraps

redis_client = redis.Redis(
    host='redis',
    port=6379,
    db=0,
    decode_responses=True,
    socket_keepalive=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    connection_pool=redis.ConnectionPool(max_connections=50)
)

# ============ 模式1: Cache-Aside (缓存旁路) ============
def cache_aside(key_prefix, ttl=300):
    """装饰器:Cache-Aside模式"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{_generate_key(args, kwargs)}"

            # 1. 尝试从缓存读取
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # 2. 缓存未命中,查询数据库
            result = func(*args, **kwargs)

            # 3. 写入缓存
            redis_client.setex(cache_key, ttl, json.dumps(result))

            return result
        return wrapper
    return decorator

# 使用示例
@cache_aside("user", ttl=600)
def get_user(user_id):
    # 数据库查询
    return db.query(f"SELECT * FROM users WHERE id={user_id}")

# ============ 模式2: Write-Through (写穿透) ============
def write_through(key_prefix):
    """写入时同步更新缓存"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # 同步更新缓存
            cache_key = f"{key_prefix}:{args[0]}"
            redis_client.set(cache_key, json.dumps(result))

            return result
        return wrapper
    return decorator

@write_through("user")
def update_user(user_id, data):
    # 更新数据库
    db.update(f"UPDATE users SET ... WHERE id={user_id}")
    return data

# ============ 模式3: Write-Behind (异步写回) ============
import asyncio
from queue import Queue

write_queue = Queue()

async def async_write_worker():
    """异步写入worker"""
    while True:
        if not write_queue.empty():
            item = write_queue.get()
            # 批量写入数据库
            db.batch_update(item)
        await asyncio.sleep(1)

def write_behind(key_prefix):
    """写入缓存,异步持久化到数据库"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # 立即写入缓存
            cache_key = f"{key_prefix}:{args[0]}"
            redis_client.set(cache_key, json.dumps(result))

            # 加入异步队列
            write_queue.put((args[0], result))

            return result
        return wrapper
    return decorator

# ============ 辅助函数 ============
def _generate_key(args, kwargs):
    """生成缓存键"""
    key_data = f"{args}:{sorted(kwargs.items())}"
    return hashlib.md5(key_data.encode()).hexdigest()

# ============ 缓存预热 ============
def warm_cache(keys_list):
    """批量预热缓存"""
    pipeline = redis_client.pipeline()

    for key in keys_list:
        data = fetch_from_db(key)
        pipeline.setex(f"user:{key}", 600, json.dumps(data))

    pipeline.execute()
    print(f"预热了 {len(keys_list)} 个缓存键")

# ============ 缓存失效策略 ============
def invalidate_cache_pattern(pattern):
    """批量删除匹配的缓存"""
    cursor = 0
    while True:
        cursor, keys = redis_client.scan(
            cursor, match=pattern, count=100
        )
        if keys:
            redis_client.delete(*keys)
        if cursor == 0:
            break

# 示例:删除所有用户缓存
invalidate_cache_pattern("user:*")
```

### 17.6.3 异步处理与队列优化

**Celery异步任务队列**
```yaml
# docker-stack-celery.yml
version: '3.8'

services:
  # ============ Web应用 ============
  web:
    image: myapp:latest
    environment:
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/1
    deploy:
      replicas: 4

  # ============ Celery Worker ============
  celery-worker:
    image: myapp:latest
    command: celery -A tasks worker --loglevel=info --concurrency=8
    environment:
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/1
      CELERYD_PREFETCH_MULTIPLIER: 4   # 每个worker预取4个任务
      CELERYD_MAX_TASKS_PER_CHILD: 1000  # 处理1000个任务后重启
    deploy:
      replicas: 4
      resources:
        limits:
          cpus: '2'
          memory: 2G

  # ============ Celery Beat (定时任务) ============
  celery-beat:
    image: myapp:latest
    command: celery -A tasks beat --loglevel=info
    environment:
      CELERY_BROKER_URL: redis://redis:6379/0
    deploy:
      replicas: 1

  # ============ Flower (监控) ============
  flower:
    image: mher/flower:latest
    command: celery --broker=redis://redis:6379/0 flower --port=5555
    ports:
      - "5555:5555"
    deploy:
      replicas: 1

networks:
  default:
    driver: overlay
```

**Celery任务优化**
```python
# tasks.py - Celery任务优化

from celery import Celery, group, chord, chain
from celery.exceptions import SoftTimeLimitExceeded
import time

app = Celery('tasks')

# ============ 配置优化 ============
app.conf.update(
    # Broker设置
    broker_url='redis://redis:6379/0',
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,

    # Result Backend
    result_backend='redis://redis:6379/1',
    result_expires=3600,  # 结果保留1小时

    # 任务执行
    task_acks_late=True,              # 任务完成后才确认
    task_reject_on_worker_lost=True,  # Worker丢失时拒绝任务
    task_time_limit=600,              # 硬超时10分钟
    task_soft_time_limit=540,         # 软超时9分钟

    # 性能优化
    worker_prefetch_multiplier=4,     # 预取倍数
    worker_max_tasks_per_child=1000,  # 防止内存泄漏

    # 序列化
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',

    # 路由
    task_routes={
        'tasks.cpu_intensive': {'queue': 'cpu'},
        'tasks.io_intensive': {'queue': 'io'},
    }
)

# ============ 任务示例 ============
@app.task(bind=True, max_retries=3)
def process_data(self, data_id):
    """带重试的任务"""
    try:
        # 模拟处理
        result = heavy_computation(data_id)
        return result

    except SoftTimeLimitExceeded:
        # 软超时处理
        cleanup()
        raise

    except Exception as exc:
        # 指数退避重试
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

@app.task
def cpu_intensive_task(data):
    """CPU密集型任务"""
    return sum(i**2 for i in range(data))

@app.task(queue='io')
def io_intensive_task(url):
    """I/O密集型任务"""
    import requests
    return requests.get(url).text

# ============ 任务编排 ============
# 并行任务组
job = group(
    process_data.s(1),
    process_data.s(2),
    process_data.s(3)
)
result = job.apply_async()

# 链式任务
job = chain(
    fetch_data.s(),
    process_data.s(),
    save_result.s()
)
result = job.apply_async()

# Chord (分散-聚合)
callback = aggregate_results.s()
header = [process_data.s(i) for i in range(100)]
job = chord(header)(callback)
result = job.apply_async()

# ============ 任务优先级 ============
@app.task
def high_priority_task():
    pass

# 发送高优先级任务
high_priority_task.apply_async(priority=9)  # 0-9,9最高
```

**RabbitMQ高性能配置**
```yaml
# 如果使用RabbitMQ而非Redis
services:
  rabbitmq:
    image: rabbitmq:3.12-management-alpine
    hostname: rabbitmq
    environment:
      RABBITMQ_DEFAULT_USER: admin
      RABBITMQ_DEFAULT_PASS: secret

      # 性能优化
      RABBITMQ_VM_MEMORY_HIGH_WATERMARK: 0.6        # 60%内存阈值
      RABBITMQ_DISK_FREE_LIMIT: "2GB"
      RABBITMQ_CHANNEL_MAX: 2048

    volumes:
      - rabbitmq-data:/var/lib/rabbitmq
      - ./rabbitmq.conf:/etc/rabbitmq/rabbitmq.conf:ro
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
        reservations:
          memory: 2G

volumes:
  rabbitmq-data:
```

**rabbitmq.conf高级配置**
```ini
# rabbitmq.conf - 高性能配置

# ============ 网络配置 ============
listeners.tcp.default = 5672
management.tcp.port = 15672

# ============ 内存管理 ============
vm_memory_high_watermark.relative = 0.6
vm_memory_high_watermark_paging_ratio = 0.75

# ============ 磁盘管理 ============
disk_free_limit.absolute = 2GB

# ============ 连接配置 ============
channel_max = 2048
heartbeat = 60

# ============ 队列配置 ============
# 延迟队列
queue_master_locator = min-masters

# ============ 集群配置 ============
cluster_partition_handling = autoheal

# ============ 日志 ============
log.file.level = warning
log.console = true
log.console.level = info
```

---

*（第17章完成,约2000行。已完成17章,剩余2章...）*

---

# 第18章: 故障排查

## 18.1 故障排查方法论

### 18.1.1 系统化排查流程

**5步故障排查法**
```
┌─────────────────────────────────────────────────────────┐
│               Docker故障排查标准流程                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [1] 问题定义 (Define)                                   │
│      ├─ 现象描述 (What)                                  │
│      ├─ 发生时间 (When)                                  │
│      ├─ 影响范围 (Scope)                                 │
│      └─ 业务影响 (Impact)                                │
│                                                         │
│  [2] 信息收集 (Gather)                                   │
│      ├─ 容器状态 (docker ps/inspect)                     │
│      ├─ 系统资源 (CPU/内存/磁盘/网络)                     │
│      ├─ 日志信息 (应用日志/系统日志)                      │
│      └─ 监控数据 (Prometheus/Grafana)                    │
│                                                         │
│  [3] 假设验证 (Hypothesize)                              │
│      ├─ 列出可能原因                                      │
│      ├─ 按概率排序                                        │
│      └─ 逐一验证假设                                      │
│                                                         │
│  [4] 问题定位 (Isolate)                                  │
│      ├─ 缩小问题范围                                      │
│      ├─ 找到根本原因                                      │
│      └─ 确认触发条件                                      │
│                                                         │
│  [5] 解决验证 (Resolve)                                  │
│      ├─ 实施解决方案                                      │
│      ├─ 验证问题解决                                      │
│      ├─ 文档记录                                          │
│      └─ 预防措施                                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**故障排查决策树**
```
容器无法访问
    │
    ├─> 容器是否运行? (docker ps)
    │   ├─ 否 → 18.2.1 容器启动失败
    │   └─ 是 → 继续
    │
    ├─> 容器健康检查? (docker inspect)
    │   ├─ 失败 → 18.2.2 健康检查失败
    │   └─ 通过 → 继续
    │
    ├─> 端口是否监听? (netstat/ss)
    │   ├─ 否 → 应用未启动
    │   └─ 是 → 继续
    │
    ├─> 网络连通性? (ping/telnet)
    │   ├─ 否 → 18.3 网络问题
    │   └─ 是 → 继续
    │
    └─> 应用响应? (curl/http请求)
        ├─ 超时 → 18.4 性能问题
        ├─ 错误 → 18.2.4 应用错误
        └─ 正常 → 负载均衡器/DNS问题
```

### 18.1.2 快速诊断工具箱

**一键诊断脚本**
```bash
#!/bin/bash
# docker-diagnose.sh - Docker快速诊断工具

CONTAINER=$1

if [ -z "$CONTAINER" ]; then
    echo "用法: $0 <容器名称或ID>"
    exit 1
fi

echo "=========================================="
echo "Docker容器快速诊断: $CONTAINER"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# 1. 容器基本状态
echo -e "\n[1] 容器状态"
echo "----------------------------------------"
docker ps -a --filter "name=$CONTAINER" --format \
  "状态: {{.Status}}\n创建: {{.CreatedAt}}\n镜像: {{.Image}}\n端口: {{.Ports}}"

# 2. 容器详细信息
echo -e "\n[2] 容器配置"
echo "----------------------------------------"
docker inspect $CONTAINER | jq -r '
  .[0] | {
    "运行状态": .State.Status,
    "启动时间": .State.StartedAt,
    "退出代码": .State.ExitCode,
    "OOM被杀": .State.OOMKilled,
    "重启次数": .RestartCount,
    "IP地址": .NetworkSettings.IPAddress,
    "网络模式": .HostConfig.NetworkMode,
    "CPU配额": .HostConfig.CpuQuota,
    "内存限制": .HostConfig.Memory
  }
' | column -t -s ':'

# 3. 资源使用情况
echo -e "\n[3] 资源使用"
echo "----------------------------------------"
docker stats $CONTAINER --no-stream --format \
  "CPU: {{.CPUPerc}}\n内存: {{.MemUsage}} ({{.MemPerc}})\n网络: {{.NetIO}}\n磁盘: {{.BlockIO}}"

# 4. 容器进程
echo -e "\n[4] 容器进程"
echo "----------------------------------------"
docker top $CONTAINER

# 5. 最近日志(最后50行)
echo -e "\n[5] 最近日志(最后50行)"
echo "----------------------------------------"
docker logs --tail 50 $CONTAINER 2>&1 | tail -20

# 6. 健康检查
echo -e "\n[6] 健康检查"
echo "----------------------------------------"
docker inspect $CONTAINER | jq -r '
  .[0].State.Health // "未配置健康检查" |
  if type == "object" then
    "状态: " + .Status + "\n" +
    "失败次数: " + (.FailingStreak | tostring) + "\n" +
    "最后检查: " + (.Log[-1].Start // "N/A")
  else . end
'

# 7. 网络连接
echo -e "\n[7] 网络连接"
echo "----------------------------------------"
docker exec $CONTAINER sh -c 'netstat -tunlp 2>/dev/null || ss -tunlp' 2>/dev/null | head -10 || echo "无法获取网络信息"

# 8. 磁盘使用
echo -e "\n[8] 磁盘使用"
echo "----------------------------------------"
docker exec $CONTAINER df -h 2>/dev/null | grep -E "Filesystem|/$" || echo "无法获取磁盘信息"

# 9. 相关事件
echo -e "\n[9] 容器事件(最近10条)"
echo "----------------------------------------"
docker events --filter "container=$CONTAINER" --since 1h --until 0s 2>/dev/null | tail -10 || echo "无近期事件"

# 10. 建议操作
echo -e "\n[10] 诊断建议"
echo "----------------------------------------"

# 检查容器状态
STATUS=$(docker inspect -f '{{.State.Status}}' $CONTAINER)
if [ "$STATUS" != "running" ]; then
    echo "⚠️  容器未运行,建议:"
    echo "   1. 查看退出原因: docker logs $CONTAINER"
    echo "   2. 检查启动命令: docker inspect $CONTAINER | jq '.[0].Config.Cmd'"
    echo "   3. 尝试重启: docker start $CONTAINER"
fi

# 检查OOM
OOM=$(docker inspect -f '{{.State.OOMKilled}}' $CONTAINER)
if [ "$OOM" = "true" ]; then
    echo "⚠️  检测到OOM Killer,建议:"
    echo "   1. 增加内存限制: docker update --memory 2g $CONTAINER"
    echo "   2. 分析内存使用: docker stats $CONTAINER"
    echo "   3. 检查应用内存泄漏"
fi

# 检查重启次数
RESTART_COUNT=$(docker inspect -f '{{.RestartCount}}' $CONTAINER)
if [ "$RESTART_COUNT" -gt 5 ]; then
    echo "⚠️  容器频繁重启($RESTART_COUNT次),建议:"
    echo "   1. 查看启动日志: docker logs $CONTAINER"
    echo "   2. 检查健康检查配置"
    echo "   3. 验证依赖服务是否正常"
fi

echo -e "\n=========================================="
echo "诊断完成"
echo "=========================================="
```

**执行快速诊断**
```bash
chmod +x docker-diagnose.sh
./docker-diagnose.sh my-app

# 示例输出(部分)
==========================================
Docker容器快速诊断: my-app
时间: 2025-12-10 14:30:00
==========================================

[1] 容器状态
----------------------------------------
状态: Up 2 hours
创建: 2025-12-10 12:30:00
镜像: myapp:latest
端口: 0.0.0.0:8080->8080/tcp

[3] 资源使用
----------------------------------------
CPU: 45.23%
内存: 1.2GiB / 2GiB (60%)
网络: 1.2MB / 3.4MB
磁盘: 45MB / 12MB

[10] 诊断建议
----------------------------------------
⚠️  容器频繁重启(8次),建议:
   1. 查看启动日志: docker logs my-app
   2. 检查健康检查配置
   3. 验证依赖服务是否正常
```

## 18.2 容器故障排查

### 18.2.1 容器无法启动

**问题场景1: 镜像拉取失败**
```bash
# 症状
docker run myapp:latest
# Unable to find image 'myapp:latest' locally
# Error response from daemon: pull access denied for myapp

# 排查步骤
# 1. 检查镜像是否存在
docker images | grep myapp

# 2. 检查镜像仓库连接
docker login registry.example.com
# 输入用户名密码

# 3. 手动拉取镜像
docker pull registry.example.com/myapp:latest

# 4. 使用完整镜像名
docker run registry.example.com/myapp:latest

# 5. 检查网络连接
curl -I https://registry.example.com
ping registry.example.com

# 解决方案
# A. 配置镜像仓库认证
cat > ~/.docker/config.json <<EOF
{
  "auths": {
    "registry.example.com": {
      "auth": "base64(username:password)"
    }
  }
}
EOF

# B. 使用本地构建
docker build -t myapp:latest .

# C. 配置镜像加速器
cat > /etc/docker/daemon.json <<EOF
{
  "registry-mirrors": [
    "https://mirror.example.com"
  ]
}
EOF
systemctl restart docker
```

**问题场景2: 端口冲突**
```bash
# 症状
docker run -d -p 8080:8080 myapp
# Error: Bind for 0.0.0.0:8080 failed: port is already allocated

# 排查步骤
# 1. 查看端口占用
netstat -tunlp | grep 8080
# 或
ss -tunlp | grep 8080
# 或
lsof -i :8080

# 示例输出
tcp  0  0  0.0.0.0:8080  0.0.0.0:*  LISTEN  12345/docker-proxy

# 2. 查找占用端口的容器
docker ps --format "{{.ID}}\t{{.Ports}}" | grep 8080

# 3. 停止冲突的容器
docker stop <container_id>

# 解决方案
# A. 使用不同端口
docker run -d -p 8081:8080 myapp

# B. 停止占用端口的服务
systemctl stop apache2  # 如果是系统服务

# C. 使用动态端口分配
docker run -d -p 8080 myapp  # Docker自动分配宿主机端口
docker port <container_id>   # 查看分配的端口
```

**问题场景3: 资源不足**
```bash
# 症状
docker run -d --memory 16g myapp
# Error: Cannot start container: not enough memory

# 排查步骤
# 1. 检查系统可用内存
free -h
#               total        used        free      shared  buff/cache   available
# Mem:           15Gi       12Gi        500Mi       100Mi        2.5Gi        2.5Gi

# 2. 检查Docker资源使用
docker stats --no-stream

# 3. 检查磁盘空间
df -h
docker system df

# 示例输出
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          25        10        8.5GB     4.2GB (49%)
Containers      15        10        2.1GB     500MB (23%)
Local Volumes   5         3         1.2GB     800MB (66%)

# 解决方案
# A. 降低资源限制
docker run -d --memory 4g myapp

# B. 清理未使用资源
docker system prune -a --volumes
# 警告: 会删除所有未使用的镜像、容器、网络、卷

# C. 增加系统资源
# - 增加物理内存
# - 调整swap大小
dd if=/dev/zero of=/swapfile bs=1G count=8
mkswap /swapfile
swapon /swapfile

# D. 迁移到资源充足的节点(Swarm)
docker service update --constraint-add node.labels.size==large myapp
```

**问题场景4: 依赖服务未就绪**
```bash
# 症状
docker logs myapp
# Error: connection refused to database:5432
# Container exits immediately after start

# 排查步骤
# 1. 检查依赖服务状态
docker ps | grep database

# 2. 测试连接
docker run --rm --network myapp_network \
  alpine sh -c 'nc -zv database 5432'

# 3. 查看容器启动顺序
docker-compose ps

# 解决方案
# A. 使用depends_on + 健康检查
version: '3.8'
services:
  database:
    image: postgres:15
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  app:
    image: myapp:latest
    depends_on:
      database:
        condition: service_healthy

# B. 应用内实现重试逻辑
import time
import psycopg2

def connect_db(max_retries=30, delay=2):
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                host="database",
                port=5432,
                user="postgres"
            )
            return conn
        except psycopg2.OperationalError:
            if i < max_retries - 1:
                print(f"数据库连接失败,{delay}秒后重试... ({i+1}/{max_retries})")
                time.sleep(delay)
            else:
                raise

# C. 使用wait-for-it脚本
#!/bin/bash
# wait-for-it.sh
set -e

host="$1"
shift
cmd="$@"

until nc -z "$host" 5432; do
  echo "等待 $host:5432..."
  sleep 1
done

echo "$host:5432 已就绪"
exec $cmd

# Dockerfile
COPY wait-for-it.sh /usr/local/bin/
ENTRYPOINT ["wait-for-it.sh", "database:5432", "--"]
CMD ["python", "app.py"]
```

### 18.2.2 容器异常退出

**退出代码分析**
```bash
# 查看容器退出代码
docker inspect -f '{{.State.ExitCode}}' myapp

# 常见退出代码含义
# 0    : 正常退出
# 1    : 应用错误(通用错误)
# 125  : Docker守护进程错误
# 126  : 命令无法执行
# 127  : 命令未找到
# 128+n: 信号终止(n为信号编号)
#   137 = 128 + 9 (SIGKILL,强制杀死)
#   139 = 128 + 11 (SIGSEGV,段错误)
#   143 = 128 + 15 (SIGTERM,正常终止)
```

**场景1: OOM Killer**
```bash
# 症状
docker inspect -f '{{.State.OOMKilled}}' myapp
# true

docker logs myapp
# (无输出或突然中断)

# 查看系统日志
dmesg | grep -i "out of memory"
journalctl -k | grep -i "killed process"

# 示例输出
[12345.678] Out of memory: Killed process 23456 (java) total-vm:4194304kB

# 排查步骤
# 1. 查看内存限制
docker inspect myapp | jq '.[0].HostConfig.Memory'

# 2. 查看实际内存使用
docker stats myapp --no-stream

# 3. 分析内存趋势
# 使用cAdvisor或Prometheus查看历史数据

# 解决方案
# A. 增加内存限制
docker update --memory 4g --memory-swap 6g myapp

# B. 调整OOM优先级
docker update --oom-score-adj -500 myapp  # 降低被杀概率

# C. 优化应用内存使用
# Java应用
docker run -e JAVA_OPTS="-Xms1g -Xmx2g -XX:+UseG1GC" myapp

# D. 启用Swap(谨慎使用)
docker run --memory 2g --memory-swap 4g myapp
```

**场景2: 应用崩溃**
```bash
# 症状
docker logs myapp
# Traceback (most recent call last):
#   File "app.py", line 42
#     result = process_data(None)
# AttributeError: 'NoneType' object has no attribute 'split'

# 排查步骤
# 1. 查看完整日志
docker logs --tail 200 myapp > myapp.log

# 2. 进入容器调试(如果可以启动)
docker run -it --entrypoint /bin/bash myapp

# 3. 检查配置文件
docker exec myapp cat /app/config.yaml

# 4. 查看环境变量
docker exec myapp env

# 解决方案
# A. 修复代码bug
def process_data(data):
    if data is None:
        raise ValueError("data cannot be None")
    return data.split(',')

# B. 添加异常处理
try:
    result = process_data(data)
except Exception as e:
    logger.error(f"处理失败: {e}")
    # 优雅降级或返回默认值

# C. 重新构建镜像
docker build -t myapp:latest .
docker service update --image myapp:latest myapp
```

**场景3: 健康检查失败**
```bash
# 症状
docker ps
# STATUS: Up 5 minutes (unhealthy)

docker inspect myapp | jq '.[0].State.Health.Log[-3:]'
# [
#   {
#     "Start": "2025-12-10T14:30:00Z",
#     "End": "2025-12-10T14:30:03Z",
#     "ExitCode": 1,
#     "Output": "HTTP/1.1 503 Service Unavailable"
#   }
# ]

# 排查步骤
# 1. 手动执行健康检查命令
docker exec myapp curl -f http://localhost:8080/health

# 2. 查看应用日志
docker logs myapp | grep -i "health"

# 3. 检查健康检查配置
docker inspect myapp | jq '.[0].Config.Healthcheck'

# 解决方案
# A. 调整健康检查参数
# Dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# B. 修复健康检查端点
@app.route('/health')
def health():
    # 检查关键依赖
    try:
        db.execute("SELECT 1")
        redis.ping()
        return jsonify({"status": "healthy"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 503

# C. 增加启动时间(start-period)
docker run --health-cmd="curl -f http://localhost:8080/health" \
           --health-interval=30s \
           --health-start-period=120s \
           myapp

# D. 禁用健康检查(临时调试)
docker run --no-healthcheck myapp
```

### 18.2.3 容器性能问题

**场景1: CPU使用率100%**
```bash
# 症状
docker stats myapp
# CPU %: 399.5%  (4核心全部跑满)

# 排查步骤
# 1. 查看容器内进程
docker top myapp

# 2. 进入容器使用top
docker exec -it myapp top

# 3. CPU profiling
# 获取容器PID
PID=$(docker inspect -f '{{.State.Pid}}' myapp)

# 使用perf分析
perf record -F 99 -p $PID -g -- sleep 30
perf report

# 或使用py-spy(Python)
docker exec myapp pip install py-spy
docker exec myapp py-spy top --pid 1

# 4. 查看慢查询
docker exec myapp-db psql -c "
  SELECT query, calls, total_time, mean_time
  FROM pg_stat_statements
  ORDER BY total_time DESC
  LIMIT 10;
"

# 解决方案
# A. 优化代码热点
# 使用缓存减少计算
# 异步处理耗时操作
# 优化算法复杂度

# B. 增加CPU配额
docker update --cpus 8 myapp

# C. 横向扩展
docker service scale myapp=4

# D. 限制并发
# Gunicorn
workers = 4  # 降低worker数量
threads = 2
worker_class = "gthread"

# E. 限流
from flask_limiter import Limiter

limiter = Limiter(
    app,
    default_limits=["100 per minute"]
)
```

**场景2: 内存持续增长**
```bash
# 症状
docker stats myapp
# 内存使用持续增长: 500MB -> 1GB -> 1.5GB -> ...

# 排查步骤
# 1. 监控内存趋势
watch -n 5 'docker stats myapp --no-stream'

# 2. 查看进程内存分布
docker exec myapp cat /proc/1/status | grep -i mem

# 3. Python内存分析
docker exec myapp pip install memory_profiler
docker exec myapp python -m memory_profiler app.py

# 4. Java堆分析
docker exec myapp jmap -heap 1
docker exec myapp jmap -dump:file=/tmp/heap.hprof 1
docker cp myapp:/tmp/heap.hprof .
# 使用MAT分析

# 5. 检查缓存大小
docker exec myapp-redis redis-cli info memory

# 解决方案
# A. 查找内存泄漏
# Python
import tracemalloc

tracemalloc.start()

# ... 运行一段时间 ...

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

for stat in top_stats[:10]:
    print(stat)

# B. 限制缓存大小
from functools import lru_cache

@lru_cache(maxsize=1000)  # 最多缓存1000条
def expensive_function(param):
    pass

# C. 定期重启worker
# Gunicorn
max_requests = 10000
max_requests_jitter = 1000

# D. 配置GC
# Java
JAVA_OPTS="-Xms2g -Xmx2g -XX:+UseG1GC -XX:MaxGCPauseMillis=200"

# E. 增加内存限制(最后手段)
docker update --memory 4g myapp
```

**场景3: 磁盘IO瓶颈**
```bash
# 症状
docker stats myapp
# BLOCK I/O: 1.2GB / 3.4GB (持续高IO)

# 应用响应缓慢,尤其是数据库操作

# 排查步骤
# 1. 查看IO统计
iostat -x 1 10

# 示例输出
Device    r/s     w/s   rkB/s   wkB/s  await  %util
sda      150.0   300.0  6000    12000  25.5   98.0

# 2. 查看容器IO
docker stats myapp --no-stream --format \
  "{{.Container}}: {{.BlockIO}}"

# 3. 查找IO热点进程
iotop -o  # 仅显示有IO的进程

# 4. 数据库慢查询
docker exec postgres-db psql -c "
  SELECT * FROM pg_stat_activity
  WHERE state = 'active'
  AND query_start < NOW() - INTERVAL '5 seconds';
"

# 解决方案
# A. 优化存储驱动
# 确保使用overlay2
docker info | grep "Storage Driver"

# B. 使用更快的存储
# 迁移到SSD/NVMe
# 使用tmpfs for临时数据
docker run -v type=tmpfs,target=/tmp,tmpfs-size=1G myapp

# C. 调整IO调度器
echo none > /sys/block/nvme0n1/queue/scheduler

# D. 数据库优化
# PostgreSQL
shared_buffers = 8GB
effective_cache_size = 24GB
random_page_cost = 1.1  # SSD
checkpoint_completion_target = 0.9

# E. 应用层优化
# 批量操作
# 减少数据库查询
# 使用索引
# 启用查询缓存
```

### 18.2.4 数据持久化问题

**场景1: 数据丢失**
```bash
# 症状
# 容器重启后数据丢失

# 排查步骤
# 1. 检查卷挂载
docker inspect myapp | jq '.[0].Mounts'

# 2. 验证数据位置
docker exec myapp ls -la /var/lib/mysql

# 3. 检查卷是否存在
docker volume ls | grep myapp

# 解决方案
# A. 正确挂载卷
docker run -v myapp-data:/var/lib/mysql mysql:8

# B. 使用bind mount
docker run -v /data/mysql:/var/lib/mysql mysql:8

# C. Docker Compose
version: '3.8'
services:
  db:
    image: mysql:8
    volumes:
      - db-data:/var/lib/mysql

volumes:
  db-data:
    driver: local
```

**场景2: 权限问题**
```bash
# 症状
docker logs myapp
# Permission denied: '/data/app.log'

# 排查步骤
# 1. 检查文件权限
docker exec myapp ls -la /data

# 2. 检查容器运行用户
docker inspect myapp | jq '.[0].Config.User'

# 3. 检查宿主机权限
ls -la /mnt/data

# 解决方案
# A. 修改宿主机权限
sudo chown -R 1000:1000 /mnt/data

# B. 以root运行(不推荐)
docker run --user root myapp

# C. Dockerfile指定用户
FROM python:3.11-slim

RUN groupadd -r app && useradd -r -g app app

WORKDIR /app
COPY --chown=app:app . .

USER app
CMD ["python", "app.py"]

# D. init容器修复权限
docker run --rm -v myapp-data:/data \
  busybox chown -R 1000:1000 /data
```

## 18.3 网络故障排查

### 18.3.1 容器间网络不通

**排查工具箱**
```bash
# 安装网络调试工具
docker run -it --rm --network myapp_network \
  nicolaka/netshoot

# 工具包含:
# - ping, traceroute, mtr
# - curl, wget, httpie
# - netstat, ss, lsof
# - tcpdump, nmap
# - dig, nslookup, host
# - iperf3
```

**场景1: DNS解析失败**
```bash
# 症状
docker exec app curl database:5432
# curl: (6) Could not resolve host: database

# 排查步骤
# 1. 测试DNS解析
docker exec app nslookup database

# 2. 检查DNS配置
docker exec app cat /etc/resolv.conf

# 3. 检查网络连接
docker inspect app | jq '.[0].NetworkSettings.Networks'

# 4. 验证服务发现
docker network inspect myapp_network | jq '.[0].Containers'

# 解决方案
# A. 确保在同一网络
docker network connect myapp_network app

# B. 使用IP地址(临时)
DATABASE_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' database)
docker exec app curl $DATABASE_IP:5432

# C. 配置自定义DNS
docker run --dns 8.8.8.8 --dns 8.8.4.4 myapp

# D. 检查Docker DNS服务
docker exec app cat /etc/resolv.conf
# nameserver 127.0.0.11  # Docker内置DNS

# 验证内置DNS
docker exec app nslookup database 127.0.0.11
```

**场景2: 端口不通**
```bash
# 症状
docker exec app curl database:5432
# curl: (7) Failed to connect to database port 5432: Connection refused

# 排查步骤
# 1. 检查端口监听
docker exec database netstat -tunlp | grep 5432

# 或
docker exec database ss -tunlp | grep 5432

# 2. 测试端口连通性
docker exec app nc -zv database 5432
# Connection to database 5432 port [tcp/postgresql] succeeded!

# 或使用telnet
docker exec app telnet database 5432

# 3. 检查防火墙规则
iptables -L -n | grep 5432

# 4. 抓包分析
docker exec app tcpdump -i eth0 port 5432

# 解决方案
# A. 确认应用监听正确地址
# 不要监听localhost,要监听0.0.0.0
bind = "0.0.0.0:5432"  # 正确
bind = "127.0.0.1:5432"  # 错误,只能容器内访问

# B. 检查防火墙
# Docker自动配置iptables,一般不需要手动配置

# C. 验证服务启动
docker exec database ps aux | grep postgres
```

**场景3: 网络策略限制**
```bash
# 症状(使用Swarm网络策略时)
# 部分容器可以访问,部分不能

# 排查步骤
# 1. 查看网络策略
docker network inspect myapp_network

# 2. 测试连通性矩阵
for service in app1 app2 app3; do
  echo "测试 $service:"
  docker exec $service curl -s -o /dev/null -w "%{http_code}" database:5432
done

# 解决方案
# A. 使用overlay网络(Swarm)
docker network create --driver overlay myapp_network

# B. 确保服务在同一网络
docker service update --network-add myapp_network app

# C. 使用服务名而非容器名
curl database:5432  # 正确(服务名)
curl database.1.abc123:5432  # 错误(容器名)
```

### 18.3.2 外部访问不通

**场景1: 端口映射问题**
```bash
# 症状
curl http://localhost:8080
# curl: (7) Failed to connect to localhost port 8080

# 排查步骤
# 1. 检查端口映射
docker ps --format "{{.Names}}: {{.Ports}}"

# 2. 检查端口监听
netstat -tunlp | grep 8080
ss -tunlp | grep 8080

# 3. 测试从宿主机访问
curl http://localhost:8080
curl http://127.0.0.1:8080
curl http://$(hostname -I | awk '{print $1}'):8080

# 4. 检查防火墙
iptables -L -n -v | grep 8080
firewall-cmd --list-all

# 解决方案
# A. 正确的端口映射格式
docker run -p 8080:80 nginx  # 宿主机8080 -> 容器80

# B. 绑定所有接口
docker run -p 0.0.0.0:8080:80 nginx

# C. 开放防火墙端口
firewall-cmd --add-port=8080/tcp --permanent
firewall-cmd --reload

# D. 检查Docker iptables规则
iptables -t nat -L -n | grep 8080
```

**场景2: Swarm路由网格问题**
```bash
# 症状
# 某些节点可以访问服务,某些不能

# 排查步骤
# 1. 检查服务发布端口
docker service inspect myapp | jq '.[0].Endpoint.Ports'

# 2. 测试每个节点
for node in node1 node2 node3; do
  echo "测试 $node:"
  ssh $node "curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8080"
done

# 3. 检查ingress网络
docker network inspect ingress

# 4. 查看节点可用性
docker node ls

# 解决方案
# A. 重建ingress网络
docker network rm ingress
docker network create \
  --driver overlay \
  --ingress \
  --subnet=10.0.0.0/24 \
  --gateway=10.0.0.1 \
  ingress

# B. 检查节点防火墙
# 确保以下端口开放:
# - 2377/tcp (cluster management)
# - 7946/tcp+udp (container network discovery)
# - 4789/udp (overlay network traffic)

# C. 服务使用host模式
docker service create --mode global --publish mode=host,target=80,published=8080 nginx
```

## 18.4 日志分析与调试

### 18.4.1 日志收集技巧

**结构化日志查询**
```bash
# 按时间范围
docker logs --since "2025-12-10T14:00:00" --until "2025-12-10T15:00:00" myapp

# 按时间相对值
docker logs --since 1h myapp  # 最近1小时
docker logs --since 30m myapp  # 最近30分钟

# 实时跟踪
docker logs -f myapp

# 只看最新N行
docker logs --tail 100 myapp

# 包含时间戳
docker logs -t myapp

# 过滤关键字
docker logs myapp 2>&1 | grep -i error
docker logs myapp 2>&1 | grep -E "(ERROR|WARN|FATAL)"

# 统计错误数量
docker logs myapp 2>&1 | grep -c ERROR

# 保存到文件
docker logs myapp > myapp_$(date +%Y%m%d_%H%M%S).log
```

**多容器日志聚合**
```bash
#!/bin/bash
# collect-logs.sh - 收集所有服务日志

SERVICES=$(docker service ls --format "{{.Name}}")
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="logs_$TIMESTAMP"

mkdir -p $LOG_DIR

for service in $SERVICES; do
    echo "收集 $service 日志..."

    # 获取服务的所有任务
    TASKS=$(docker service ps $service --format "{{.Name}}.{{.ID}}" --filter "desired-state=running")

    for task in $TASKS; do
        CONTAINER=$(docker ps --filter "name=$task" --format "{{.ID}}")
        if [ -n "$CONTAINER" ]; then
            docker logs $CONTAINER > "$LOG_DIR/${service}_${CONTAINER:0:12}.log" 2>&1
            echo "  ✓ $CONTAINER"
        fi
    done
done

# 打包
tar -czf logs_$TIMESTAMP.tar.gz $LOG_DIR
echo "日志已保存到: logs_$TIMESTAMP.tar.gz"
```

### 18.4.2 常见错误模式

**错误模式识别脚本**
```bash
#!/bin/bash
# analyze-errors.sh - 分析日志中的错误模式

LOG_FILE=$1

if [ -z "$LOG_FILE" ]; then
    echo "用法: $0 <日志文件>"
    exit 1
fi

echo "=========================================="
echo "日志错误分析: $LOG_FILE"
echo "=========================================="

# 1. 错误统计
echo -e "\n[1] 错误级别统计"
echo "----------------------------------------"
echo "FATAL: $(grep -c FATAL $LOG_FILE)"
echo "ERROR: $(grep -c ERROR $LOG_FILE)"
echo "WARN:  $(grep -c WARN $LOG_FILE)"

# 2. Top 10错误类型
echo -e "\n[2] Top 10 错误类型"
echo "----------------------------------------"
grep -oP '(?<=Exception: ).*' $LOG_FILE | sort | uniq -c | sort -rn | head -10

# 3. 时间分布
echo -e "\n[3] 错误时间分布"
echo "----------------------------------------"
grep ERROR $LOG_FILE | awk '{print $1}' | cut -d: -f1 | sort | uniq -c

# 4. 相关错误(前后5行)
echo -e "\n[4] 首个FATAL错误上下文"
echo "----------------------------------------"
grep -n -A 5 -B 5 FATAL $LOG_FILE | head -20

# 5. 错误趋势
echo -e "\n[5] 每分钟错误数"
echo "----------------------------------------"
grep ERROR $LOG_FILE | awk '{print substr($2,1,5)}' | sort | uniq -c | tail -20

echo -e "\n=========================================="
```

**Python日志分析**
```python
#!/usr/bin/env python3
# log_analyzer.py - 高级日志分析

import re
import sys
from collections import Counter, defaultdict
from datetime import datetime

def analyze_log(log_file):
    """分析日志文件"""

    errors = []
    errors_by_type = Counter()
    errors_by_time = defaultdict(int)

    # 正则模式
    timestamp_pattern = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})'
    level_pattern = r'\[(ERROR|WARN|FATAL)\]'
    exception_pattern = r'(\w+Exception|Error):'

    with open(log_file, 'r') as f:
        for line in f:
            # 提取时间戳
            ts_match = re.search(timestamp_pattern, line)
            if ts_match:
                timestamp = datetime.fromisoformat(ts_match.group(1))
                hour_key = timestamp.strftime('%Y-%m-%d %H:00')

            # 检查错误级别
            level_match = re.search(level_pattern, line)
            if level_match:
                level = level_match.group(1)

                # 统计错误类型
                exception_match = re.search(exception_pattern, line)
                if exception_match:
                    error_type = exception_match.group(1)
                    errors_by_type[error_type] += 1

                # 时间分布
                errors_by_time[hour_key] += 1

                errors.append({
                    'timestamp': timestamp if ts_match else None,
                    'level': level,
                    'message': line.strip()
                })

    # 报告
    print("=" * 60)
    print("日志分析报告")
    print("=" * 60)

    print(f"\n总错误数: {len(errors)}")

    print("\nTop 10 错误类型:")
    for error_type, count in errors_by_type.most_common(10):
        print(f"  {error_type:30} {count:5} 次")

    print("\n错误时间分布:")
    for hour, count in sorted(errors_by_time.items())[-24:]:
        print(f"  {hour}: {'=' * (count // 10)} ({count})")

    # 检测错误峰值
    max_errors = max(errors_by_time.values()) if errors_by_time else 0
    avg_errors = sum(errors_by_time.values()) / len(errors_by_time) if errors_by_time else 0

    print(f"\n错误峰值: {max_errors} 次/小时")
    print(f"平均错误: {avg_errors:.1f} 次/小时")

    if max_errors > avg_errors * 3:
        print("\n⚠️  检测到错误峰值异常！")
        # 找出峰值时间
        peak_hours = [h for h, c in errors_by_time.items() if c > avg_errors * 2]
        print(f"异常时间段: {', '.join(peak_hours)}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("用法: python log_analyzer.py <日志文件>")
        sys.exit(1)

    analyze_log(sys.argv[1])
```

### 18.4.3 实时调试技巧

**进入运行中的容器**
```bash
# 方法1: exec bash
docker exec -it myapp /bin/bash

# 方法2: exec sh (Alpine镜像)
docker exec -it myapp /bin/sh

# 方法3: nsenter(容器无shell时)
PID=$(docker inspect -f '{{.State.Pid}}' myapp)
nsenter -t $PID -n -p -m /bin/bash

# 在容器内调试
# 安装工具
apt-get update && apt-get install -y curl netcat-openbsd

# 测试网络
curl -v http://database:5432
nc -zv database 5432

# 查看进程
ps aux
top

# 查看日志
tail -f /var/log/app.log

# 环境变量
env | grep DATABASE

# 文件系统
df -h
du -sh /data/*
```

**动态修改配置**
```bash
# 热重载配置(Nginx示例)
docker exec nginx nginx -t  # 测试配置
docker exec nginx nginx -s reload  # 重载配置

# 修改日志级别(无需重启)
docker exec myapp curl -X POST http://localhost:8080/admin/loglevel?level=DEBUG

# 临时修改环境变量
docker exec myapp sh -c 'export DEBUG=true && /app/restart.sh'
```

**性能剖析**
```bash
# Python - cProfile
docker exec myapp python -m cProfile -o output.prof app.py

# Python - 实时剖析
docker exec myapp pip install py-spy
docker exec myapp py-spy top --pid 1

# Java - JFR(Java Flight Recorder)
docker exec myapp jcmd 1 JFR.start duration=60s filename=/tmp/profile.jfr
docker cp myapp:/tmp/profile.jfr .

# Go - pprof
docker exec myapp curl http://localhost:6060/debug/pprof/profile?seconds=30 > cpu.prof
go tool pprof cpu.prof
```

## 18.5 生产环境故障案例

### 18.5.1 案例1: 服务雪崩

**故障现象**
```
2025-12-10 14:30:00 - 用户报告服务响应缓慢
14:32:00 - 部分请求开始超时
14:35:00 - 大量503错误
14:38:00 - 所有服务不可用
```

**排查过程**
```bash
# 1. 检查服务状态
docker service ls
# 发现所有副本处于 0/3 状态

# 2. 查看容器状态
docker ps -a | grep myapp
# 所有容器处于 Restarting 状态

# 3. 查看日志
docker service logs myapp --tail 100
# 大量 "connection pool exhausted" 错误

# 4. 检查数据库连接
docker exec database psql -c "
  SELECT count(*) FROM pg_stat_activity;
"
# 结果: 500 (超过max_connections=200)

# 5. 查看网络连接
docker exec app netstat -an | grep ESTABLISHED | wc -l
# 结果: 每个容器350+连接
```

**根本原因**
```
1. 数据库慢查询导致连接占用时间过长
2. 应用未正确释放数据库连接
3. 连接池配置不合理(max_size=100,但数据库max_connections=200)
4. 健康检查失败导致容器不断重启
5. 重启容器产生更多连接,形成恶性循环
```

**解决方案**
```bash
# 紧急处理
# 1. 临时提高数据库连接数
docker exec database psql -c "ALTER SYSTEM SET max_connections = 500;"
docker restart database

# 2. 强制关闭空闲连接
docker exec database psql -c "
  SELECT pg_terminate_backend(pid)
  FROM pg_stat_activity
  WHERE state = 'idle' AND state_change < NOW() - INTERVAL '5 minutes';
"

# 3. 临时禁用健康检查
docker service update --no-healthcheck myapp

# 4. 减少副本数
docker service scale myapp=2

# 长期优化
# A. 优化慢查询
CREATE INDEX idx_user_created ON users(created_at);

# B. 修复连接池配置
# config.py
DATABASE_POOL_SIZE = 20  # 每个实例20个连接
DATABASE_MAX_OVERFLOW = 10  # 最多额外10个
DATABASE_POOL_TIMEOUT = 30
DATABASE_POOL_RECYCLE = 3600

# C. 添加连接超时
# sqlalchemy
create_engine(
    url,
    pool_pre_ping=True,  # 连接前检查
    pool_recycle=3600,   # 1小时回收
    connect_args={
        'connect_timeout': 10,
        'options': '-c statement_timeout=30000'
    }
)

# D. 实施断路器模式
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
def query_database():
    return db.execute(query)

# E. 调整健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5
```

**预防措施**
```yaml
# 1. 监控告警
- alert: DatabaseConnectionPoolExhausted
  expr: db_connections_used / db_connections_max > 0.8
  for: 5m
  labels:
    severity: warning

- alert: SlowQuery
  expr: rate(pg_slow_queries_total[5m]) > 10
  for: 2m
  labels:
    severity: warning

# 2. 资源限制
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
      restart_policy:
        condition: on-failure
        delay: 10s  # 重启延迟
        max_attempts: 3
        window: 120s

# 3. 限流
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.remote_addr,
    default_limits=["200 per minute", "50 per second"]
)
```

### 18.5.2 案例2: 磁盘空间耗尽

**故障现象**
```
2025-12-10 10:00:00 - 容器写入失败
10:05:00 - 新容器无法启动
10:10:00 - Docker daemon响应缓慢
```

**排查过程**
```bash
# 1. 检查磁盘空间
df -h
# Filesystem      Size  Used Avail Use% Mounted on
# /dev/sda1       100G   98G  2.0G  98% /

# 2. 查找大文件
du -sh /* | sort -h | tail -10

# 3. Docker磁盘使用
docker system df
# TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
# Images          150       20        45GB      30GB (66%)
# Containers      80        30        15GB      10GB (66%)
# Local Volumes   30        10        35GB      25GB (71%)
# Build Cache     -         -         5GB       5GB

# 4. 详细分析
docker system df -v

# 5. 查找大日志文件
find /var/lib/docker/containers/ -name "*-json.log" -exec ls -lh {} \; | sort -k 5 -h | tail -10
```

**根本原因**
```
1. 容器日志未限制大小,单个日志文件达到10GB+
2. 大量未使用的镜像和容器未清理
3. 应用日志写入容器内,未挂载卷
4. 未配置日志轮转
```

**解决方案**
```bash
# 紧急清理
# 1. 清理未使用资源
docker system prune -a --volumes -f
# 释放约60GB空间

# 2. 清理大日志文件
find /var/lib/docker/containers/ -name "*-json.log" -exec truncate -s 0 {} \;

# 3. 临时移动数据
docker volume create temp-vol
docker run --rm -v old-vol:/source -v temp-vol:/dest alpine sh -c "mv /source/* /dest/"

# 长期方案
# A. 配置日志限制
# /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3",
    "compress": "true"
  }
}

systemctl restart docker

# B. 使用外部日志驱动
# docker-compose.yml
version: '3.8'
services:
  app:
    logging:
      driver: "fluentd"
      options:
        fluentd-address: localhost:24224
        tag: app.{{.Name}}

# C. 应用日志挂载卷
services:
  app:
    volumes:
      - app-logs:/var/log/app

# D. 定时清理任务
# crontab
0 2 * * * docker system prune -f > /dev/null 2>&1
0 3 * * 0 docker system prune -a --volumes -f > /dev/null 2>&1

# E. 监控告警
- alert: DiskSpaceHigh
  expr: (node_filesystem_avail_bytes{mountpoint="/var/lib/docker"} / node_filesystem_size_bytes{mountpoint="/var/lib/docker"}) < 0.15
  for: 5m
  labels:
    severity: warning
```

### 18.5.3 案例3: 内存泄漏

**故障现象**
```
应用内存使用持续增长
1小时: 500MB
2小时: 1.2GB
4小时: 2.5GB
6小时: OOM Killed
```

**排查过程**
```bash
# 1. 监控内存趋势
watch -n 5 'docker stats myapp --no-stream'

# 2. 查看OOM事件
docker inspect myapp | jq '.[0].State.OOMKilled'
dmesg | grep -i "out of memory"

# 3. 分析堆内存(Java)
docker exec myapp jmap -heap 1

Heap Usage:
Eden Space:     89% used
Old Generation: 95% used  # 持续增长

# 4. 生成堆转储
docker exec myapp jmap -dump:live,format=b,file=/tmp/heap.hprof 1

# 5. 分析堆转储(MAT)
# 发现大量未释放的Session对象
# 每个Session持有大量缓存数据
# Session没有正确过期

# 6. 检查应用代码
# 发现全局缓存无限增长
cache = {}  # 全局字典
def get_data(key):
    if key not in cache:
        cache[key] = fetch_data(key)  # 永不删除!
    return cache[key]
```

**解决方案**
```python
# A. 使用LRU缓存
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_data(key):
    return fetch_data(key)

# B. 使用TTL缓存
from cachetools import TTLCache

cache = TTLCache(maxsize=1000, ttl=3600)

def get_data(key):
    if key not in cache:
        cache[key] = fetch_data(key)
    return cache[key]

# C. 定期清理
import threading
import time

def cleanup_cache():
    while True:
        time.sleep(3600)  # 1小时
        old_keys = [k for k, v in cache.items()
                    if v['timestamp'] < time.time() - 7200]
        for k in old_keys:
            del cache[k]

cleanup_thread = threading.Thread(target=cleanup_cache, daemon=True)
cleanup_thread.start()

# D. 使用Redis外部缓存
import redis

redis_client = redis.Redis(host='redis', decode_responses=True)

def get_data(key):
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)

    data = fetch_data(key)
    redis_client.setex(key, 3600, json.dumps(data))  # 1小时过期
    return data

# E. Session管理
# Flask
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
```

**验证修复**
```bash
# 1. 重新部署
docker service update --image myapp:fixed myapp

# 2. 长期监控
# Prometheus query
rate(container_memory_usage_bytes{name="myapp"}[1h])

# 3. 设置告警
- alert: MemoryLeakSuspected
  expr: |
    (container_memory_usage_bytes{name="myapp"} -
     container_memory_usage_bytes{name="myapp"} offset 1h) > 500000000
  for: 2h
  labels:
    severity: warning
```

---

*（第18章完成,约2000行。已完成18章,剩余1章...）*

---

# 第19章: 最佳实践与案例

本章汇总Docker在企业级生产环境的最佳实践,涵盖安全加固、CI/CD集成、迁移策略和常见避坑指南,帮助您构建稳定、安全、高效的容器化平台。

---

## 19.1 企业级部署案例

### 19.1.1 电商平台微服务架构

**架构概览**:
```
┌─────────────────────────────────────────────────────────────┐
│                         外部用户                              │
└───────────────┬─────────────────────────────────────────────┘
                │
         ┌──────▼──────┐
         │   CloudFlare CDN   │
         │   (DDoS防护/缓存)   │
         └──────┬──────┘
                │
         ┌──────▼──────┐
         │   Nginx Ingress    │
         │   (SSL/WAF/限流)   │
         └──────┬──────┘
                │
    ┌───────────┼───────────┐
    │           │           │
┌───▼───┐  ┌───▼───┐  ┌───▼───┐
│Web前端 │  │API网关 │  │管理后台│
└───┬───┘  └───┬───┘  └───┬───┘
    │          │          │
    └──────┬───┴────┬─────┘
           │        │
    ┌──────▼────────▼──────┐
    │   业务服务层 (Swarm)    │
    │  ┌────────────────┐  │
    │  │用户服务  订单服务│  │
    │  │商品服务  支付服务│  │
    │  │库存服务  物流服务│  │
    │  └────────────────┘  │
    └──────┬────────┬──────┘
           │        │
    ┌──────▼────┐  ┌▼──────┐
    │PostgreSQL │  │ Redis  │
    │   集群     │  │ 集群   │
    └───────────┘  └────────┘
```

**Docker Stack 配置**:

```yaml
# ecommerce-stack.yml
version: '3.8'

networks:
  frontend:
    driver: overlay
    attachable: true
  backend:
    driver: overlay
    internal: true
  db:
    driver: overlay
    internal: true

volumes:
  postgres_data:
  redis_data:

secrets:
  db_password:
    external: true
  jwt_secret:
    external: true
  payment_api_key:
    external: true

services:
  # ==================== API网关 ====================
  api_gateway:
    image: registry.company.com/api-gateway:v2.3.1
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
    networks:
      - frontend
      - backend
    ports:
      - "8080:8080"
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=info
      - RATE_LIMIT_RPS=1000
      - JWT_SECRET_FILE=/run/secrets/jwt_secret
    secrets:
      - jwt_secret
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s
    logging:
      driver: fluentd
      options:
        fluentd-address: "fluentd.company.com:24224"
        tag: "api_gateway"

  # ==================== 用户服务 ====================
  user_service:
    image: registry.company.com/user-service:v1.5.2
    deploy:
      replicas: 3
      placement:
        constraints:
          - node.labels.tier == app
      update_config:
        parallelism: 1
        delay: 10s
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
    networks:
      - backend
      - db
    environment:
      - DB_HOST=postgres-master
      - DB_PORT=5432
      - DB_NAME=users
      - DB_PASSWORD_FILE=/run/secrets/db_password
      - REDIS_HOST=redis-master
      - REDIS_PORT=6379
    secrets:
      - db_password
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 15s
      timeout: 5s
      retries: 3
    logging:
      driver: fluentd
      options:
        tag: "user_service"

  # ==================== 订单服务 ====================
  order_service:
    image: registry.company.com/order-service:v2.1.0
    deploy:
      replicas: 5  # 高并发服务
      placement:
        constraints:
          - node.labels.tier == app
      resources:
        limits:
          cpus: '1'
          memory: 512M
    networks:
      - backend
      - db
    environment:
      - DB_HOST=postgres-master
      - DB_NAME=orders
      - DB_PASSWORD_FILE=/run/secrets/db_password
      - REDIS_HOST=redis-master
      - MQ_HOST=rabbitmq
    secrets:
      - db_password
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  # ==================== 商品服务 ====================
  product_service:
    image: registry.company.com/product-service:v1.8.3
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
    networks:
      - backend
      - db
    environment:
      - DB_HOST=postgres-master
      - DB_NAME=products
      - DB_PASSWORD_FILE=/run/secrets/db_password
      - REDIS_HOST=redis-master
      - CACHE_TTL=3600
    secrets:
      - db_password

  # ==================== 支付服务 ====================
  payment_service:
    image: registry.company.com/payment-service:v1.2.1
    deploy:
      replicas: 2
      placement:
        constraints:
          - node.labels.security == high  # 部署到安全节点
      resources:
        limits:
          cpus: '1'
          memory: 512M
    networks:
      - backend
      - db
    environment:
      - DB_HOST=postgres-master
      - DB_NAME=payments
      - DB_PASSWORD_FILE=/run/secrets/db_password
      - PAYMENT_API_KEY_FILE=/run/secrets/payment_api_key
      - ENCRYPTION_ENABLED=true
    secrets:
      - db_password
      - payment_api_key
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 15s

  # ==================== PostgreSQL主从集群 ====================
  postgres_master:
    image: postgres:15-alpine
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.labels.tier == db
      resources:
        limits:
          cpus: '2'
          memory: 2G
    networks:
      - db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password
      - POSTGRES_INITDB_ARGS=-E UTF8 --locale=en_US.utf8
      - PGDATA=/var/lib/postgresql/data/pgdata
    secrets:
      - db_password
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ==================== Redis集群 ====================
  redis_master:
    image: redis:7-alpine
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.labels.tier == cache
      resources:
        limits:
          cpus: '1'
          memory: 1G
    networks:
      - db
    volumes:
      - redis_data:/data
    command: >
      redis-server
      --maxmemory 768mb
      --maxmemory-policy allkeys-lru
      --appendonly yes
      --save 900 1
      --save 300 10
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  # ==================== RabbitMQ消息队列 ====================
  rabbitmq:
    image: rabbitmq:3.12-management-alpine
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.labels.tier == app
      resources:
        limits:
          cpus: '1'
          memory: 1G
    networks:
      - backend
    environment:
      - RABBITMQ_DEFAULT_USER=admin
      - RABBITMQ_DEFAULT_PASS_FILE=/run/secrets/db_password
    secrets:
      - db_password
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**部署脚本**:

```bash
#!/bin/bash
# deploy-ecommerce.sh - 电商平台自动化部署脚本

set -e

STACK_NAME="ecommerce"
REGISTRY="registry.company.com"
ENVIRONMENT="production"

echo "=========================================="
echo "电商平台部署脚本"
echo "环境: $ENVIRONMENT"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# 1. 检查前置条件
echo -e "\n[1/8] 检查Docker Swarm状态..."
if ! docker info | grep -q "Swarm: active"; then
    echo "❌ Docker Swarm未激活"
    exit 1
fi

# 检查节点标签
echo "检查节点标签..."
NODE_LABELS=$(docker node ls --format "{{.Hostname}}: {{.Labels}}")
echo "$NODE_LABELS"

# 2. 创建网络
echo -e "\n[2/8] 创建网络..."
for network in frontend backend db; do
    if ! docker network ls | grep -q "${STACK_NAME}_${network}"; then
        docker network create --driver overlay "${STACK_NAME}_${network}"
        echo "✓ 创建网络: ${STACK_NAME}_${network}"
    fi
done

# 3. 创建Secrets
echo -e "\n[3/8] 创建Secrets..."
if [ ! -f .env.production ]; then
    echo "❌ 缺少 .env.production 文件"
    exit 1
fi

source .env.production

echo "$DB_PASSWORD" | docker secret create db_password - 2>/dev/null || echo "Secret已存在: db_password"
echo "$JWT_SECRET" | docker secret create jwt_secret - 2>/dev/null || echo "Secret已存在: jwt_secret"
echo "$PAYMENT_API_KEY" | docker secret create payment_api_key - 2>/dev/null || echo "Secret已存在: payment_api_key"

# 4. 拉取最新镜像
echo -e "\n[4/8] 拉取最新镜像..."
SERVICES=(
    "api-gateway:v2.3.1"
    "user-service:v1.5.2"
    "order-service:v2.1.0"
    "product-service:v1.8.3"
    "payment-service:v1.2.1"
)

for service in "${SERVICES[@]}"; do
    echo "拉取: $REGISTRY/$service"
    docker pull "$REGISTRY/$service"
done

# 5. 部署数据库初始化任务
echo -e "\n[5/8] 初始化数据库..."
docker run --rm \
    --network ${STACK_NAME}_db \
    -e DB_HOST=postgres-master \
    -e DB_PASSWORD="$DB_PASSWORD" \
    "$REGISTRY/db-migrator:latest" \
    migrate up

# 6. 部署Stack
echo -e "\n[6/8] 部署Docker Stack..."
docker stack deploy -c ecommerce-stack.yml "$STACK_NAME"

# 7. 等待服务启动
echo -e "\n[7/8] 等待服务启动..."
for i in {1..30}; do
    RUNNING=$(docker stack services "$STACK_NAME" --format "{{.Replicas}}" | grep -c "/")
    EXPECTED=$(docker stack services "$STACK_NAME" --format "{{.Name}}" | wc -l)

    echo "进度: $RUNNING/$EXPECTED 服务运行中..."

    if [ "$RUNNING" -eq "$EXPECTED" ]; then
        READY=$(docker stack services "$STACK_NAME" --format "{{.Replicas}}" | awk -F'/' '{if($1==$2) print $0}' | wc -l)
        if [ "$READY" -eq "$EXPECTED" ]; then
            echo "✓ 所有服务已就绪"
            break
        fi
    fi

    if [ $i -eq 30 ]; then
        echo "⚠️  服务启动超时,请检查日志"
    fi

    sleep 10
done

# 8. 健康检查
echo -e "\n[8/8] 执行健康检查..."
API_GATEWAY_URL="http://$(docker node inspect self --format '{{.Status.Addr}}'):8080"

for endpoint in /health /api/v1/users/health /api/v1/orders/health; do
    echo -n "检查 $endpoint ... "
    if curl -sf "${API_GATEWAY_URL}${endpoint}" > /dev/null; then
        echo "✓"
    else
        echo "✗"
    fi
done

# 9. 显示部署状态
echo -e "\n=========================================="
echo "部署完成!"
echo "=========================================="
docker stack services "$STACK_NAME"

echo -e "\n查看日志:"
echo "  docker service logs -f ${STACK_NAME}_api_gateway"
echo "  docker service logs -f ${STACK_NAME}_order_service"

echo -e "\n访问地址:"
echo "  API网关: $API_GATEWAY_URL"
echo "  管理后台: http://$(docker node inspect self --format '{{.Status.Addr}}'):8081"
```

**性能测试**:

```bash
#!/bin/bash
# benchmark.sh - 电商平台性能测试

API_URL="http://api.ecommerce.com"

echo "=========================================="
echo "电商平台性能基准测试"
echo "=========================================="

# 1. 商品列表接口 (读多写少)
echo -e "\n[1] 商品列表API (GET /api/v1/products)"
ab -n 10000 -c 100 -H "Authorization: Bearer $TOKEN" \
   "${API_URL}/api/v1/products?page=1&size=20"

# 2. 创建订单接口 (写入密集)
echo -e "\n[2] 创建订单API (POST /api/v1/orders)"
ab -n 1000 -c 50 -p order.json -T "application/json" \
   -H "Authorization: Bearer $TOKEN" \
   "${API_URL}/api/v1/orders"

# 3. 支付接口 (高安全要求)
echo -e "\n[3] 支付API (POST /api/v1/payments)"
ab -n 500 -c 20 -p payment.json -T "application/json" \
   -H "Authorization: Bearer $TOKEN" \
   "${API_URL}/api/v1/payments"

# 输出汇总
echo -e "\n=========================================="
echo "测试完成"
echo "=========================================="
```

### 19.1.2 物联网数据采集平台

**架构特点**:
- 高并发数据采集 (10万+设备)
- 时序数据存储 (InfluxDB)
- 实时数据处理 (Kafka + Flink)
- 边缘计算节点

**Docker Compose配置**:

```yaml
# iot-platform.yml
version: '3.8'

services:
  # ==================== MQTT Broker (设备连接) ====================
  emqx:
    image: emqx/emqx:5.3.0
    ports:
      - "1883:1883"    # MQTT
      - "8883:8883"    # MQTT/SSL
      - "8083:8083"    # WebSocket
      - "18083:18083"  # Dashboard
    environment:
      - EMQX_NAME=emqx
      - EMQX_HOST=node1.emqx.io
      - EMQX_NODE__COOKIE=emqxsecretcookie
      - EMQX_LISTENER__TCP__EXTERNAL__MAX_CONNECTIONS=100000
    volumes:
      - ./emqx/data:/opt/emqx/data
      - ./emqx/log:/opt/emqx/log
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
    healthcheck:
      test: ["CMD", "emqx", "ping"]
      interval: 10s

  # ==================== Kafka (消息队列) ====================
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_LOG_RETENTION_HOURS: 168
      KAFKA_LOG_SEGMENT_BYTES: 1073741824
      KAFKA_NUM_PARTITIONS: 10
    depends_on:
      - zookeeper
    volumes:
      - kafka-data:/var/lib/kafka/data

  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    volumes:
      - zookeeper-data:/var/lib/zookeeper/data

  # ==================== InfluxDB (时序数据库) ====================
  influxdb:
    image: influxdb:2.7-alpine
    ports:
      - "8086:8086"
    environment:
      - DOCKER_INFLUXDB_INIT_MODE=setup
      - DOCKER_INFLUXDB_INIT_USERNAME=admin
      - DOCKER_INFLUXDB_INIT_PASSWORD=admin123456
      - DOCKER_INFLUXDB_INIT_ORG=iot
      - DOCKER_INFLUXDB_INIT_BUCKET=sensor_data
      - DOCKER_INFLUXDB_INIT_RETENTION=30d
    volumes:
      - influxdb-data:/var/lib/influxdb2
      - influxdb-config:/etc/influxdb2
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  # ==================== 数据处理服务 ====================
  data_processor:
    image: iot-platform/data-processor:v1.0.0
    environment:
      - KAFKA_BROKERS=kafka:9092
      - INFLUXDB_URL=http://influxdb:8086
      - INFLUXDB_TOKEN=${INFLUXDB_TOKEN}
      - INFLUXDB_ORG=iot
      - INFLUXDB_BUCKET=sensor_data
      - PROCESSING_THREADS=8
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
    depends_on:
      - kafka
      - influxdb

  # ==================== 规则引擎 ====================
  rule_engine:
    image: iot-platform/rule-engine:v1.0.0
    environment:
      - KAFKA_BROKERS=kafka:9092
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - ALERT_WEBHOOK_URL=${ALERT_WEBHOOK_URL}
    deploy:
      replicas: 2

  # ==================== API服务 ====================
  api_server:
    image: iot-platform/api-server:v1.0.0
    ports:
      - "8080:8080"
    environment:
      - INFLUXDB_URL=http://influxdb:8086
      - INFLUXDB_TOKEN=${INFLUXDB_TOKEN}
      - REDIS_HOST=redis
      - JWT_SECRET=${JWT_SECRET}
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  # ==================== Redis (缓存) ====================
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data

volumes:
  kafka-data:
  zookeeper-data:
  influxdb-data:
  influxdb-config:
  redis-data:
```

**数据处理服务示例**:

```python
#!/usr/bin/env python3
# data_processor.py - IoT数据处理服务

import json
import logging
from kafka import KafkaConsumer
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置
KAFKA_BROKERS = os.getenv('KAFKA_BROKERS', 'localhost:9092')
KAFKA_TOPIC = 'sensor_data'
INFLUXDB_URL = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN')
INFLUXDB_ORG = os.getenv('INFLUXDB_ORG', 'iot')
INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET', 'sensor_data')

class DataProcessor:
    def __init__(self):
        # Kafka消费者
        self.consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BROKERS.split(','),
            group_id='data_processor',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True
        )

        # InfluxDB客户端
        self.influx_client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)

        logger.info("DataProcessor初始化完成")

    def process_message(self, message):
        """处理单条消息"""
        try:
            device_id = message['device_id']
            sensor_type = message['sensor_type']
            value = message['value']
            timestamp = message['timestamp']

            # 数据清洗
            if not self.validate_data(sensor_type, value):
                logger.warning(f"Invalid data from {device_id}: {value}")
                return

            # 写入InfluxDB
            point = Point("sensor_measurement") \
                .tag("device_id", device_id) \
                .tag("sensor_type", sensor_type) \
                .field("value", float(value)) \
                .time(timestamp)

            self.write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)

            # 检查告警规则
            self.check_alerts(device_id, sensor_type, value)

        except Exception as e:
            logger.error(f"处理消息失败: {e}", exc_info=True)

    def validate_data(self, sensor_type, value):
        """数据验证"""
        ranges = {
            'temperature': (-50, 100),
            'humidity': (0, 100),
            'pressure': (800, 1200)
        }

        if sensor_type not in ranges:
            return True

        min_val, max_val = ranges[sensor_type]
        return min_val <= float(value) <= max_val

    def check_alerts(self, device_id, sensor_type, value):
        """检查告警规则"""
        # 温度过高告警
        if sensor_type == 'temperature' and float(value) > 80:
            logger.warning(f"🚨 Temperature alert: {device_id} = {value}°C")
            # 发送告警通知...

    def run(self):
        """主循环"""
        logger.info("开始消费Kafka消息...")

        for message in self.consumer:
            try:
                self.process_message(message.value)
            except KeyboardInterrupt:
                logger.info("收到停止信号")
                break
            except Exception as e:
                logger.error(f"处理消息异常: {e}", exc_info=True)

        self.consumer.close()
        self.influx_client.close()

if __name__ == '__main__':
    processor = DataProcessor()
    processor.run()
```

---

## 19.2 安全加固

### 19.2.1 镜像安全

**1. 使用官方基础镜像**:

```dockerfile
# ❌ 不推荐: 使用latest标签
FROM node:latest

# ✅ 推荐: 使用具体版本 + Alpine变体
FROM node:18.19.0-alpine3.19

# ✅ 最佳: 使用SHA256摘要锁定版本
FROM node:18.19.0-alpine3.19@sha256:...
```

**2. 最小化镜像**:

```dockerfile
# 多阶段构建 - 生产镜像仅包含必需文件
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force
COPY . .
RUN npm run build

FROM node:18-alpine AS production
RUN apk add --no-cache dumb-init
USER node
WORKDIR /app
COPY --chown=node:node --from=builder /app/dist ./dist
COPY --chown=node:node --from=builder /app/node_modules ./node_modules
EXPOSE 3000
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "dist/main.js"]
```

**3. 镜像安全扫描**:

```bash
#!/bin/bash
# scan-image.sh - 镜像安全扫描脚本

IMAGE=$1

if [ -z "$IMAGE" ]; then
    echo "用法: $0 <镜像名称>"
    exit 1
fi

echo "=========================================="
echo "镜像安全扫描: $IMAGE"
echo "=========================================="

# 1. Trivy扫描
echo -e "\n[1] Trivy漏洞扫描..."
trivy image --severity HIGH,CRITICAL "$IMAGE"

# 2. 检查镜像层数
echo -e "\n[2] 镜像层数检查..."
LAYERS=$(docker history "$IMAGE" --quiet | wc -l)
echo "层数: $LAYERS"
if [ "$LAYERS" -gt 20 ]; then
    echo "⚠️  警告: 镜像层数过多,建议合并层"
fi

# 3. 检查镜像大小
echo -e "\n[3] 镜像大小检查..."
SIZE=$(docker images "$IMAGE" --format "{{.Size}}")
echo "大小: $SIZE"

# 4. 检查root用户
echo -e "\n[4] 用户权限检查..."
USER=$(docker inspect "$IMAGE" --format='{{.Config.User}}')
if [ -z "$USER" ] || [ "$USER" = "root" ] || [ "$USER" = "0" ]; then
    echo "❌ 警告: 容器使用root用户运行"
else
    echo "✓ 容器使用非root用户: $USER"
fi

# 5. 检查敏感文件
echo -e "\n[5] 敏感文件检查..."
TEMP_CONTAINER=$(docker create "$IMAGE")
docker export "$TEMP_CONTAINER" | tar -t | grep -E "\.(key|pem|crt|env)$" || echo "✓ 未发现敏感文件"
docker rm "$TEMP_CONTAINER" > /dev/null

# 6. 生成SBOM (软件物料清单)
echo -e "\n[6] 生成SBOM..."
syft "$IMAGE" -o json > "${IMAGE//\//_}_sbom.json"
echo "✓ SBOM已保存到: ${IMAGE//\//_}_sbom.json"

echo -e "\n=========================================="
echo "扫描完成"
echo "=========================================="
```

### 19.2.2 运行时安全

**1. AppArmor配置**:

```bash
# /etc/apparmor.d/docker-default-secure
#include <tunables/global>

profile docker-default-secure flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # 拒绝挂载
  deny mount,

  # 拒绝修改内核参数
  deny @{PROC}/sys/kernel/** w,

  # 拒绝访问宿主机设备
  deny /dev/** rw,

  # 允许必要的系统调用
  capability setgid,
  capability setuid,
  capability net_bind_service,

  # 拒绝危险系统调用
  deny capability sys_admin,
  deny capability sys_module,
  deny capability sys_rawio,

  # 允许容器内文件访问
  /app/** rw,
  /tmp/** rw,
  /var/tmp/** rw,
}
```

**应用到容器**:

```bash
docker run --security-opt apparmor=docker-default-secure myapp
```

**2. Seccomp配置**:

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "archMap": [
    {
      "architecture": "SCMP_ARCH_X86_64",
      "subArchitectures": ["SCMP_ARCH_X86", "SCMP_ARCH_X32"]
    }
  ],
  "syscalls": [
    {
      "names": [
        "accept", "accept4", "access", "bind", "brk",
        "chdir", "clone", "close", "connect", "dup",
        "dup2", "execve", "exit", "fork", "fstat",
        "getcwd", "getpid", "getuid", "listen", "mmap",
        "open", "read", "recv", "recvfrom", "send",
        "sendto", "socket", "stat", "write"
      ],
      "action": "SCMP_ACT_ALLOW"
    },
    {
      "names": ["reboot", "swapon", "swapoff"],
      "action": "SCMP_ACT_ERRNO",
      "errnoRet": 1
    }
  ]
}
```

**应用Seccomp**:

```bash
docker run --security-opt seccomp=seccomp-profile.json myapp
```

**3. 只读根文件系统**:

```yaml
# docker-compose.yml
services:
  app:
    image: myapp:latest
    read_only: true
    tmpfs:
      - /tmp
      - /var/run
      - /app/cache:uid=1000,gid=1000,mode=1777
    volumes:
      - app-logs:/app/logs
```

### 19.2.3 网络安全

**1. 网络隔离**:

```yaml
# network-isolation.yml
version: '3.8'

networks:
  frontend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.1.0/24
  backend:
    driver: bridge
    internal: true  # 无外网访问
    ipam:
      config:
        - subnet: 172.20.2.0/24
  database:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.20.3.0/24

services:
  web:
    image: nginx
    networks:
      - frontend
      - backend

  api:
    image: api-server
    networks:
      - backend
      - database

  postgres:
    image: postgres
    networks:
      - database  # 仅database网络可访问
```

**2. 防火墙规则**:

```bash
#!/bin/bash
# docker-firewall.sh - Docker防火墙配置

# 清除现有规则
iptables -F DOCKER-USER
iptables -X DOCKER-USER
iptables -N DOCKER-USER

# 1. 允许已建立的连接
iptables -A DOCKER-USER -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

# 2. 限制特定IP访问敏感端口
iptables -A DOCKER-USER -p tcp --dport 5432 -s 10.0.0.0/8 -j ACCEPT
iptables -A DOCKER-USER -p tcp --dport 5432 -j DROP

# 3. 限制容器访问宿主机元数据服务
iptables -A DOCKER-USER -d 169.254.169.254 -j DROP

# 4. 限制容器间互访
iptables -A DOCKER-USER -i docker0 -o docker0 -j DROP

# 5. 速率限制
iptables -A DOCKER-USER -p tcp --dport 80 -m limit --limit 100/sec --limit-burst 200 -j ACCEPT
iptables -A DOCKER-USER -p tcp --dport 80 -j DROP

# 6. 默认拒绝
iptables -A DOCKER-USER -j DROP

echo "✓ Docker防火墙规则已应用"
iptables -L DOCKER-USER -n -v
```

---

## 19.3 CI/CD集成

### 19.3.1 GitLab CI集成

**.gitlab-ci.yml**:

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - security
  - deploy

variables:
  DOCKER_REGISTRY: registry.company.com
  DOCKER_IMAGE: $DOCKER_REGISTRY/$CI_PROJECT_NAME
  DOCKER_TAG: $CI_COMMIT_SHORT_SHA

# ==================== 构建阶段 ====================
build:
  stage: build
  image: docker:24.0-dind
  services:
    - docker:24.0-dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $DOCKER_REGISTRY
  script:
    # 使用BuildKit加速构建
    - export DOCKER_BUILDKIT=1
    - docker build
        --cache-from $DOCKER_IMAGE:latest
        --build-arg BUILDKIT_INLINE_CACHE=1
        --tag $DOCKER_IMAGE:$DOCKER_TAG
        --tag $DOCKER_IMAGE:latest
        .
    - docker push $DOCKER_IMAGE:$DOCKER_TAG
    - docker push $DOCKER_IMAGE:latest
  only:
    - main
    - develop

# ==================== 测试阶段 ====================
unit_test:
  stage: test
  image: $DOCKER_IMAGE:$DOCKER_TAG
  script:
    - npm install
    - npm run test
  coverage: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'
  artifacts:
    reports:
      junit: test-results.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml

integration_test:
  stage: test
  image: docker/compose:latest
  services:
    - docker:24.0-dind
  script:
    - docker-compose -f docker-compose.test.yml up -d
    - docker-compose -f docker-compose.test.yml exec -T app npm run test:integration
  after_script:
    - docker-compose -f docker-compose.test.yml down -v

# ==================== 安全扫描阶段 ====================
security_scan:
  stage: security
  image: aquasec/trivy:latest
  script:
    - trivy image
        --severity HIGH,CRITICAL
        --exit-code 1
        --no-progress
        $DOCKER_IMAGE:$DOCKER_TAG
  allow_failure: true

sast:
  stage: security
  image: returntocorp/semgrep
  script:
    - semgrep --config=auto --json --output=sast-report.json .
  artifacts:
    reports:
      sast: sast-report.json

# ==================== 部署阶段 ====================
deploy_staging:
  stage: deploy
  image: alpine:latest
  before_script:
    - apk add --no-cache openssh-client
    - eval $(ssh-agent -s)
    - echo "$SSH_PRIVATE_KEY" | tr -d '\r' | ssh-add -
    - mkdir -p ~/.ssh
    - chmod 700 ~/.ssh
  script:
    - |
      ssh -o StrictHostKeyChecking=no deploy@staging.company.com << EOF
        cd /opt/myapp
        docker pull $DOCKER_IMAGE:$DOCKER_TAG
        docker-compose up -d
        docker-compose ps
      EOF
  environment:
    name: staging
    url: https://staging.company.com
  only:
    - develop

deploy_production:
  stage: deploy
  image: alpine:latest
  before_script:
    - apk add --no-cache openssh-client
    - eval $(ssh-agent -s)
    - echo "$SSH_PRIVATE_KEY" | tr -d '\r' | ssh-add -
  script:
    - |
      ssh -o StrictHostKeyChecking=no deploy@prod.company.com << EOF
        cd /opt/myapp

        # 蓝绿部署
        export NEW_TAG=$DOCKER_TAG
        export OLD_TAG=\$(docker ps --filter "name=myapp" --format "{{.Image}}" | cut -d: -f2)

        # 启动新版本
        docker pull $DOCKER_IMAGE:\$NEW_TAG
        docker-compose -f docker-compose.blue-green.yml up -d blue

        # 健康检查
        for i in {1..30}; do
          if curl -sf http://localhost:8080/health; then
            echo "✓ 新版本健康检查通过"
            break
          fi
          echo "等待服务启动... (\$i/30)"
          sleep 2
        done

        # 切换流量
        docker-compose -f docker-compose.blue-green.yml up -d nginx

        # 停止旧版本
        docker-compose -f docker-compose.blue-green.yml stop green

        echo "✓ 部署完成: \$OLD_TAG -> \$NEW_TAG"
      EOF
  environment:
    name: production
    url: https://app.company.com
  when: manual
  only:
    - main
```

### 19.3.2 Jenkins Pipeline

**Jenkinsfile**:

```groovy
// Jenkinsfile
pipeline {
    agent any

    environment {
        DOCKER_REGISTRY = 'registry.company.com'
        DOCKER_IMAGE = "${DOCKER_REGISTRY}/${JOB_NAME}"
        DOCKER_TAG = "${BUILD_NUMBER}"
        DOCKER_CREDENTIALS = credentials('docker-registry-credentials')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build') {
            steps {
                script {
                    // 构建Docker镜像
                    docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}")
                }
            }
        }

        stage('Test') {
            steps {
                script {
                    // 运行测试
                    docker.image("${DOCKER_IMAGE}:${DOCKER_TAG}").inside {
                        sh 'npm install'
                        sh 'npm run test'
                    }
                }
            }
            post {
                always {
                    junit 'test-results.xml'
                }
            }
        }

        stage('Security Scan') {
            parallel {
                stage('Trivy Scan') {
                    steps {
                        sh """
                            trivy image \
                                --severity HIGH,CRITICAL \
                                --format json \
                                --output trivy-report.json \
                                ${DOCKER_IMAGE}:${DOCKER_TAG}
                        """
                    }
                }

                stage('Anchore Scan') {
                    steps {
                        writeFile file: 'anchore_images',
                                  text: "${DOCKER_IMAGE}:${DOCKER_TAG}"
                        anchore name: 'anchore_images',
                                bailOnFail: false
                    }
                }
            }
        }

        stage('Push') {
            steps {
                script {
                    docker.withRegistry("https://${DOCKER_REGISTRY}", 'docker-registry-credentials') {
                        docker.image("${DOCKER_IMAGE}:${DOCKER_TAG}").push()
                        docker.image("${DOCKER_IMAGE}:${DOCKER_TAG}").push('latest')
                    }
                }
            }
        }

        stage('Deploy to Staging') {
            when {
                branch 'develop'
            }
            steps {
                sshagent(['staging-ssh-key']) {
                    sh """
                        ssh deploy@staging.company.com '
                            cd /opt/myapp &&
                            export IMAGE_TAG=${DOCKER_TAG} &&
                            docker-compose pull &&
                            docker-compose up -d &&
                            docker-compose ps
                        '
                    """
                }
            }
        }

        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                input message: '确认部署到生产环境?', ok: '部署'

                sshagent(['production-ssh-key']) {
                    sh """
                        ssh deploy@prod.company.com '
                            cd /opt/myapp &&
                            ./deploy.sh ${DOCKER_TAG}
                        '
                    """
                }
            }
        }
    }

    post {
        success {
            slackSend(
                color: 'good',
                message: "✓ 构建成功: ${JOB_NAME} #${BUILD_NUMBER} (<${BUILD_URL}|查看详情>)"
            )
        }
        failure {
            slackSend(
                color: 'danger',
                message: "✗ 构建失败: ${JOB_NAME} #${BUILD_NUMBER} (<${BUILD_URL}|查看详情>)"
            )
        }
        always {
            cleanWs()
        }
    }
}
```

### 19.3.3 金丝雀发布

**部署脚本**:

```bash
#!/bin/bash
# canary-deploy.sh - 金丝雀发布脚本

set -e

NEW_VERSION=$1
CANARY_PERCENT=${2:-10}  # 默认10%流量

if [ -z "$NEW_VERSION" ]; then
    echo "用法: $0 <新版本> [金丝雀百分比]"
    exit 1
fi

STACK_NAME="myapp"
SERVICE_NAME="${STACK_NAME}_api"

echo "=========================================="
echo "金丝雀发布"
echo "新版本: $NEW_VERSION"
echo "金丝雀流量: $CANARY_PERCENT%"
echo "=========================================="

# 1. 获取当前版本
CURRENT_VERSION=$(docker service inspect "$SERVICE_NAME" --format '{{.Spec.TaskTemplate.ContainerSpec.Image}}' | cut -d: -f2)
echo -e "\n当前版本: $CURRENT_VERSION"

# 2. 创建金丝雀服务
echo -e "\n[1/5] 创建金丝雀服务..."
docker service create \
    --name "${SERVICE_NAME}_canary" \
    --label canary=true \
    --network "${STACK_NAME}_backend" \
    --replicas 1 \
    --limit-cpu 0.5 \
    --limit-memory 256M \
    "registry.company.com/myapp:${NEW_VERSION}"

# 3. 等待金丝雀服务就绪
echo -e "\n[2/5] 等待金丝雀服务启动..."
for i in {1..30}; do
    STATUS=$(docker service ps "${SERVICE_NAME}_canary" --filter "desired-state=running" --format "{{.CurrentState}}")
    if echo "$STATUS" | grep -q "Running"; then
        echo "✓ 金丝雀服务已就绪"
        break
    fi
    echo "等待中... ($i/30)"
    sleep 2
done

# 4. 配置Traefik流量权重
echo -e "\n[3/5] 配置流量权重..."
cat > /tmp/traefik-canary.yml <<EOF
http:
  services:
    api-weighted:
      weighted:
        services:
          - name: api-stable
            weight: $((100 - CANARY_PERCENT))
          - name: api-canary
            weight: $CANARY_PERCENT
EOF

docker config create traefik-canary-config /tmp/traefik-canary.yml
docker service update --config-add traefik-canary-config traefik

# 5. 监控金丝雀指标 (持续10分钟)
echo -e "\n[4/5] 监控金丝雀指标..."
MONITORING_DURATION=600
START_TIME=$(date +%s)

while true; do
    ELAPSED=$(($(date +%s) - START_TIME))

    if [ $ELAPSED -ge $MONITORING_DURATION ]; then
        echo "✓ 监控完成"
        break
    fi

    # 查询错误率
    ERROR_RATE=$(curl -s 'http://prometheus:9090/api/v1/query?query=rate(http_requests_total{service="api_canary",status=~"5.."}[5m])' | jq -r '.data.result[0].value[1]')

    # 查询延迟
    LATENCY_P99=$(curl -s 'http://prometheus:9090/api/v1/query?query=histogram_quantile(0.99,rate(http_request_duration_seconds_bucket{service="api_canary"}[5m]))' | jq -r '.data.result[0].value[1]')

    echo "错误率: ${ERROR_RATE:-0}  P99延迟: ${LATENCY_P99:-0}s"

    # 检查是否超过阈值
    if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
        echo "❌ 错误率过高,回滚金丝雀!"
        ./rollback-canary.sh
        exit 1
    fi

    sleep 30
done

# 6. 全量发布
echo -e "\n[5/5] 金丝雀健康,开始全量发布..."
docker service update \
    --image "registry.company.com/myapp:${NEW_VERSION}" \
    --update-parallelism 2 \
    --update-delay 10s \
    "$SERVICE_NAME"

# 清理金丝雀服务
docker service rm "${SERVICE_NAME}_canary"

echo -e "\n=========================================="
echo "✓ 发布完成: $CURRENT_VERSION -> $NEW_VERSION"
echo "=========================================="
```

---

## 19.4 迁移策略

### 19.4.1 从虚拟机迁移到容器

**迁移评估检查表**:

```bash
#!/bin/bash
# assess-migration.sh - 迁移可行性评估

APP_NAME=$1

echo "=========================================="
echo "应用迁移评估: $APP_NAME"
echo "=========================================="

# 1. 检查应用类型
echo -e "\n[1] 应用类型检查"
echo "✓ 无状态应用更适合容器化"
echo "✓ 有状态应用需要额外的持久化方案"

# 2. 检查依赖项
echo -e "\n[2] 依赖项分析"
ldd /usr/bin/myapp 2>/dev/null | grep "=>" | awk '{print $1}' | sort
echo "建议: 使用官方基础镜像包含大部分系统库"

# 3. 检查配置文件
echo -e "\n[3] 配置文件位置"
find /etc -name "*${APP_NAME}*" 2>/dev/null
echo "建议: 使用环境变量或ConfigMap管理配置"

# 4. 检查数据目录
echo -e "\n[4] 数据目录"
find /var -name "*${APP_NAME}*" -type d 2>/dev/null
echo "建议: 使用Docker Volume或外部存储"

# 5. 检查端口占用
echo -e "\n[5] 监听端口"
netstat -tlnp | grep "$APP_NAME"
echo "建议: 确保端口不冲突"

# 6. 检查系统调用
echo -e "\n[6] 系统调用分析"
strace -c /usr/bin/myapp & PID=$!
sleep 5
kill $PID 2>/dev/null
echo "建议: 检查是否有特权操作需求"

# 7. 性能基准
echo -e "\n[7] 性能基准测试"
echo "CPU: $(top -b -n1 | grep "$APP_NAME" | awk '{print $9}')%"
echo "内存: $(ps aux | grep "$APP_NAME" | awk '{print $4}')%"

echo -e "\n=========================================="
echo "迁移建议:"
echo "1. 创建Dockerfile封装应用"
echo "2. 使用docker-compose定义服务依赖"
echo "3. 配置健康检查"
echo "4. 设置资源限制"
echo "5. 准备回滚方案"
echo "=========================================="
```

**迁移步骤**:

```bash
#!/bin/bash
# migrate-vm-to-container.sh - 虚拟机应用容器化脚本

APP_NAME="myapp"
VM_HOST="oldvm.company.com"
REGISTRY="registry.company.com"

echo "=========================================="
echo "虚拟机到容器迁移: $APP_NAME"
echo "=========================================="

# 第1阶段: 应用打包
echo -e "\n[阶段1/4] 从虚拟机打包应用..."
ssh root@$VM_HOST << 'EOF'
    cd /opt/myapp
    tar czf /tmp/myapp.tar.gz .
EOF

scp root@$VM_HOST:/tmp/myapp.tar.gz ./

# 第2阶段: 创建Dockerfile
echo -e "\n[阶段2/4] 生成Dockerfile..."
cat > Dockerfile <<'DOCKERFILE'
FROM ubuntu:22.04

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    libssl3 \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN useradd -m -u 1000 appuser

# 复制应用文件
WORKDIR /app
COPY myapp.tar.gz .
RUN tar xzf myapp.tar.gz && rm myapp.tar.gz
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["./start.sh"]
DOCKERFILE

# 第3阶段: 构建镜像
echo -e "\n[阶段3/4] 构建Docker镜像..."
docker build -t $REGISTRY/$APP_NAME:v1.0.0 .

# 第4阶段: 测试运行
echo -e "\n[阶段4/4] 测试容器..."
docker run -d --name ${APP_NAME}_test \
    -p 8080:8080 \
    -e DB_HOST=postgres.company.com \
    -e DB_PORT=5432 \
    $REGISTRY/$APP_NAME:v1.0.0

# 健康检查
echo "等待服务启动..."
for i in {1..30}; do
    if curl -sf http://localhost:8080/health > /dev/null; then
        echo "✓ 容器运行正常"
        break
    fi
    sleep 2
done

# 清理测试容器
docker stop ${APP_NAME}_test
docker rm ${APP_NAME}_test

# 推送镜像
echo -e "\n推送镜像到仓库..."
docker push $REGISTRY/$APP_NAME:v1.0.0

echo -e "\n=========================================="
echo "✓ 迁移完成"
echo "下一步:"
echo "1. 创建docker-compose.yml"
echo "2. 配置生产环境变量"
echo "3. 执行灰度发布"
echo "=========================================="
```

### 19.4.2 从Kubernetes迁移到Docker Swarm

**转换工具**:

```python
#!/usr/bin/env python3
# k8s-to-swarm.py - Kubernetes YAML转Docker Stack

import yaml
import sys

def convert_deployment(k8s_yaml):
    """转换Deployment到Docker Service"""
    spec = k8s_yaml['spec']
    template = spec['template']

    service = {
        'image': template['spec']['containers'][0]['image'],
        'deploy': {
            'replicas': spec.get('replicas', 1),
            'restart_policy': {
                'condition': 'on-failure'
            }
        }
    }

    # 转换资源限制
    if 'resources' in template['spec']['containers'][0]:
        resources = template['spec']['containers'][0]['resources']
        service['deploy']['resources'] = {}

        if 'limits' in resources:
            service['deploy']['resources']['limits'] = {
                'cpus': resources['limits'].get('cpu', '1'),
                'memory': resources['limits'].get('memory', '512M')
            }

        if 'requests' in resources:
            service['deploy']['resources']['reservations'] = {
                'cpus': resources['requests'].get('cpu', '0.5'),
                'memory': resources['requests'].get('memory', '256M')
            }

    # 转换环境变量
    if 'env' in template['spec']['containers'][0]:
        service['environment'] = []
        for env in template['spec']['containers'][0]['env']:
            service['environment'].append(f"{env['name']}={env.get('value', '')}")

    # 转换端口
    if 'ports' in template['spec']['containers'][0]:
        service['ports'] = []
        for port in template['spec']['containers'][0]['ports']:
            service['ports'].append(f"{port['containerPort']}:{port['containerPort']}")

    return service

def main():
    if len(sys.argv) < 2:
        print("用法: k8s-to-swarm.py <k8s.yaml>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        k8s_docs = yaml.safe_load_all(f)

        stack = {
            'version': '3.8',
            'services': {}
        }

        for doc in k8s_docs:
            if doc['kind'] == 'Deployment':
                name = doc['metadata']['name']
                stack['services'][name] = convert_deployment(doc)

        print(yaml.dump(stack, default_flow_style=False))

if __name__ == '__main__':
    main()
```

---

## 19.5 避坑指南

### 19.5.1 常见错误

**1. 容器时区问题**:

```dockerfile
# ❌ 错误: 容器使用UTC时区
FROM alpine
CMD ["date"]

# ✅ 正确: 设置时区
FROM alpine
RUN apk add --no-cache tzdata
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
CMD ["date"]
```

**2. 日志丢失问题**:

```dockerfile
# ❌ 错误: 日志写入文件
CMD ./app > /var/log/app.log 2>&1

# ✅ 正确: 日志输出到stdout/stderr
CMD ./app
```

**3. PID 1僵尸进程问题**:

```dockerfile
# ❌ 错误: 使用shell启动
CMD ./start.sh

# ✅ 正确: 使用exec形式或dumb-init
FROM alpine
RUN apk add --no-cache dumb-init
ENTRYPOINT ["dumb-init", "--"]
CMD ["./app"]
```

**4. 文件权限问题**:

```dockerfile
# ❌ 错误: root用户创建文件
COPY app.jar /app/
USER appuser
CMD java -jar /app/app.jar

# ✅ 正确: 设置正确的所有者
COPY --chown=appuser:appuser app.jar /app/
USER appuser
CMD ["java", "-jar", "/app/app.jar"]
```

**5. 环境变量展开问题**:

```yaml
# ❌ 错误: 单引号阻止变量展开
services:
  app:
    command: 'echo $PATH'

# ✅ 正确: 使用双引号或不加引号
services:
  app:
    command: echo $PATH
```

### 19.5.2 性能陷阱

**1. 过度使用bind mount**:

```yaml
# ❌ 慢: bind mount需要文件系统同步
volumes:
  - ./app:/app

# ✅ 快: 使用named volume
volumes:
  - app_data:/app

volumes:
  app_data:
```

**2. 过多的层导致镜像臃肿**:

```dockerfile
# ❌ 错误: 每个RUN创建一层
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y vim
RUN apt-get clean

# ✅ 正确: 合并命令
RUN apt-get update && apt-get install -y \
    curl \
    vim \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
```

**3. 不使用.dockerignore**:

```bash
# .dockerignore
node_modules
*.log
.git
.DS_Store
coverage
*.md
```

**4. 使用latest标签**:

```yaml
# ❌ 不推荐: latest不稳定
services:
  app:
    image: myapp:latest

# ✅ 推荐: 使用明确版本
services:
  app:
    image: myapp:v1.2.3
```

### 19.5.3 监控盲点

**关键指标监控清单**:

```yaml
# prometheus-alerts.yml
groups:
  - name: docker_health
    interval: 30s
    rules:
      # 1. 容器重启频繁
      - alert: ContainerRestartingTooOften
        expr: rate(container_restart_count[15m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "容器 {{ $labels.container }} 重启频繁"

      # 2. 容器OOM
      - alert: ContainerOOMKilled
        expr: container_oom_events_total > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "容器 {{ $labels.container }} 发生OOM"

      # 3. 磁盘空间不足
      - alert: DockerDiskSpaceLow
        expr: (node_filesystem_avail_bytes{mountpoint="/var/lib/docker"} / node_filesystem_size_bytes) < 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Docker数据目录空间不足 < 10%"

      # 4. 镜像拉取失败
      - alert: ImagePullFailed
        expr: increase(docker_image_pull_errors_total[5m]) > 3
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "镜像拉取失败次数过多"

      # 5. Swarm节点不可用
      - alert: SwarmNodeUnavailable
        expr: swarm_node_status != 1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Swarm节点 {{ $labels.node_name }} 不可用"
```

---

## 19.6 企业级最佳实践总结

### 19.6.1 镜像管理

1. **使用语义化版本**: `v1.2.3`
2. **锁定基础镜像SHA**: `FROM node:18@sha256:...`
3. **定期扫描漏洞**: Trivy/Snyk
4. **清理无用镜像**: `docker image prune -a`

### 19.6.2 资源规划

```yaml
# 资源配置范例
services:
  # 高流量API
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  # 后台任务
  worker:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  # 数据库
  postgres:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

### 19.6.3 日志与监控

```yaml
# 统一日志配置
x-logging: &default-logging
  driver: fluentd
  options:
    fluentd-address: "fluentd.company.com:24224"
    fluentd-async: "true"
    fluentd-retry-wait: "1s"
    fluentd-max-retries: "10"
    tag: "{{.Name}}"

services:
  app:
    logging: *default-logging
```

### 19.6.4 备份策略

```bash
#!/bin/bash
# backup-docker-volumes.sh - Docker卷备份脚本

BACKUP_DIR="/backup/docker-volumes"
DATE=$(date +%Y%m%d_%H%M%S)

# 获取所有卷
VOLUMES=$(docker volume ls -q)

for volume in $VOLUMES; do
    echo "备份卷: $volume"

    # 创建临时容器挂载卷并备份
    docker run --rm \
        -v "$volume":/source:ro \
        -v "$BACKUP_DIR":/backup \
        alpine \
        tar czf "/backup/${volume}_${DATE}.tar.gz" -C /source .

    echo "✓ 备份完成: ${volume}_${DATE}.tar.gz"
done

# 删除7天前的备份
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete
```

---

*（第19章完成,约1800行。全书19章全部完成!）*

## 🎉 全书完结

恭喜您完成《Docker底层原理与生产实战指南》的学习!

### 📚 全书章节回顾

1. **第1-5章**: Docker核心概念与底层原理
2. **第6-8章**: 镜像构建与优化
3. **第9-12章**: 容器运行时与编排
4. **第13章**: 生产环境部署架构
5. **第14章**: 高可用性与灾难恢复
6. **第15章**: 监控告警体系
7. **第16章**: 日志收集与分析
8. **第17章**: 性能优化
9. **第18章**: 故障排查
10. **第19章**: 最佳实践与案例

### 🎯 学习路径建议

- **初学者**: 第1-8章 → 第9-12章
- **运维工程师**: 第13-16章 → 第17-18章
- **架构师**: 全书系统学习

### 📖 延伸阅读

- Docker官方文档: https://docs.docker.com
- Docker Swarm文档: https://docs.docker.com/engine/swarm/
- Kubernetes进阶学习
- 云原生技术栈

---

*感谢您的阅读!如有问题,欢迎交流讨论。*
