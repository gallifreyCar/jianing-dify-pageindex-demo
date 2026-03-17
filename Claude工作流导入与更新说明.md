# Claude 工作流导入与更新说明

这份文档是写给后续继续维护这套 Dify 工作流的人看的，尤其适合给 Claude Code 或其他 coding agent 当操作说明。

目标不是解释 Dify 原理，而是说明:

- 为什么前端导入 DSL 容易失败
- 我这次是怎么把新工作流导入 Dify 的
- 后来又是怎么稳定更新在线工作流的
- Claude 如果继续接手，最推荐用哪些能力和 skill

## 1. 先说结论

这次之所以能比较快把工作流导入并反复更新，不是因为单纯“页面点得更准”，而是因为最后用了两层方案:

1. 正常走 Dify 的导入链路
2. 当前端导入或页面渲染不稳定时，直接更新 Dify 数据库里的 workflow 数据

也就是说，真正稳定的方法不是只依赖 UI，而是:

- UI 导入
- API 导入
- 数据库直写

三种方式配合。

## 2. 为什么只靠前端导入很容易失败

Dify 的 DSL 导入经常会遇到下面几类问题:

- `DSL 已经导入成功，但页面渲染报错`
- `应用已经创建了，但 workflow graph 某些字段不兼容`
- `节点类型兼容，但节点字段结构不兼容`
- `浏览器自动化权限不足，看不到真实报错`
- `分享页和控制台用的是不同会话，误以为导入没生效`

这次实际碰到过的情况包括:

- Safari 对 Apple Events JavaScript 支持不稳定
- Chrome 没开允许 Apple Events 时，自动化读不到报错
- 某些旧版 DSL 字段导入后，应用已经被创建，但 workflow 页面白屏或报错
- 某些节点在当前 Dify 版本里字段格式不完全兼容

所以如果 Claude 一直停留在“重新导一次 DSL 看看”，会很容易卡住。

## 3. 这次实际采用的工作流导入方式

### 3.1 第一阶段: 先走正常导入

优先做的是:

1. 在浏览器里完成 Dify 登录
2. 用现有会话导入 DSL
3. 检查应用是否真的被创建

关键判断标准不是“页面有没有报错”，而是:

- 应用记录是否创建出来
- workflow 页面能不能打开
- 后端数据库里是否已经有对应的 workflow 数据

这一步的经验是:

- 如果导入时报错，不要立刻认为“完全失败”
- 很多时候是“应用已创建，但 graph 不兼容”

### 3.2 第二阶段: 直接看数据库

当前端表现不稳定时，我直接去看 Dify 的 Postgres。

重点表是:

- `apps`
- `workflows`

重点看:

- 应用是否存在
- workflow 对应的 `graph`
- `features`
- `environment_variables`
- `conversation_variables`

一旦确认应用已经存在，就不再反复赌前端导入器，而是开始对齐数据库里的真实结构。

## 4. 真正稳定的更新方式: 直写 workflows 表

后面绝大多数“更新在线工作流”的动作，都是直接更新 `workflows` 表完成的。

核心字段是:

- `graph`
- `features`
- `environment_variables`
- `conversation_variables`

### 4.1 数据来源

工作流 DSL 文件主要在这里:

- [/Users/gallifreycar/Documents/Playground/dify_customer_service/workflow_pageindex_customer_service.yml](/Users/gallifreycar/Documents/Playground/dify_customer_service/workflow_pageindex_customer_service.yml)

如果要同步到仓库版本，还会复制到:

- [/Users/gallifreycar/Documents/Playground/jianing-dify-pageindex-demo/dify_customer_service/workflow_pageindex_customer_service.yml](/Users/gallifreycar/Documents/Playground/jianing-dify-pageindex-demo/dify_customer_service/workflow_pageindex_customer_service.yml)

### 4.2 更新思路

流程是:

1. 读取 YAML
2. 取出 `workflow.graph`
3. 取出 `workflow.features`
4. 整理 `workflow.environment_variables`
5. 整理 `workflow.conversation_variables`
6. 转成 JSON
7. 再 base64 编码
8. 通过 `docker compose exec db_postgres psql` 更新 `workflows` 表

### 4.3 为什么要 base64

因为 `graph` 是大 JSON，里面有很多引号、换行和代码字符串，直接拼 SQL 很容易炸。

base64 的好处是:

- 不容易被引号打断
- 不容易因为换行或反斜杠出问题
- 便于 shell 和 SQL 间传递

### 4.4 一个关键细节

这两个字段非常容易写错:

- `environment_variables`
- `conversation_variables`

实际经验:

