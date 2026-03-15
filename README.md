# 嘉宁测试电商 Dify + PageIndex Demo

这个仓库整理了一个本地可跑的售后客服 demo，核心能力包括：

- Dify Chatflow 工作流 DSL
- 官方 `VectifyAI/PageIndex` 接入封装服务
- 本地 mock 售后文档与订单接口
- DeepSeek 作为推理模型
- 对上游 `dify` 和 `PageIndex` 的最小补丁

## 目录

- `dify_customer_service/`
  - 工作流 DSL
  - PageIndex 本地服务
  - mock 文档
  - mock 订单/文档接口
- `patches/dify-docker-compose.patch`
  - 给 Dify 本地 `docker-compose.yaml` 增加本地 mock 服务和 `pageindex_official` 服务
- `patches/pageindex-utils.patch`
  - 给官方 PageIndex 增加 OpenAI-compatible `base_url` 支持，兼容 DeepSeek

## 本地运行思路

1. 按官方方式启动 Dify。
2. 应用 `patches/dify-docker-compose.patch` 到 Dify 仓库。
3. 应用 `patches/pageindex-utils.patch` 到官方 PageIndex 仓库。
4. 将 `dify_customer_service/pageindex_service.py` 和 `dify_customer_service/mock_docs/` 挂到 Dify compose 里的 `pageindex_official` 服务。
5. 在 Dify 中导入 `dify_customer_service/workflow_pageindex_customer_service.yml`。

## 说明

- 本仓库不包含你的私有 API Key。
- 订单接口仍是本地 mock，便于体验流程。
- 文档检索已切到官方 PageIndex 思路，不再依赖旧向量库。
