# Copilot 指南 — weather_forward

此仓库是一个极简的高德天气转发服务（单文件 Flask 应用）。本文件为 AI 编码代理提供可立即上手的项目要点、运行/调试命令、约定和示例。

主要结构
- 单个主要实现文件：`weather_forward.py` — 启动 Flask 服务并实现所有 HTTP 接口与缓存逻辑。
- 依赖：直接在代码中使用 `flask` 与 `requests`。

关键端点（来自 `weather_forward.py`）
- `/` ：服务信息与示例
- `/health` ：健康检查
- `/api/weather/current/<adcode>` ：获取实时天气（`adcode` 为 6 位行政编码）
- `/api/weather/cache/<adcode>` （DELETE）：清除指定地区缓存

重要实现细节（可直接引用代码片段）
- API Key 在文件中以常量 `AMAP_API_KEY` 定义（硬编码）。搜索 `AMAP_API_KEY` 即可定位。代理如需替换 Key，可直接在 `weather_forward.py` 修改或在运行前注入环境变量并修改文件以读取环境变量。
- 缓存实现：模块级 `weather_cache` 字典 + `CACHE_TIMEOUT`（秒）。代理在处理请求时会先查缓存再调用高德 API。
- 对外调用：使用 `requests.get` 请求 `AMAP_WEATHER_URL`，超时与异常通过 `requests.exceptions` 捕获并映射到 HTTP 错误码（502/504/500）。
- 返回格式：统一使用 JSON，携带 `success`, `code`, `data`（当 success 为 True 时）和 `timestamp` 字段。参见 `/api/weather/current/<adcode>` 的返回构造。

开发 / 运行
- 安装依赖（仓库的 `requirements.txt` 目前为空；代码需要 `Flask` 和 `requests`）：

  ```bash
  pip install Flask requests
  # 或者补充 requirements.txt: Flask\nrequests
  ```

- 运行（默认端口 8000，可通过环境变量覆盖）：

  Windows CMD:
  ```bat
  set PORT=8000
  set DEBUG=True
  python weather_forward.py
  ```

  PowerShell:
  ```powershell
  $env:PORT=8000; $env:DEBUG='True'; python weather_forward.py
  ```

- 测试接口示例：

  ```bash
  curl http://localhost:8000/api/weather/current/110000
  curl -X DELETE http://localhost:8000/api/weather/cache/110000
  ```

项目约定与可预期行为
- 参数校验：`adcode` 必须为 6 位数字，校验逻辑在 `get_current_weather` 中实现；无效参数返回 400。
- 日志：使用标准 `logging`，记录缓存命中、外部 API 调用与错误信息；代理可通过日志追踪调用链。
- 错误映射：高德 API 状态不为 `1` 将返回 500，并将 `info` 文本暴露在响应 `message` 中。

集成点与外部依赖
- 外部服务：高德天气 API（`AMAP_WEATHER_URL`），请求参数包括 `key`, `city(adcode)`, `extensions`, `output`。
- 运行环境：任何支持 Python 与 Flask 的环境。注意网络请求到高德 API 需要联网与有效 API Key。

维护/改动提示（仅可观察到的事实）
- 目前没有单元测试目录或 CI 配置；所有逻辑在 `weather_forward.py` 单文件实现。
- `requirements.txt` 为空，CI/构建步骤在仓库内未发现，应在需要时补充依赖清单。

要点总结（代理速查）
- 入口文件：`weather_forward.py`（查看路由、`AMAP_API_KEY`、`CACHE_TIMEOUT`）
- 运行：`python weather_forward.py`（使用 `PORT` / `DEBUG` 环境变量）
- 依赖：`Flask`, `requests`（请补充 `requirements.txt`）
- 调试提示：查看控制台日志（`logging`）以确认缓存与外部 API 调用。

如果上述信息不完整或你想让我把 `AMAP_API_KEY` 移入环境变量/补充 `requirements.txt`，请确认我可以修改这些文件。期待你的反馈以便迭代此指南。
