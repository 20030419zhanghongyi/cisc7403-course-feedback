# CISC7403 Course Feedback System

课程反馈系统作业。Hanyan 负责反馈与正式数据库脚本，Zhanghongyi 负责统计与整体部署。接口见 [共同约定](docs/team-agreement.md)。

## 当前阶段

`zhanghongyi` 分支已实现统计查询、只读网页、数据库连接模块和独立开发部署，并提供完整三服务 `docker-compose.yml` 草案。草案仍缺 Hanyan 的反馈服务与正式建表脚本，不能视为已完成联调或课程虚拟机验证。接入步骤及独立从零复现方法见 [三服务部署与交接说明](docs/deployment-guide.md)。

`compose.dev.yml` 用于统计服务独立开发，不需要 Hanyan 的代码。临时表结构在 `dev/init/01-schema.sql`；联调时改为挂载她提供的 `database/init.sql`。正式初始化不会加入测试数据。

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

### 查看统计网页

```bash
docker compose -f compose.dev.yml up -d --build --wait db dashboard
```

打开 [统计页面](http://localhost:6111)。页面展示总数、两位小数的平均难度及四个主题计数，点击 Refresh results 或刷新浏览器即可更新。没有反馈时显示 No data yet；连接或查询失败时显示暂不可用，不把错误显示成 0 条数据。页面不提供写入功能。

### 运行统计集成测试

```bash
docker compose -f compose.dev.yml run --rm dashboard python -m unittest discover -s dashboard/tests -v
```

测试连接真实 PostgreSQL，创建随机命名的独立测试数据库，验证空表、样例统计、新增数据后的刷新、只读路由、错误配置与实际连接失败。结束后只删除测试自身创建的数据库，不修改开发数据库的反馈记录。测试需要当前开发数据库用户具备创建数据库的权限；不要对共享或生产数据库运行。当前官方镜像初始化的开发用户满足此条件。

### 停止与再次启动

```bash
docker compose -f compose.dev.yml down
docker compose -f compose.dev.yml up -d --wait db dashboard
```

普通 `down` 会保留本项目的数据卷，下次启动仍有之前的数据。不要添加删除数据卷的参数。初始化脚本仅在空数据目录首次启动时执行；修改脚本或 `.env` 密码不会自动修改已有数据库，需先规划迁移或密码更新。

## 文件说明

- `dashboard/db.py`：读取五个连接变量，验证配置，建立只读连接。
- `dashboard/requirements.txt`：固定版本的数据库驱动、Flask 和 Gunicorn。
- `dashboard/stats.py`：用一条 SQL 查询总数、平均难度和四个主题计数。
- `dashboard/app.py` 和 `dashboard/templates/index.html`：只读统计页面；正常返回 200，查询失败返回 503。
- `dashboard/Dockerfile`：统计服务镜像，监听 6111 端口。
- `compose.dev.yml`：独立开发项目，使用独立网络与数据卷，不修改其他 Docker 项目。
- `dev/Dockerfile.check`：临时连接检查镜像，不是最终统计服务镜像。
- `dev/init/01-schema.sql`：与共同约定一致的临时测试表。
- `dev/sample-feedback.sql`：手动加载的测试记录。
- `dev/checks/check_database.py`：从真实 PostgreSQL 读取反馈并报告连接结果。

下一步接入 Hanyan 的正式建表脚本和反馈服务，完成整体配置与联调。完整系统最终仍需在课程虚拟机通过 `docker compose up --build` 验证。

## 部署准备与验证记录

- [三服务部署与交接说明](docs/deployment-guide.md)：完整配置草案、待交接文件、运行方法和独立复现步骤。
- [独立环境复现检查记录](docs/reproduction-check.md)：已通过的检查以及尚待联调、课程虚拟机验证的范围。
