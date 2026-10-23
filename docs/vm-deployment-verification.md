# 合并后的虚拟机部署与验收记录

验证日期：2026 年 10 月 23 日。本记录整理 PR #1、PR #2 合并后进行的虚拟机部署、功能验证及报告截图。

实际部署的代码版本为 `main` 提交 [`dda5f186e3c9ae889843839aa24bbe6d0e5722ba`](https://github.com/20030419zhanghongyi/cisc7403-course-feedback/commit/dda5f186e3c9ae889843839aa24bbe6d0e5722ba)。本材料提交到 Zhanghongyi 的个人分支，记录的是该合并版本的结果；复现完整系统时应使用上述提交。

## 环境与部署

| 项目 | 本次环境 |
|---|---|
| 虚拟化平台 | VirtualBox，虚拟机名称 Ubuntu 24.04 |
| 客户机 | Ubuntu 24.04，ARM，4 CPU，8 GB 内存 |
| Docker / Compose | Docker 29.8.2 / Docker Compose v5.6.0 |
| 虚拟机项目目录 | `/home/hongyizhang/cisc7403-course-feedback` |
| 三个服务 | `feedback`、`dashboard`、`db` |
| 数据库镜像 | 官方 `postgres:17.6-bookworm` |
| 持久化卷 | `cisc7403-course-feedback_feedback_data` |

从合并后的 Git 提交使用 `git archive` 导出源码，传入虚拟机并核对归档校验和后解压。部署目录不含 `.git`。在虚拟机内单独生成 `.env` 和随机数据库密码，文件权限设为 `0600`；本次提交不包含该文件或密码。

在虚拟机项目目录完成集成文件检查，并实际执行以下 Compose 启动命令：

```sh
sudo docker compose up --build -d --wait --wait-timeout 180
```

两个应用通过 Compose 内部网络中的 `db:5432` 连接数据库。虚拟机仅发布应用端口 `6110` 和 `6111`，数据库没有发布到宿主机；`docker compose ps` 中的 `5432/tcp` 是容器端口。

虚拟机内的访问地址是 `http://127.0.0.1:6110/`（反馈）和 `http://127.0.0.1:6111/`（统计）。为从 Mac 浏览器验证虚拟机中的服务，另设置了两条 VirtualBox NAT 转发：Mac 的 `127.0.0.1:6110`、`127.0.0.1:6111` 分别转发到虚拟机的对应端口。网页截图来自 Mac 浏览器，访问的是虚拟机中运行的应用；终端截图来自 Ubuntu 虚拟机。访问时需保持虚拟机和服务运行。

## 虚拟机实际验证结果

| 检查项 | 观察结果 |
|---|---|
| 镜像构建与首次启动 | 反馈与统计镜像构建成功，PostgreSQL 初始化完成，三个服务启动 |
| 空数据库页面 | 总数为 0，平均难度显示 No data yet |
| 浏览器真实提交 | 依次提交 `(1, Docker)`、`(3, Docker)`、`(5, Kubernetes)`，均显示成功提示 |
| 统计结果 | 总数 3，平均难度 3.00；Virtual Machine 0、Docker 2、Kubernetes 1、Serverless 0 |
| 五种无效输入 | 难度 0、6、2.5，非法主题、空数据均返回 HTTP 400；统计总数仍为 3 |
| 容器状态 | 三个服务均为 Up；`dashboard` 和 `db` 为 healthy；`feedback` 没有配置 healthcheck，已通过实际 HTTP 提交验证 |
| 端口 | feedback 发布 6110，dashboard 发布 6111，db 的 5432 保持内部访问 |
| 成功提交日志 | 三条 Feedback submitted successfully 日志分别包含 difficulty/topic：1/Docker、3/Docker、5/Kubernetes，与统计页面一致 |

成功日志通过以下命令读取。日志时间为 UTC，与 Ubuntu 桌面显示的本地时间相差 8 小时。

```sh
cd ~/cisc7403-course-feedback
sudo docker compose ps
sudo docker compose logs --no-color feedback | grep 'Feedback submitted successfully'
```

当前演示数据保留上述三条反馈，采集日志时没有再次提交样例。

## 截图与报告对应关系

截图保存在 [`evidence/2026-10-23/`](evidence/2026-10-23/)；均为原始截图，没有修改页面或日志中的数据。

| 文件 | 内容 | 用途 |
|---|---|---|
| [01-vm-build-success.png](evidence/2026-10-23/01-vm-build-success.png) | 虚拟机内构建及启动结果 | 部署补充证据 |
| [02-feedback-form.jpg](evidence/2026-10-23/02-feedback-form.jpg) | 反馈表单 | 反馈页截图 |
| [03-feedback-success.jpg](evidence/2026-10-23/03-feedback-success.jpg) | 第三次真实提交后的成功提示与表单 | 建议作为报告的反馈页截图 |
| [04-dashboard-three-records.jpg](evidence/2026-10-23/04-dashboard-three-records.jpg) | 三条反馈对应的统计结果 | 统计页截图 |
| [05-vm-containers.png](evidence/2026-10-23/05-vm-containers.png) | 原始 Compose 状态输出，含容器名、镜像、状态及端口 | 运行容器截图 |
| [06-vm-status-and-success-logs.png](evidence/2026-10-23/06-vm-status-and-success-logs.png) | 简洁服务状态表和三条成功日志 | 同时覆盖运行容器与应用日志 |

老师要求的反馈页、统计页、运行容器、应用日志四类截图均已收集。报告可选用 03、04、06 三张，其中 06 同时覆盖后两类证据，以控制三页正文的篇幅。

## 验证边界与剩余交付

完整自动化集成测试已在 Mac 的 Docker 环境通过，结果见合并版本的 [PR 整合审查与验收记录](https://github.com/20030419zhanghongyi/cisc7403-course-feedback/blob/dda5f186e3c9ae889843839aa24bbe6d0e5722ba/docs/integration-review.md)。虚拟机内未完成 `scripts/test-full-stack.py` 全套测试；本次 VM 结果仅覆盖上表实际执行的操作。配置使用命名卷，但本次 VM 验证没有执行停止、重建后持久化测试，不能将主机上的该项结果当作 VM 实测结果。

仍需整理不超过三页正文的报告（封面和源码另计），包括架构、功能、容器化与部署、运行证据、挑战和实际成员贡献；提交完整源码、两个 Dockerfile 和 `docker-compose.yml`；每位成员独立填写、签署并提交角色声明。本文是验收材料，不是已完成的最终报告或签名声明。

日常恢复已部署服务可在虚拟机项目目录执行 `sudo docker compose up -d`。保留当前演示数据，不要执行会删除数据卷的 `docker compose down -v`。
