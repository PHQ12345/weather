weather_forward — 高德天气转发服务 v2.0
===

极简的Flask天气转发服务，支持实时天气查询和1天天气预测。

## 功能特性

✅ **实时天气** - 获取实时天气信息（温度、湿度、风力等）
✅ **天气预测** - 获取1-3天天气预测数据
✅ **内存缓存** - 自动缓存30分钟，减少API调用
✅ **完善错误处理** - 详细的错误信息和状态码
✅ **请求日志** - 记录所有API请求和缓存状态
✅ **环境变量 支持** - API Key、端口、缓存时间可配置

## 快速开始

### 1️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

### 2️⃣ 运行服务

#### Windows CMD
```batch
set PORT=8000
set DEBUG=True
python weather_forward.py
```

#### Windows PowerShell
```powershell
$env:PORT=8000; $env:DEBUG=$true; python weather_forward.py
```

#### Linux / macOS
```bash
export PORT=8000
export DEBUG=True
python weather_forward.py
```

完成后访问：`http://localhost:8000`

## API 接口

所有接口返回统一的JSON格式：

```json
{
  "success": true,
  "code": 200,
  "data": { ... },
  "timestamp": "2026-02-16T10:30:00.123456"
}
```

### 1. 首页

```
GET /
```

获取服务信息和API列表

**示例:**
```bash
curl http://localhost:8000/
```

### 2. 健康检查

```
GET /health
```

检查服务是否正常运行

**示例:**
```bash
curl http://localhost:8000/health
```

**响应:**
```json
{
  "status": "healthy",
  "service": "weather-forward",
  "cache_items": 5
}
```

### 3. 实时天气

```
GET /api/weather/current/<adcode>
```

获取指定地区的实时天气

| 参数 | 说明 | 示例 |
|------|------|------|
| `adcode` | 6位行政编码 | `110000`(北京)、`310000`(上海) |

**示例:**
```bash
curl http://localhost:8000/api/weather/current/110000
```

**响应:**
```json
{
  "success": true,
  "code": 200,
  "data": {
    "location": {
      "adcode": "110000",
      "province": "北京",
      "city": "北京",
      "district": "朝阳"
    },
    "weather": {
      "description": "晴",
      "temperature": 5,
      "humidity": 65,
      "wind_direction": "北",
      "wind_power": "3级",
      "wind_speed": "15"
    },
    "report_time": "2026-02-16T10:30:00Z"
  },
  "timestamp": "2026-02-16T10:30:00.123456"
}
```

### 4. 天气预测

```
GET /api/weather/forecast/<adcode>
```

获取指定地区的天气预测（最多3天）

| 参数 | 说明 | 示例 |
|------|------|------|
| `adcode` | 6位行政编码 | `110000`(北京) |

**示例:**
```bash
curl http://localhost:8000/api/weather/forecast/110000
```

**响应:**
```json
{
  "success": true,
  "code": 200,
  "data": {
    "location": {
      "adcode": "110000",
      "province": "北京",
      "city": "北京",
      "district": ""
    },
    "publish_time": "2026-02-16T10:30:00Z",
    "forecasts": [
      {
        "day": 1,
        "date": "2026-02-16",
        "weather_day": "多云",
        "weather_night": "晴",
        "temperature_high": 8,
        "temperature_low": -2,
        "wind_direction_day": "北",
        "wind_power_day": "3级",
        "wind_direction_night": "北",
        "wind_power_night": "3级"
      }
    ]
  },
  "timestamp": "2026-02-16T10:30:00.123456"
}
```

### 5. 管理缓存

#### 获取缓存状态
```
GET /api/weather/cache/<adcode>
```

**示例:**
```bash
curl http://localhost:8000/api/weather/cache/110000
```

#### 清除指定地区的缓存
```
DELETE /api/weather/cache/<adcode>
```

**示例:**
```bash
curl -X DELETE http://localhost:8000/api/weather/cache/110000
```

## 常见的行政编码

| 城市 | 编码 |
|------|------|
| 北京 | 110000 |
| 上海 | 310000 |
| 广州 | 440100 |
| 深圳 | 440300 |
| 杭州 | 330100 |
| 成都 | 510100 |
| 西安 | 610100 |
| 南京 | 320100 |

完整编码列表参考：[高德地区编码表](https://lbs.amap.com/api/webapi/guide/api/district)

## 环境变量配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `AMAP_API_KEY` | 高德API Key（必需） | `a51c1bf712e1cddf19cc4afdca57fc03` |
| `PORT` | 服务端口 | `8000` |
| `DEBUG` | 调试模式 | `False` |
| `CACHE_TIMEOUT` | 缓存超时时间（秒） | `1800` |

## 错误处理

所有错误都返回统一格式，包含错误码和错误信息：

```json
{
  "success": false,
  "code": 400,
  "message": "adcode参数缺失",
  "timestamp": "2026-02-16T10:30:00.123456"
}
```

常见错误码：

| 码 | 说明 |
|----|----|
| 400 | 请求参数错误 |
| 404 | 接口不存在 |
| 405 | 请求方法不允许 |
| 500 | 服务器错误或高德API错误 |
| 502 | 无法连接高德API |
| 504 | 高德API请求超时 |

## 工作原理

1. **请求到达** → 验证参数格式
2. **检查缓存** → 如果缓存有效直接返回
3. **调用高德API** → 获取最新数据
4. **解析数据** → 统一格式化
5. **存入缓存** → 避免频繁调用
6. **返回结果** → JSON格式

## 代码结构

```
weather_forward.py
├── 配置项              (API Key、缓存等)
├── 辅助函数
│   ├── validate_adcode()      # 验证行政编码
│   ├── create_error_response() # 创建错误响应
│   └── create_success_response() # 创建成功响应
├── 路由处理
│   ├── index()              # 首页
│   ├── health_check()       # 健康检查
│   ├── get_current_weather() # 实时天气
│   ├── get_forecast_weather() # 天气预测
│   └── manage_cache()       # 缓存管理
├── 错误处理
│   ├── not_found()          # 404处理
│   ├── method_not_allowed() # 405处理
│   └── server_error()       # 500处理
└── main               # 应用启动
```

## 完善的代码特性

✨ **缓存系统** - 分离实时和预测缓存，独立管理

✨ **错误处理** - 区分不同类型的错误（参数、网络、API）

✨ **日志记录** - 详细的日志便于调试和监控

✨ **环境配置** - 支持环境变量注入，易于容器化

✨ **统一响应格式** - 所有接口返回一致的JSON结构

✨ **请求验证** - 参数校验和异常捕获

## 开发建议

### 添加新接口

1. 创建新的辅助函数处理业务逻辑
2. 使用 `validate_adcode()` 验证参数
3. 使用 `create_error_response()` / `create_success_response()` 创建响应
4. 添加到对应的缓存系统

### 扩展缓存

可实现Redis缓存替代内存缓存：

```python
# 例：使用Redis
import redis
cache = redis.Redis(host='localhost', port=6379)
```

### 性能优化

- 增加缓存时间（`CACHE_TIMEOUT`）
- 使用Redis实现分布式缓存
- 添加请求限流（rate limiting）
- 异步调用高德API

## 许可证

MIT

## 贡献

欢迎提交Issue和Pull Request！
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
