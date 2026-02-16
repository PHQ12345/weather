weather_forward — 高德天气转发服务
=================================

简介
----
一个极简的高德天气转发服务，单文件实现，基于 Flask 与 requests。主要用于根据行政区编码（adcode）转发并缓存高德实时天气数据。

主要文件
----
- [weather_forward.py](weather_forward.py): 服务入口，包含所有路由、缓存与对高德 API 的调用逻辑。

依赖
----
- Python 3.7+
- Flask
- requests

安装依赖
----
```bash
pip install Flask requests
```

运行
----
在 Windows CMD:
```bat
set PORT=8000
set DEBUG=True
python weather_forward.py
```
PowerShell:
```powershell
$env:PORT=8000; $env:DEBUG='True'; python weather_forward.py
```

环境与配置
----
- `AMAP_API_KEY`：高德 API Key 常量定义在 `weather_forward.py`，可直接在文件中替换或修改为读取环境变量。
- `CACHE_TIMEOUT`：模块内缓存超时时长（秒），用于缓存天气响应以减少外部请求。

常用接口
----
- GET `/api/weather/current/<adcode>`：获取实时天气（`adcode` 为 6 位行政编码）。
- DELETE `/api/weather/cache/<adcode>`：清除指定地区缓存。
- GET `/health`：健康检查。

约定与注意事项
----
- 参数校验：`adcode` 必须为 6 位数字，错误返回 400。
- 对外调用超时与异常映射到相应 HTTP 错误码（见 `weather_forward.py` 中实现）。
- 当前仓库没有列出依赖在 `requirements.txt`，建议在需要时补充。

联系人
----
请在仓库中查看 `weather_forward.py` 以获得更多实现细节或告知我是否需要：
- 将 `AMAP_API_KEY` 移入环境变量
- 补充 `requirements.txt`
