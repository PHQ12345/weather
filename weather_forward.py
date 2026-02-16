# weather_forward.py
"""
高德天气转发服务
支持实时天气查询和天气预测功能
"""
from flask import Flask, jsonify, request as flask_request
import requests
from datetime import datetime
import os
import logging
from functools import wraps

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)

# 高德API配置（从环境变量读取，支持硬编码降级）
AMAP_API_KEY = os.environ.get('AMAP_API_KEY', 'a51c1bf712e1cddf19cc4afdca57fc03')
AMAP_WEATHER_URL = "https://restapi.amap.com/v3/weather/weatherInfo"

# 缓存配置
weather_cache = {}
forecast_cache = {}
CACHE_TIMEOUT = int(os.environ.get('CACHE_TIMEOUT', '1800'))  # 30分钟
API_TIMEOUT = 5  # 接口超时时间（秒）


@app.route('/')
def index():
    """服务首页"""
    return jsonify({
        'service': '高德天气转发服务',
        'version': '2.0.0',
        'description': '支持实时天气查询和1天预测',
        'endpoints': {
            '首页': '/',
            '健康检查': '/health',
            '实时天气': '/api/weather/current/<adcode>',
            '天气预测': '/api/weather/forecast/<adcode>',
            '清除缓存': 'DELETE /api/weather/cache/<adcode>'
        },
        'examples': {
            '实时天气': '/api/weather/current/110000',
            '天气预测': '/api/weather/forecast/110000'
        },
        'documentation': {
            'adcode': '6位行政编码，如110000(北京)、310000(上海)等'
        },
        'timestamp': datetime.now().isoformat()
    })


@app.route('/health')
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'weather-forward',
        'uptime': 'running',
        'cache_items': len(weather_cache) + len(forecast_cache),
        'timestamp': datetime.now().isoformat()
    })


def validate_adcode(adcode):
    """
    验证行政编码格式
    返回 (is_valid, error_message)
    """
    if not adcode or not isinstance(adcode, str):
        return False, 'adcode参数缺失'
    if not adcode.isdigit():
        return False, 'adcode必须是纯数字'
    if len(adcode) != 6:
        return False, 'adcode必须是6位数字'
    return True, None


def create_error_response(code, message):
    """
    创建统一的错误响应
    """
    return {
        'success': False,
        'code': code,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }


def create_success_response(data):
    """
    创建统一的成功响应
    """
    return {
        'success': True,
        'code': 200,
        'data': data,
        'timestamp': datetime.now().isoformat()
    }


