# Dify 售后客服 Demo 使用说明

这份文档面向“想在本地把整套客服流程跑起来”的使用者，介绍当前目录中的文件用途、运行方式、测试方法，以及后续如何替换成真实业务接口。

## 目录说明

- `workflow_pageindex_customer_service.yml`
  - Dify 工作流 DSL
  - 这是当前最核心的导入文件
- `workflow_pageindex_customer_service.mmd`
  - 工作流结构示意图
- `pageindex_service.py`
  - 基于官方 `VectifyAI/PageIndex` 封装的本地 HTTP 服务
  - Dify 的文档检索分支实际调用的是它
- `mock_backend.py`
  - 本地 mock 服务
  - 提供测试订单接口和文档文件访问接口
- `mock_docs/`
  - 嘉宁测试电商的测试文档
  - 按售后场景拆分为退换货、物流、质保、安装使用、客服模版
- `basic_chatflow_import.yml`
  - 简化版导入测试文件
- `minimal_ascii_chatflow.yml`
  - 更小的 ASCII 兼容导入测试文件

## 当前流程能力

这套客服流程目前包含这些能力：

- 一级分类
  - 文档问题
  - 订单查询
  - 其他
- 二级分类
  - 退换货
  - 物流签收
  - 质保售后
  - 安装使用
  - 其他
- 文档问题
  - 进入 `pageindex_service.py`
  - 调用官方 PageIndex 路线做树结构检索
- 订单查询
  - 调用 `mock_backend.py` 里的 `/orders/query`
- 模型
  - 当前默认按 DeepSeek 兼容 OpenAI API 的方式工作

## 运行关系

这套 demo 实际是三个部分一起协作：

1. Dify
   - 提供工作流编排和对话界面
2. `pageindex_official`
   - 对外提供 `/search`
   - 负责文档检索和回答生成
3. `jianing_mock`
   - 对外提供 `/orders/query`
   - 负责查单 mock 和测试文档访问

## 本地启动建议

当前推荐的本地运行方式不是只看这个目录，而是配合仓库根目录里的 patch 一起使用。

建议顺序：

1. 启动本地 Dify
2. 应用 Dify compose 补丁
3. 应用官方 PageIndex 补丁
4. 启动 `pageindex_official` 和 `jianing_mock`
5. 导入本目录中的工作流 DSL

总入口请先看：

- [README.md](/Users/gallifreycar/Documents/Playground/jianing-dify-pageindex-demo/README.md)

## Dify 中要导入的文件

优先导入：

- `workflow_pageindex_customer_service.yml`

如果你只是想验证导入能力或做最小调试，也可以试：

- `basic_chatflow_import.yml`
- `minimal_ascii_chatflow.yml`

## 测试文档说明

`mock_docs/` 当前包含 5 类测试资料：

- `01_退货与退款政策.md`
- `02_物流与签收处理.md`
- `03_质保与换新规则.md`
- `04_安装使用与故障排查.md`
- `05_客服回复模版.md`

这些文档不是随便拼的，它们是按售后客服常见问题场景拆出来的，方便工作流先做分类，再让 PageIndex 在更小的范围里检索。

## 建议测试问题

你可以直接在 Dify 里测试这些问题：

文档类：

- `退款规则是什么？`
- `我签收后还能退货吗？`
- `物流签收破损怎么处理？`
- `这个商品质保多久？`
- `我不会安装，给我使用说明`

订单类：

- `帮我查一下订单 JN202603150001`
- `订单 JN202603150002 的退款进度是什么？`
- `订单 JN202603150003 今天能送到吗？`

可用测试订单号：

- `JN202603150001`
- `JN202603150002`
- `JN202603150003`

## 当前接口说明

### 文档检索接口

由 `pageindex_service.py` 提供：

- `GET /health`
- `POST /search`

请求体示例：

```json
{
  "q": "退款规则是什么？",
  "scene": "refund"
}
```

### 订单查询接口

由 `mock_backend.py` 提供：

- `GET /health`
- `GET /docs`
- `GET /docs/<filename>`
- `POST /orders/query`

请求体示例：

```json
{
  "order_no": "JN202603150001",
  "phone_tail": "6688"
}
```

## 如果你要替换成真实业务

后续接入真实系统时，优先改这几块：

1. 替换订单接口
   - 把 Dify 工作流里的 `/orders/query` 改成真实订单服务
   - 同步调整鉴权、字段名和返回格式
2. 替换测试文档
   - 用真实售后文档替换 `mock_docs/`
   - 尽量按场景拆分文档，减少检索范围
3. 调整 `SCENE_TO_FILE`
   - 在 `pageindex_service.py` 里维护场景与文档的映射
4. 优化客服回复
   - 当前已经是客服口吻，但仍然是 demo 级别
   - 后续可以根据品牌语气再调 prompt
5. 增加缓存和预热
   - 当前 PageIndex 采用按场景懒加载
   - 首次命中某个场景时会稍慢

## 这份目录适合继续扩展什么

如果你打算把它继续做成真实项目，建议后续在这里继续增加：

- 真实 API 适配层
- 订单状态解释模版
- 工单创建接口
- 转人工节点
- 多轮补充信息收集逻辑
- 更多按类目拆分的售后文档

## 相关文档

- 返回仓库总览：[README.md](/Users/gallifreycar/Documents/Playground/jianing-dify-pageindex-demo/README.md)
- 查看今天的完整思路和踩坑记录：[实施记录.md](/Users/gallifreycar/Documents/Playground/jianing-dify-pageindex-demo/实施记录.md)