- `environment_variables` 最稳的是写成 `{}` 这种对象，不要写成空数组 `[]`
- `conversation_variables` 不能只保留 YAML 里的数组形式，最终要整理成“按变量名索引的 JSON 对象”

如果这两个字段结构不对，前端和运行时都可能出奇怪问题。

## 5. 我这次是怎么修改 YAML 的

不是每次都用手改长字符串。

因为 Dify 的 code 节点在 YAML 里经常被序列化成大段嵌入式字符串，直接 patch 有时很痛苦。

所以我这次混合使用了:

- `apply_patch`
- Ruby 脚本读写 YAML

典型做法是:

1. 用 Ruby `YAML.load_file`
2. 找到目标节点，比如:
   - `route_l1_code`
   - `parse_order_api`
3. 更新对应节点的 `data.code`
4. 再写回 YAML
5. 用 Ruby 再做一次 YAML 解析校验

这样改复杂 code 节点，通常比直接 patch 一长坨字符串稳。

## 6. 为什么后来更新比导入快很多

因为后期已经形成了固定套路:

1. 本地改 YAML
2. 校验 YAML 可解析
3. 同步仓库副本
4. 转 JSON + base64
5. 更新 `workflows` 表
6. 刷新 Dify 页面验证

一旦绕开“前端导入器兼容性”这个不稳定点，后面更新 workflow 会快很多。

## 7. 如果 Claude 继续接手，推荐的操作顺序

建议 Claude 不要一上来就反复点 Dify 页面，而是按这个顺序:

1. 先确认目标应用和 workflow ID
2. 看本地 YAML 是否是最新
3. 看数据库里的 live workflow 是否已经被更新
4. 只有在需要新建应用时，才优先尝试 UI / API 导入
5. 一旦已有应用，优先用数据库直写更新

判断是否“该放弃前端改走数据库”的标准:

- 应用已创建，但页面打不开
- DSL 看起来语法没错，但导入后就是渲染异常
- 多次导入只是在猜字段兼容性
- 浏览器报错读不全

出现这些情况时，直接下数据库通常更高效。

## 8. 推荐 Claude 使用的 skill

下面这些 skill 对这类任务最有帮助。

### 8.1 `$playwright`

文件:

- [$playwright](/Users/gallifreycar/.codex/skills/playwright/SKILL.md)

适合做:

- 登录后读 Dify 页面内容
- 看导入后的真实页面报错
- 验证聊天页是否正常响应
- 在一个真实聊天窗口里跑回归测试

这次非常有用的一点是:

- 工作流修完以后，可以直接在分享页里连续提问，验证“查单、文档、兜底”是否回归

### 8.2 `$doc`

文件:

- [$doc](/Users/gallifreycar/.codex/skills/doc/SKILL.md)

虽然这次主要不是 `.docx`，但它对“生成规范文档、整理交付说明、给别人看的操作手册”还是有帮助。

适合:

- 写交付文档
- 写实施记录
- 整理操作手册

### 8.3 不算 skill，但强烈建议优先用的能力

这类任务里，最重要的不是更多 skill，而是下面这些操作习惯:

- `rg` 搜索项目和配置
- 用脚本修改 YAML/JSON，而不是只靠手改长字符串
- 直接看数据库真实数据
- 用 `curl` 验证 HTTP 节点目标服务
- 用真实聊天页做最终回归

## 9. 给 Claude 的建议

如果 Claude 再遇到“导入失败”，最不该做的是一直重复:

- 重新导一次
- 再猜一个 DSL 版本
- 再换一个浏览器

更好的做法是:

1. 先判断应用是否已创建
2. 再判断问题是在“导入失败”还是“渲染失败”
3. 如果是渲染失败，直接查数据库结构
4. 把工作流更新流程切换成“YAML -> JSON -> DB”

一句话总结:

前端导入适合“新建”，数据库直写适合“稳定迭代”。

## 10. 当前这套项目里，最值得保留的经验

- 不要只相信前端导入结果，要看数据库里的真实 workflow
- 分享页和控制台都要测
- 节点路由改动后，要用同一个聊天窗口做多轮验证
- 迁移容器环境后，要先验证 HTTP 服务，再验证聊天链路
- 文档检索链路问题，要区分:
  - 服务没启动
  - 服务启动了但模型不通
  - 模型通了但代码抛异常

## 11. 一句话版给 Claude

如果你接手这个项目:

- 新建 workflow 可以先用 UI / API 导入
- 一旦应用已经存在，优先改 YAML 并直写 `workflows` 表
- 最后一定用真实聊天页回归，不要只看导入成功提示
