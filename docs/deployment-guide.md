# 三服务部署与交接说明

根目录 `docker-compose.yml` 是完整部署配置草案。它遵守共同约定，包含反馈、统计和 PostgreSQL 三个服务，但完整构建和联调必须等待 Hanyan 的正式代码。`compose.dev.yml` 继续用于当前统计服务独立开发。

## 接入前需要的文件

| 文件 | 负责人 | 接入要求 |
|---|---|---|
| `feedback/Dockerfile` 及源码、依赖 | Hanyan | 使用 `feedback/` 作为构建上下文，监听 `0.0.0.0:6110` |
| `database/init.sql` | Hanyan | 按共同约定创建 `public.feedback`，不自动插入测试数据 |
| `dashboard/Dockerfile` 及源码、依赖 | Zhanghongyi | 已实现，监听 `0.0.0.0:6111` |
| `.env` | 部署者 | 从 `.env.example` 复制并替换本地密码，不提交 Git |

Hanyan 的文件到位前，可以运行 `docker compose -f docker-compose.yml config --quiet` 检查语法，但这不证明缺失的文件存在，也不证明系统能够运行。执行 `sh scripts/check-integration.sh` 会列出缺失文件，阻止把草案误认为已可联调。不要创建空的反馈服务或用测试脚本冒充她的正式交付。

## 完整系统部署

在代码到齐后，在课程虚拟机准备 Docker Engine 和 Compose 插件；本地也可以用 Docker Desktop。首次构建需要访问官方镜像和依赖仓库。

1. 同步整合后的代码，复制 `.env.example` 为 `.env`，填写密码。
2. 执行 `sh scripts/check-integration.sh` 检查文件和配置。
3. 如果本机的开发统计服务正在使用 6111，先执行 `docker compose -f compose.dev.yml down`，保留开发数据卷。
4. 从仓库根目录执行老师要求的命令：

```bash
docker compose up --build
```

打开 `http://虚拟机地址:6110` 和 `http://虚拟机地址:6111`。只有 6110、6111 映射到宿主机；PostgreSQL 仅在内部网络使用 5432。两个应用的 `DB_HOST=db`、`DB_PORT=5432` 在完整配置中固定，以避免把本地调试地址带入容器。

数据库将 `.env` 的数据库名、用户名和密码映射到 `POSTGRES_*`。初始化脚本只读挂载，缺失时不会被自动创建成目录。数据库健康检查通过后启动应用；统计服务的健康检查访问真实页面，因此数据库查询失败也会使统计服务不健康。反馈服务的完整可用性必须通过实际提交验证，目前未擅自假定它有额外健康检查路由。

完整系统使用 `cisc7403-course-feedback` 项目及自己的 `feedback_data` 数据卷；开发环境使用另一个项目和数据卷。两者不共享反馈，切换后不会自动带入开发测试数据。

## 运行与停止

```bash
docker compose ps
docker compose logs feedback
docker compose logs dashboard
docker compose down
```

普通 `down` 保留数据库数据卷。不要为解决启动问题随意删除数据卷。已有数据卷上修改 `.env` 密码或初始化脚本不会自动更新数据库，需要单独处理数据库密码或表结构迁移。

## 联调验收

- [ ] 在空数据卷上创建正式表，初始记录数为零。
- [ ] 6110 页面提交反馈成功，日志记录难度与主题。
- [ ] 6111 页面刷新后总数、平均难度和四主题计数准确。
- [ ] 三服务停止再启动后数据仍然存在。
- [ ] 在课程虚拟机确认端口可访问，并保存最终截图。

## 独立从零复现的方法

从一个新克隆的 `zhanghongyi` 工作目录开始，不复制原目录的 `.env` 或数据卷。准备新的 `.env` 密码；若旧页面占用 6111，可将 `DASHBOARD_PORT` 改为另一个空闲端口，例如 16111。此变量仅影响开发配置，完整配置仍固定 6111。

每次检查选择新的项目名称。下面的 `cisc7403-repro-example` 必须尚未使用，后续命令保持同一名称：

```bash
docker compose -p cisc7403-repro-example -f compose.dev.yml config --quiet
docker compose -p cisc7403-repro-example -f compose.dev.yml build --no-cache db-check dashboard
docker compose -p cisc7403-repro-example -f compose.dev.yml up -d --wait db dashboard
docker compose -p cisc7403-repro-example -f compose.dev.yml run --rm db-check
docker compose -p cisc7403-repro-example -f compose.dev.yml exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < dev/sample-feedback.sql
docker compose -p cisc7403-repro-example -f compose.dev.yml run --rm db-check
docker compose -p cisc7403-repro-example -f compose.dev.yml run --rm dashboard python -m unittest discover -s dashboard/tests -v
```

通过映射端口访问真实网页，检查空表时暂无数据，加载样例后总数 3、平均难度 3.00、Docker 2、Kubernetes 1、其他 0。随后 `down` 再 `up -d --wait db dashboard`，检查数据仍在。最后用同一项目名执行 `down` 停止复现容器并保留数据卷。

这验证新目录、新配置、新数据库与不使用应用构建缓存的复现。若宿主机已有基础镜像，Docker 可以复用它；这不等同于全新操作系统或另一种 CPU 架构验证，也不替代课程虚拟机验收。
