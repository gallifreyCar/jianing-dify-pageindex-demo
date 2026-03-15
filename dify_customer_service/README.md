# Dify 智能客服（PageIndex + 订单接口）本地试跑

这个目录给你一个可直接改造的起步包：
- `workflow_pageindex_customer_service.yml`：Dify 工作流 DSL 草图（建议导入后按你当前 Dify 版本微调）
- `workflow_pageindex_customer_service.mmd`：流程图

## 1) 本地启动 Dify

要求：本机已安装 Docker / Docker Compose。

```bash
cd /Users/gallifreycar/Documents/Playground
git clone --depth=1 https://github.com/langgenius/dify.git dify-local
cd dify-local/docker
cp .env.example .env
docker compose up -d
```

初始化：
- 打开 `http://localhost/install` 创建管理员
- 然后登录 `http://localhost`

## 2) 导入 DSL（草图版）

在 Dify 控制台：
1. 新建 `Chatflow` 应用
2. 右上角导入 DSL
3. 选择 `workflow_pageindex_customer_service.yml`
4. 如果导入报字段错误，按报错位置做字段名微调（我可以继续帮你改到可导入）

## 3) 你需要改的配置（必改）

1. LLM 模型改成你后续接入的 DeepSeek（在各个 `llm` 节点里改）。
2. `http-request` 节点：
- `https://pageindex.local/search` 改成你的 PageIndex 服务地址
- `https://api.yourshop.com/orders/query` 改成你的订单接口
3. 文档检索路径当前走 PageIndex，不依赖旧向量库；如果你想一部分文档继续走 Dify Knowledge，也可以在分支上补 `knowledge-retrieval` 节点。

## 4) 推荐路由策略（售后客服）

- 先做一级分类：`文档问题` / `订单查询` / `其他`
- 文档问题再做二级分类：`退换货` / `物流签收` / `质保售后` / `安装使用` / `其他`
- `订单查询` 走 API
- `文档问题` 走 PageIndex，并按二级场景构造不同检索 query
- 低置信度时走兜底：引导补充信息或转人工
