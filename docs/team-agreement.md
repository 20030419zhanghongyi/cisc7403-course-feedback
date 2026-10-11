# 双人开发接口与协作约定

本文件统一 Hanyan 与 Zhanghongyi 的数据库接口、容器配置和交接标准，供两人并行开发使用。Hanyan 负责反馈与数据库，Zhanghongyi 负责统计与整体部署。共同接口以本文件为统一维护入口。

状态：初始对齐方案，待双方核对；下方勾选项不代表已确认或已完成。老师的要求以 [作业说明](../course-materials/Project1_Course_Feedback_Microservices.pdf) 为准。具体命名、配置方式、数据持久化和错误处理属于本组实现约定。

## 责任与文件归属

| 负责人 | 开发分支 | 主要维护文件 | 对另一方的交付 |
|---|---|---|---|
| Hanyan | `hanyan` | `feedback/`、`database/init.sql` | 可运行的反馈服务、Dockerfile、依赖清单、正式建表脚本 |
| Zhanghongyi | `zhanghongyi` | `dashboard/`、`docker-compose.yml`、`.env.example`、`.gitignore`、`README.md` | 可运行的统计服务、Dockerfile、完整部署配置与启动说明 |
| 双方 | 合并到 `main` | 本文件、报告材料 | 接口变更确认、联调、课程虚拟机验证 |

各应用 Dockerfile 的构建上下文为自己的目录，即 `./feedback` 和 `./dashboard`；应用源码和依赖应放在对应目录。双方可以自行选择应用框架，只要遵守共同接口。

## 服务与端口

| 服务 | Compose 服务名 | 容器内监听地址 | 宿主机端口 | 职责 |
|---|---|---|---|---|
| 反馈 | `feedback` | `0.0.0.0:6110` | `6110` | 提交反馈并写入数据库 |
| 统计 | `dashboard` | `0.0.0.0:6111` | `6111` | 直接查询数据库并展示统计 |
| 数据库 | `db` | PostgreSQL 端口 `5432` | 默认不开放 | 保存反馈 |

两个网页入口均为 `/`。反馈表单的提交路由由 Hanyan 自行实现，统计服务不调用该路由，两者无需约定额外 HTTP API。两个应用通过 Compose 内部网络访问 `db:5432`，不能在应用容器内用 `localhost` 指向数据库。

## 数据库结构

数据库名为 `course_feedback`，连接用户为 `course_app`，表为 `public.feedback`。`id` 由数据库生成，应用插入时只传 `difficulty` 和 `topic`。

```sql
CREATE TABLE IF NOT EXISTS public.feedback (
    id SERIAL PRIMARY KEY,
    difficulty INTEGER NOT NULL CHECK (difficulty BETWEEN 1 AND 5),
    topic VARCHAR(32) NOT NULL CHECK (
        topic IN ('Virtual Machine', 'Docker', 'Kubernetes', 'Serverless')
    )
);
```

此 SQL 是双方接口基准；正式脚本由 Hanyan 在 `database/init.sql` 维护。表单标签可以自行设计，实际存储的主题必须使用上面的英文字符串，大小写和空格一致。前端显示中文时也不得将中文标签作为 `topic` 写入。

初次部署只建表，不自动加入演示数据。每次有效提交产生一条记录；本项目不要求登录、用户身份识别或重复提交去重。

## 环境变量

两个应用读取以下五个变量，由 Compose 注入；变量缺失或连接失败时应清晰报错，不静默回退到另一套数据库。

| 应用变量 | Compose 内的值 | 说明 |
|---|---|---|
| `DB_HOST` | `db` | 内部服务名 |
| `DB_PORT` | `5432` | 数据库内部端口 |
| `DB_NAME` | `course_feedback` | 数据库名 |
| `DB_USER` | `course_app` | 用户名 |
| `DB_PASSWORD` | 来自本地 `.env` | 不写死在源码或镜像中 |

PostgreSQL 容器使用官方镜像所需的变量：`POSTGRES_DB` 对应 `DB_NAME`，`POSTGRES_USER` 对应 `DB_USER`，`POSTGRES_PASSWORD` 对应 `DB_PASSWORD`。Zhanghongyi 在 Compose 中完成映射，保证三个服务使用一致的值。

