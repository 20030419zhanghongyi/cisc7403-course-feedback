# CISC7403 Course Feedback System

课程反馈系统作业。Hanyan 负责反馈与正式数据库脚本，Zhanghongyi 负责统计与整体部署。接口见 [共同约定](docs/team-agreement.md)。

## 当前阶段

`zhanghongyi` 分支已准备统计服务目录、数据库连接模块和独立开发数据库。此阶段没有统计网页、反馈服务或最终三服务 `docker-compose.yml`，不代表作业已经完成。

`compose.dev.yml` 仅用于第一阶段，不需要 Hanyan 的代码。临时表结构在 `dev/init/01-schema.sql`；联调时改为挂载她提供的 `database/init.sql`。正式初始化不会加入测试数据。

## 复现环境

需要 Git、可运行 Linux 容器的 Docker 环境和 Docker Compose。Mac 或 Windows 可以用 Docker Desktop，Linux 可以安装 Docker Engine 与 Compose 插件，不要求 Docker Desktop。项目不依赖开发者电脑上的 Python、pip 或 PostgreSQL。

首次运行需能访问镜像仓库和 Python 包仓库。应用依赖版本记录在 `dashboard/requirements.txt`，数据库镜像版本记录在 Compose 配置。镜像标签不是不可变摘要，当前配置不承诺逐字节相同构建；后续可固定镜像摘要。跨设备无需复制本机虚拟环境。

从 GitHub 克隆仓库并切换到 `zhanghongyi` 分支后，在仓库根目录执行下列步骤。Windows 可在 Git Bash 或 WSL 中执行这些命令。

### 准备本地配置

```bash
cp .env.example .env
```

将 `.env` 中的 `DB_PASSWORD` 改为自己的本地密码，其余值保持示例约定。`.env` 不提交到仓库。Compose 将 `DB_NAME`、`DB_USER`、`DB_PASSWORD` 映射到数据库容器的 `POSTGRES_*` 变量，将五个 `DB_*` 变量注入检查容器。

### 启动数据库并验证空表

```bash
docker compose -f compose.dev.yml up -d --wait db
docker compose -f compose.dev.yml run --rm --build db-check
```

预期输出 `connection: ok`、`read_only: on`、`record_count: 0`。连接检查在 Docker 内运行，通过 `db:5432` 访问数据库；数据库不映射宿主机端口。

### 添加独立测试数据

以下命令仅用于这个开发 Compose 项目，脚本遇到非空表会拒绝执行，不会删除或覆盖已有反馈。

```bash
docker compose -f compose.dev.yml exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < dev/sample-feedback.sql
docker compose -f compose.dev.yml run --rm db-check
```

预期读取三条记录：`(1, Docker)`、`(3, Docker)`、`(5, Kubernetes)`，其中括号内数字是难度。后续统计应得到总数 3、平均难度 3.00、Docker 2、Kubernetes 1、其他主题 0。

### 停止与再次启动

```bash
docker compose -f compose.dev.yml down
docker compose -f compose.dev.yml up -d --wait db
```

普通 `down` 会保留本项目的数据卷，下次启动仍有之前的数据。不要添加删除数据卷的参数。初始化脚本仅在空数据目录首次启动时执行；修改脚本或 `.env` 密码不会自动修改已有数据库，需先规划迁移或密码更新。

## 文件说明

- `dashboard/db.py`：读取五个连接变量，验证配置，建立只读连接。
- `dashboard/requirements.txt`：当前数据库驱动依赖；网页依赖在下一阶段添加。
- `compose.dev.yml`：独立开发项目，使用独立网络与数据卷，不修改其他 Docker 项目。
- `dev/Dockerfile.check`：临时连接检查镜像，不是最终统计服务镜像。
- `dev/init/01-schema.sql`：与共同约定一致的临时测试表。
- `dev/sample-feedback.sql`：手动加载的测试记录。
- `dev/checks/check_database.py`：从真实 PostgreSQL 读取反馈并报告连接结果。

下一阶段实现统计查询和页面。完整系统最终仍需在课程虚拟机通过 `docker compose up --build` 验证。
