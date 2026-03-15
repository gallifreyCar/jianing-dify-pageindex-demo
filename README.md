# 嘉宁测试电商 Dify + PageIndex 售后客服 Demo

这是一个本地可运行的售后客服示例项目，目标是用 `Dify + 官方 VectifyAI/PageIndex + DeepSeek` 搭一套不依赖旧向量库的新方案。

这个仓库主要包含：

- Dify Chatflow 工作流 DSL
- 官方 `VectifyAI/PageIndex` 的本地接入封装
- 嘉宁测试电商的 mock 售后知识文档
- mock 订单查询接口
- 对上游 `Dify` 和 `PageIndex` 的最小补丁

## 5 分钟快速开始

如果你只想尽快把 demo 跑起来，按这个顺序做：

1. 准备环境
   - 安装 Docker Desktop
   - 准备一个可用的 DeepSeek API Key
2. 启动 Dify
   - 拉取官方 `langgenius/dify`
   - 应用本仓库里的 `patches/dify-docker-compose.patch`
   - 在 Dify 的 `.env` 中补上 DeepSeek 相关环境变量
   - 启动 `docker compose up -d`
3. 准备官方 PageIndex
   - 拉取官方 `VectifyAI/PageIndex`
   - 应用 `patches/pageindex-utils.patch`
4. 放入本仓库内容
   - 使用 `dify_customer_service/pageindex_service.py`
   - 使用 `dify_customer_service/mock_docs/`
5. 导入工作流
   - 登录 Dify
   - 导入 `dify_customer_service/workflow_pageindex_customer_service.yml`
6. 开始测试
   - 文档问题：`退款规则是什么？`
   - 文档问题：`物流签收破损怎么处理？`
   - 订单问题：`帮我查一下订单 JN202603150001`

如果你想看更完整的使用说明，请直接跳到：

- [dify_customer_service/README.md](/Users/gallifreycar/Documents/Playground/jianing-dify-pageindex-demo/dify_customer_service/README.md)

## 仓库结构

- `dify_customer_service/`
  - 客服工作流 DSL
  - `pageindex_service.py`
  - mock 文档
  - mock 订单和文档接口
- `patches/dify-docker-compose.patch`
  - 给 Dify 本地 `docker-compose.yaml` 增加 `jianing_mock` 和 `pageindex_official`
- `patches/pageindex-utils.patch`
  - 给官方 PageIndex 增加 OpenAI-compatible `base_url` 支持，兼容 DeepSeek

## 适合谁用

- 想把老旧 RAG 客服方案替换成新的文档检索流程
- 想先在本地把“问题分类 + 文档检索 + 查单接口”跑通
- 想验证官方 PageIndex 是否适合自己的电商售后场景

## 当前能力

- 售后问题一级分类：文档问题 / 订单查询 / 其他
- 文档问题二级分类：退换货 / 物流签收 / 质保售后 / 安装使用 / 其他
- 文档查询走官方 PageIndex 思路
- 查单走本地 mock API
- 模型使用 DeepSeek

## 快速说明

1. 启动本地 Dify。
2. 应用 `patches/dify-docker-compose.patch`。
3. 拉取并补丁官方 `VectifyAI/PageIndex` 仓库，应用 `patches/pageindex-utils.patch`。
4. 启动 `pageindex_official` 和 `jianing_mock`。
5. 导入 `dify_customer_service/workflow_pageindex_customer_service.yml`。

更细的使用说明可以看：

- [dify_customer_service/README.md](/Users/gallifreycar/Documents/Playground/jianing-dify-pageindex-demo/dify_customer_service/README.md)

如果你想了解这套方案今天是怎么一步步做出来的、踩了哪些坑、最后怎么解决的，可以看：

- [实施记录.md](/Users/gallifreycar/Documents/Playground/jianing-dify-pageindex-demo/实施记录.md)

## 说明

- 本仓库不包含任何真实私钥。
- 订单接口目前是 mock，用来体验流程。
- 文档检索已经切到官方 PageIndex 路线，不依赖旧向量库。