仓库提交 `.env.example`，实际 `.env` 加入 `.gitignore`。示例仅使用明显占位密码，使用者按 README 准备本地配置后运行 `docker compose up --build`。日志和截图不得包含实际密码。

## 初始化与启动

- 数据库使用官方 PostgreSQL 镜像；具体镜像版本在 Compose 实现时固定，双方使用相同版本验证。
- 将 `./database/init.sql` 只读挂载为数据库容器中的 `/docker-entrypoint-initdb.d/01-init.sql`。
- 使用数据卷保存数据库数据。初始化脚本只在空数据目录首次初始化时自动执行；修改 SQL 不会自动更新已有数据库。
- Zhanghongyi 配置数据库健康检查及应用启动依赖；双方应用在连接不可用时给出明确错误，数据库恢复后能通过重试请求或重启服务恢复。
- 普通停止和重启应保留反馈。需要调整已有表结构时，双方先讨论迁移方案，不通过删除共享数据卷解决问题。
- 本地可以各用自己的 Docker 环境和数据库；最终在课程提供的虚拟机上验证整个系统。

## 功能结果约定

### 反馈服务

后端校验难度和主题；只有数据库提交成功才显示成功提示，并向标准输出或标准错误写成功日志。日志至少包含难度与主题，可通过 `docker compose logs feedback` 查看。校验或写入失败时显示错误，不记录成功提交。

### 统计服务

页面显示反馈总数、平均难度和全部四个主题计数，未被选择的主题显示 0。平均难度按所有记录的算术平均计算，显示时保留两位小数。没有记录时平均难度显示“暂无数据”或等价文字，不显示误导性的 0 分。数据库查询失败时显示错误，不伪装成空数据库。

浏览器刷新即可更新数据。统计服务只读反馈记录，不建表、不插入或修改反馈；正式建表由初始化脚本负责。

## 联调前可以独立完成的工作

Hanyan 在自己的环境验证建表、输入校验、提交入库、成功提示和日志，再验证反馈镜像能构建运行。Zhanghongyi 使用相同表结构和独立测试数据完成统计查询、页面、统计镜像，以及数据库加统计服务的局部部署验证。

正式建表脚本尚未交付时，Zhanghongyi 可按本文件临时建测试表；接入时改用 Hanyan 的正式脚本。无需等待反馈页面完成，也无需两人共用一个本地数据库。完整 Compose 的最终验收需要双方的源码与 Dockerfile 全部就绪。

测试数据只用于独立测试环境，不放入正式初始化脚本，不清空已有共享反馈。

## 共同验收样例

在空的独立测试数据库中，按顺序提交以下三条数据：

| 难度 | 主题 |
|---|---|
| 1 | Docker |
| 3 | Docker |
| 5 | Kubernetes |

预期总数为 3、平均难度为 3.00，主题计数依次为 Virtual Machine 0、Docker 2、Kubernetes 1、Serverless 0。

- [ ] 空表时页面显示总数 0、四个主题 0、平均难度暂无数据。
- [ ] 三条反馈分别提交成功，数据库新增三条记录，成功日志包含对应难度和主题。
- [ ] 刷新统计页面后显示上述预期结果。
- [ ] 非法难度或主题被拒绝，数据库记录数不变。
- [ ] 数据库不可用时两个页面明确反馈错误，不显示虚假成功或零条统计。
- [ ] 普通重启后记录仍然存在。
- [ ] 在课程虚拟机通过 `docker compose up --build` 启动三个容器并完成上述主要流程。

## 确认与变更流程

- [ ] Hanyan 已核对数据库结构、主题取值、环境变量、反馈端口和交接文件。
- [ ] Zhanghongyi 已核对统计口径、环境变量、构建上下文和部署路径。

双方在各自分支开发，开始前同步 `main`。通过 Pull Request 交付，由另一方检查后合并；最终报告与截图使用整合后的版本。

修改字段、主题字符串、环境变量、端口、构建目录或初始化路径前，先说明变更原因和受影响文件，取得另一方确认，再更新本文件及实现。这里的勾选应由实际核对者更新，不预先代填。

## 个人工作范围

- [Hanyan 工作范围](hanyan-work-scope.md)
- [Zhanghongyi 工作范围](zhanghongyi-work-scope.md)
