# Hanyan 工作范围定义

Hanyan 负责同学 A 部分：反馈功能与数据库。目标是让学生可以提交有效反馈，将记录保存到 PostgreSQL，并留下可通过 Docker 查看的一条成功提交日志。开发分支为 `hanyan`，最终合并到 `main`。

## 负责的工作

| 工作项 | 交付要求 |
|---|---|
| 反馈网页 | 提供难度 1–5 和四个主题的选择表单；写入成功后明确显示提交成功 |
| 提交处理 | 校验难度和主题；每次有效提交插入一条记录；保存失败不能提示成功 |
| 应用日志 | 数据库写入成功后记录难度和主题，输出到标准输出或标准错误，支持 `docker compose logs feedback` 查看 |
| 数据库设计 | 提供反馈表初始化 SQL，包含主键、必填和取值约束 |
| 反馈容器 | 提供 Dockerfile、依赖清单及运行入口；从环境变量读取数据库配置 |
| 报告材料 | 提供反馈页面、提交成功和成功日志截图，整理数据库设计、实现困难与实际贡献 |

## 文件归属与交接

主要维护 `feedback/` 和 `database/`。至少交付：

- `feedback/` 下的应用源码、页面、依赖清单和 `Dockerfile`。
- `database/init.sql`，用于首次启动数据库时建表。
- 反馈服务启动方式、配置说明及可供联调的输入样例。

整体 Compose 配置由 Zhanghongyi 维护。Hanyan 提供数据库初始化路径、反馈容器启动要求，并配合解决连接和启动问题。统计页面和统计查询由 Zhanghongyi 实现。

## 共同接口约定

以下是本组的初始实现约定，用来支持双方独立开发；具体命名不是老师强制要求。若需要修改，先与另一位同学协商，并同步更新这两份文档及相关代码。

| 项目 | 约定 |
|---|---|
| Compose 服务名 | `feedback`、`dashboard`、`db` |
| 数据库 | 官方 PostgreSQL 镜像；数据库名 `course_feedback`，用户 `course_app` |
| 应用连接配置 | 两个应用读取 `DB_HOST`、`DB_PORT`、`DB_NAME`、`DB_USER`、`DB_PASSWORD`；由 Compose 注入 |
| 容器内数据库地址 | `DB_HOST=db`，`DB_PORT=5432`；不能用 `localhost` |
| 数据表 | `public.feedback` |
| 字段 | `id SERIAL PRIMARY KEY`、`difficulty INTEGER NOT NULL`、`topic VARCHAR(32) NOT NULL` |
| 数据约束 | `difficulty` 为 1–5；`topic` 仅允许下面四个字符串；数据库约束与应用校验保持一致 |
| 主题字符串 | `Virtual Machine`、`Docker`、`Kubernetes`、`Serverless`，大小写和空格一致 |
| 反馈页面 | `/`；应用监听 `0.0.0.0:6110`，宿主机映射 `6110:6110` |
| 统计页面 | `/`；应用监听 `0.0.0.0:6111`，宿主机映射 `6111:6111` |
| 数据访问 | 两个应用直接连接 PostgreSQL；统计服务只查询反馈数据，不依赖反馈服务提供接口 |
| 数据库初始化 | Hanyan 提供 `database/init.sql`；Zhanghongyi 在 Compose 中挂载到 `/docker-entrypoint-initdb.d/` |
| 本地配置 | Zhanghongyi 提供 `.env.example` 和启动说明；实际密码放本地 `.env`，不提交到 Git |

数据库初始化脚本只会在 PostgreSQL 数据目录首次初始化时自动执行。已有数据卷上的表结构变更需要双方另行协调，不能默认重新启动就会执行新脚本。

## 完成验收标准

- [ ] 浏览器访问宿主机 6110 端口，可填写难度与主题。
- [ ] 一次有效提交新增一条数据库记录，页面明确提示成功。
- [ ] 难度超出 1–5 或主题不在约定列表时，不写入数据库；后端也进行校验。
- [ ] 保存失败时不显示成功，不记录成功日志。
- [ ] 成功日志可通过 Docker 命令查看，包含本次难度和主题。
- [ ] 首次初始化数据库可以创建约定的数据表，反馈服务能够使用 `db` 连接。
- [ ] Dockerfile 能构建，应用在容器中运行，并完成与统计服务的联调。
- [ ] 向 Zhanghongyi 提供负责部分的报告文字和截图。

## 协作与共同交付

1. 开始开发前，将 `main` 的最新内容合并到各自开发分支，获取本文件和 `course-materials` 中的老师原始资料。
2. 在自己的分支提交负责的代码；涉及对方负责的文件或共同接口时，先同步变更。
3. 完成后向 `main` 发起 Pull Request，由另一位同学检查，再合并。合并冲突由双方一起处理。
4. 双方在课程虚拟机上完成最终联调，核对两个页面、数据库、三个容器和提交日志，并共同整理报告。
5. 报告正文最多 3 页，封面和源代码不计入；应覆盖架构、容器部署、运行截图、挑战及成员贡献。
6. 提交完整源代码、两个 Dockerfile 和 `docker-compose.yml`。每个人单独填写、签署并提交角色声明表。

前端简单 HTML 即可；图表、认证、自动刷新和其他额外功能均不属于本次必做范围。成员贡献应按实际完成情况填写。

## 老师原始资料

- [作业说明 PDF](../course-materials/Project1_Course_Feedback_Microservices.pdf)
- [个人角色声明表](../course-materials/CISC7403Role%20Declaration%20Page.docx)