@app.route('/api/weather/current/<adcode>')
def get_current_weather(adcode):
    """
    获取实时天气
    参数: adcode - 地区行政编码，6位数字，如110000(北京)
    返回: JSON格式的天气信息
    """
    # 1. 验证参数
    is_valid, error_msg = validate_adcode(adcode)
    if not is_valid:
        return jsonify(create_error_response(400, error_msg)), 400
    
    # 2. 检查缓存
    cache_key = f"current_{adcode}"
    if cache_key in weather_cache:
        cache_time, cache_data = weather_cache[cache_key]
        if datetime.now().timestamp() - cache_time < CACHE_TIMEOUT:
            logger.info(f"缓存命中 - 实时天气: {adcode}")
            return jsonify(cache_data)
    
    # 3. 调用高德API获取实时天气
    try:
        logger.info(f"调用高德API - 获取实时天气: {adcode}")
        params = {
            'key': AMAP_API_KEY,
            'city': adcode,
            'extensions': 'base',
            'output': 'JSON'
        }
        
        response = requests.get(AMAP_WEATHER_URL, params=params, timeout=API_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        # 检查API返回状态
        if data.get('status') != '1':
            error_info = data.get('info', '未知错误')
            logger.error(f"高德API错误 - {error_info}")
            return jsonify(create_error_response(500, f'高德API错误: {error_info}')), 500
        
        # 检查是否有数据
        if 'lives' not in data or not data['lives']:
            logger.warning(f"未获取到天气数据: {adcode}")
            return jsonify(create_error_response(500, '未获取到天气数据')), 500
        
        live = data['lives'][0]
        
        # 格式化返回数据
        weather_data = {
            'location': {
                'adcode': live.get('adcode', adcode),
                'province': live.get('province', ''),
                'city': live.get('city', ''),
                'district': live.get('district', '')
            },
            'weather': {
                'description': live.get('weather', ''),
                'temperature': int(live.get('temperature', 0)),
                'humidity': int(live.get('humidity', 0)),
                'wind_direction': live.get('winddirection', ''),
                'wind_direction_code': live.get('windcode', ''),
                'wind_power': live.get('windpower', ''),
                'wind_speed': live.get('windspeed', '0')
            },
            'report_time': live.get('reporttime', ''),
            'live_index': live.get('live_index', [])
        }
        
        result = create_success_response(weather_data)
        
        # 存入缓存
        weather_cache[cache_key] = (datetime.now().timestamp(), result)
        
        logger.info(f"实时天气查询成功: {live.get('city', adcode)} - {live.get('weather', '')}")
        return jsonify(result)
        
    except requests.exceptions.Timeout:
        logger.error("高德API请求超时（实时天气）")
        return jsonify(create_error_response(504, '请求高德API超时')), 504
        
    except requests.exceptions.ConnectionError:
        logger.error("高德API连接失败（实时天气）")
        return jsonify(create_error_response(502, '无法连接高德API')), 502
        
    except requests.exceptions.RequestException as e:
        logger.error(f"高德API请求失败（实时天气）: {str(e)}")
        return jsonify(create_error_response(502, f'请求高德API失败: {str(e)}')), 502
        
    except ValueError:
        logger.error("高德API返回数据无效（实时天气）")
        return jsonify(create_error_response(500, '高德API返回数据无效')), 500
        
    except Exception as e:
        logger.error(f"服务器错误（实时天气）: {str(e)}")
        return jsonify(create_error_response(500, f'服务器错误: {str(e)}')), 500


@app.route('/api/weather/forecast/<adcode>')
def get_forecast_weather(adcode):
    """
    获取天气预测（预报）
    参数: adcode - 地区行政编码，6位数字，如110000(北京)
    返回: JSON格式的1天预测信息
    """
    # 1. 验证参数
    is_valid, error_msg = validate_adcode(adcode)
    if not is_valid:
        return jsonify(create_error_response(400, error_msg)), 400
    
    # 2. 检查缓存
    cache_key = f"forecast_{adcode}"
    if cache_key in forecast_cache:
        cache_time, cache_data = forecast_cache[cache_key]
        if datetime.now().timestamp() - cache_time < CACHE_TIMEOUT:
            logger.info(f"缓存命中 - 天气预测: {adcode}")
            return jsonify(cache_data)
    
    # 3. 调用高德API获取预测数据
    try:
        logger.info(f"调用高德API - 获取天气预测: {adcode}")
        params = {
            'key': AMAP_API_KEY,
            'city': adcode,
            'extensions': 'all',  # 使用all参数获取预测数据
            'output': 'JSON'
        }
        
        response = requests.get(AMAP_WEATHER_URL, params=params, timeout=API_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        # 检查API返回状态
        if data.get('status') != '1':
            error_info = data.get('info', '未知错误')
            logger.error(f"高德API错误 - {error_info}")
            return jsonify(create_error_response(500, f'高德API错误: {error_info}')), 500
        
        # 检查是否有数据
        if 'forecasts' not in data or not data['forecasts']:
            logger.warning(f"未获取到预测数据: {adcode}")
            return jsonify(create_error_response(500, '未获取到预测数据')), 500
        
        forecast = data['forecasts'][0]
        
        # 提取当前日期的预测（通常第一条）
        casts = forecast.get('casts', [])
        if not casts:
            return jsonify(create_error_response(500, '无预测数据')), 500
        
        # 解析最多3条预测数据
        forecast_data = {
            'location': {
                'adcode': forecast.get('adcode', adcode),
                'province': forecast.get('province', ''),
                'city': forecast.get('city', ''),
                'district': forecast.get('district', '')
            },
            'publish_time': forecast.get('reporttime', ''),
            'forecasts': []
        }
        
        for i, cast in enumerate(casts[:3]):  # 限制为3天预测
            forecast_item = {
                'day': i + 1,
                'date': cast.get('date', ''),
                'weather_day': cast.get('dayweather', ''),
                'weather_night': cast.get('nightweather', ''),
                'temperature_high': int(cast.get('daytemp', 0)),
                'temperature_low': int(cast.get('nighttemp', 0)),
                'wind_direction_day': cast.get('daywind', ''),
                'wind_direction_night': cast.get('nightwind', ''),
                'wind_power_day': cast.get('daypower', ''),
                'wind_power_night': cast.get('nightpower', '')
            }
            forecast_data['forecasts'].append(forecast_item)
        
        result = create_success_response(forecast_data)
        
        # 存入缓存
        forecast_cache[cache_key] = (datetime.now().timestamp(), result)
        
        logger.info(f"天气预测查询成功: {forecast.get('city', adcode)} - {len(casts)}天预报")
        return jsonify(result)
        
    except requests.exceptions.Timeout:
        logger.error("高德API请求超时（天气预测）")
        return jsonify(create_error_response(504, '请求高德API超时')), 504
        
    except requests.exceptions.ConnectionError:
        logger.error("高德API连接失败（天气预测）")
        return jsonify(create_error_response(502, '无法连接高德API')), 502
        
    except requests.exceptions.RequestException as e:
        logger.error(f"高德API请求失败（天气预测）: {str(e)}")
        return jsonify(create_error_response(502, f'请求高德API失败: {str(e)}')), 502
        
    except ValueError:
        logger.error("高德API返回数据无效（天气预测）")
        return jsonify(create_error_response(500, '高德API返回数据无效')), 500
        
    except Exception as e:
        logger.error(f"服务器错误（天气预测）: {str(e)}")
        return jsonify(create_error_response(500, f'服务器错误: {str(e)}')), 500


@app.route('/api/weather/cache/<adcode>', methods=['DELETE', 'GET'])
def manage_cache(adcode):
    """
    管理缓存
    DELETE: 清除指定地区的所有缓存
    GET: 获取缓存状态
    """
    # 验证参数
    is_valid, error_msg = validate_adcode(adcode)
    if not is_valid:
        return jsonify(create_error_response(400, error_msg)), 400
    
    if flask_request.method == 'DELETE':
        count = 0
        cache_keys_to_delete = [
            f"current_{adcode}",
            f"forecast_{adcode}"
        ]
        
        for cache_key in cache_keys_to_delete:
            if cache_key in weather_cache:
                del weather_cache[cache_key]
                count += 1
            if cache_key in forecast_cache:
                del forecast_cache[cache_key]
                count += 1
        
        return jsonify({
            'success': True,
            'code': 200,
            'message': f'已清除 {adcode} 的缓存（{count}项）',
            'timestamp': datetime.now().isoformat()
        })
    
    else:  # GET method
        current_cached = f"current_{adcode}" in weather_cache
        forecast_cached = f"forecast_{adcode}" in forecast_cache
        
        cache_info = {
            'adcode': adcode,
            'current_weather_cached': current_cached,
            'forecast_cached': forecast_cached,
            'total_cache_items': len(weather_cache) + len(forecast_cache)
        }
        
        if current_cached:
            cache_time, _ = weather_cache[f"current_{adcode}"]
            cache_age = datetime.now().timestamp() - cache_time
            cache_info['current_cache_age_seconds'] = int(cache_age)
            cache_info['current_cache_expires_in'] = int(CACHE_TIMEOUT - cache_age)
        
        if forecast_cached:
            cache_time, _ = forecast_cache[f"forecast_{adcode}"]
            cache_age = datetime.now().timestamp() - cache_time
            cache_info['forecast_cache_age_seconds'] = int(cache_age)
            cache_info['forecast_cache_expires_in'] = int(CACHE_TIMEOUT - cache_age)
        
        return jsonify(create_success_response(cache_info))


@app.errorhandler(404)
def not_found(error):
    """404处理"""
    return jsonify(create_error_response(404, '接口不存在，请检查URL')), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """405处理"""
    return jsonify(create_error_response(405, '请求方法不允许')), 405


@app.errorhandler(500)
def server_error(error):
    """500处理"""
    logger.error(f"服务器内部错误: {str(error)}")
    return jsonify(create_error_response(500, '服务器内部错误')), 500


@app.before_request
def log_request():
    """记录请求日志"""
    logger.info(f"[{flask_request.method}] {flask_request.path} - IP: {flask_request.remote_addr}")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print("\n" + "="*60)
    print("高德天气转发服务 v2.0.0".center(60))
    print("="*60)
    print(f"服务状态:   启动中...")
    print(f"端口:       {port}")
    print(f"调试模式:   {debug}")
    print(f"API Key:    {AMAP_API_KEY[:5]}***{AMAP_API_KEY[-5:]}")
    print(f"缓存时间:   {CACHE_TIMEOUT}秒")
    print("\n快速测试:")
    print(f"  实时天气:  curl http://localhost:{port}/api/weather/current/110000")
    print(f"  天气预测:  curl http://localhost:{port}/api/weather/forecast/110000")
    print(f"  健康检查:  curl http://localhost:{port}/health")
    print(f"  清除缓存:  curl -X DELETE http://localhost:{port}/api/weather/cache/110000")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)