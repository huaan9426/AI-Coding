1. 基础信息类

bash



```bash
docker version                  # 查看 Docker 客户端和服务端版本
docker info                     # 查看 Docker 系统信息（包含容器数、镜像数、存储驱动等）
docker system df                # 查看 Docker 磁盘占用情况（镜像、容器、卷、构建缓存）
```

2. 镜像管理（image）

bash



```bash
docker images                   # 列出本地所有镜像
docker images -a                # 列出所有镜像（包括中间层）
docker images -q | sort -u      # 只显示镜像 ID 并去重

docker pull nginx:1.25          # 拉取指定版本镜像
docker pull nginx:latest        # 拉取最新版（latest 标签）

docker build -t myapp:1.0 .     # 当前目录 Dockerfile 构建镜像，标签为 myapp:1.0
docker build --no-cache -t app . # 强制不使用缓存重新构建

docker rmi nginx:latest         # 删除指定镜像
docker rmi $(docker images -q -f dangling=true)  # 删除悬空镜像（无人使用的）
docker image prune -a -f       # 一键清理所有不被任何容器使用的镜像（慎用 -a）

docker history nginx:latest     # 查看镜像每一层构建历史
docker inspect nginx:latest     # 查看镜像详细信息（标签、环境变量、入口点等）

docker tag myapp:1.0 myapp:latest      # 给镜像打新标签
docker push username/myapp:1.0         # 推送到 Docker Hub（或私有仓库）
```

3. 容器生命周期

bash



```bash
docker run nginx:latest                    # 启动新容器（默认前台）
docker run -d nginx                        # 后台运行（daemon）
docker run -d --name web1 -p 8080:80 nginx   # 常用组合：后台、命名、端口映射
docker run --restart=always ...            # 容器退出自动重启（生产推荐）

docker ps               # 查看运行中的容器
docker ps -a            # 查看所有容器（包括已停止的
docker ps -q            # 只显示运行中容器的 ID
docker ps -aq           # 所有容器的 ID

docker start web1       # 启动已停止的容器
docker stop web1        # 停止运行中的容器
docker restart web1     # 重启容器

docker rm web1                         # 删除已停止的容器
docker rm -f $(docker ps -aq)          # 强制删除所有容器（危险操作）
docker container prune -f              # 一键清理所有已停止的容器

docker logs web1              # 查看容器日志
docker logs -f web1           # 实时查看日志（类似 tail -f）
docker logs --tail 100 web1   # 只看最后 100 行

docker exec -it web1 bash     # 进入运行中的容器（交互式 bash）
docker exec -it web1 sh       # 如果没有 bash，用 sh
```

4. 资源限制与常用运行参数

bash



```bash
docker run -d \
  --name mysql \
  --restart=always \
  -p 3306:3306 \
  -v /data/mysql:/var/lib/mysql \
  -e MYSQL_ROOT_PASSWORD=123456 \
  -m 2g --cpus="2" \
  mysql:8.0
```

常用参数说明：

- -d：后台运行
- --name：指定容器名字
- -p 宿主机端口:容器端口：端口映射
- -v 宿主机路径:容器路径：数据卷挂载（持久化）
- -e KEY=VALUE：设置环境变量
- --restart=always|on-failure：重启策略
- -m：限制内存
- --cpus：限制 CPU 核心数
- --network：指定网络（bridge、host、none 或自定义网络）
- 容器资源监控

bash



```bash
docker stats                   # 实时查看所有容器 CPU、内存、网络、IO 使用情况（类似 top）
docker top web1                # 查看容器内进程（类似 ps aux）
```

6. 网络管理

bash



```bash
docker network ls                       # 列出所有网络
docker network create mynet             # 创建桥接网络
docker run --network mynet ...          # 容器加入指定网络
docker run --network host ...           # 直接使用宿主机网络（无隔离（性能最高）
```

7. 数据卷（Volume）管理（推荐方式）

bash



```bash
docker volume create mydata             # 创建命名卷
docker volume ls
docker volume prune                     # 清理未使用的卷

docker run -v mydata:/app/data ...      # 使用命名卷（推荐
docker run -v /host/path:/container/path ... # 直接绑定宿主机目录（开发常用）
```

8. Docker Compose（多容器编排神器）

bash



```bash
docker-compose up -d                    # 后台启动所有服务
docker-compose down                     # 停止并删除容器+网络
docker-compose logs -f                  # 查看所有服务日志
docker-compose exec app bash           # 进入某个服务容器
docker-compose restart nginx            # 重启单个服务
```

9. 清理命令（定期执行防止磁盘爆掉）

bash



```bash
# 一键清理脚本（生产慎用，建议加 -f 强制）
docker system prune -a --volumes -f
# 分步清理更安全：
docker container prune -f      # 清理停止的容器
docker image prune -f           # 清理悬空镜像
docker volume prune -f          # 清理未使用卷
docker builder prune -f         # 清理构建缓存（非常占空间！）
```

10. 常用组合技巧（实战必备）

bash



```bash
# 一行命令启动常用开发环境
docker run -d --name postgres -e POSTGRES_PASSWORD=123456 -p 5432:5432 postgres:15

# 查看某个容器 IP
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' web1

# 复制文件到/从容器
docker cp host_file.txt web1:/tmp/
docker cp web1:/var/log/app.log ./

# 导出/导入镜像（迁移用）
docker save nginx:latest > nginx.tar
docker load < nginx.tar
```

