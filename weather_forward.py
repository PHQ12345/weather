# weather_forward.py
"""
高德天气转发服务 - 极简版
单一文件，只实现实时天气查询功能
"""
from flask import Flask, jsonify
import requests
from datetime import datetime
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)

# 高德API配置（直接在这里配置）
AMAP_API_KEY = "a51c1bf712e1cddf19cc4afdca57fc03"  # 请替换为你的高德API Key
AMAP_WEATHER_URL = "https://restapi.amap.com/v3/weather/weatherInfo"

# 简单的内存缓存
weather_cache = {}
CACHE_TIMEOUT = 1800  # 30分钟


@app.route('/')
def index():
    """服务首页"""
    return jsonify({
        'service': '高德天气转发服务',
        'version': '1.0.0',
        'endpoints': {
            '实时天气': '/api/weather/current/<adcode>'
        },
        'example': '/api/weather/current/110000',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/health')
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'weather-forward',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/weather/current/<adcode>')
def get_current_weather(adcode):
    """
    获取实时天气
    参数 adcode: 地区行政编码，如 110000（北京）
    """
    # 1. 验证参数
    if not adcode or not adcode.isdigit() or len(adcode) != 6:
        return jsonify({
            'success': False,
            'code': 400,
            'message': 'adcode必须是6位数字',
            'timestamp': datetime.now().isoformat()
        }), 400
    
    # 2. 检查缓存
    cache_key = f"weather_{adcode}"
    if cache_key in weather_cache:
        cache_time, cache_data = weather_cache[cache_key]
        if datetime.now().timestamp() - cache_time < CACHE_TIMEOUT:
            logger.info(f"从缓存返回: {adcode}")
            return jsonify(cache_data)
    
    # 3. 调用高德API
    try:
        params = {
            'key': AMAP_API_KEY,
            'city': adcode,
            'extensions': 'base',
            'output': 'JSON'
        }
        
        logger.info(f"调用高德API: {adcode}")
        response = requests.get(AMAP_WEATHER_URL, params=params, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        
        # 检查API返回状态
        if data.get('status') != '1':
            error_msg = data.get('info', '未知错误')
            logger.error(f"高德API错误: {error_msg}")
            return jsonify({
                'success': False,
                'code': 500,
                'message': f'高德API错误: {error_msg}',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        # 解析天气数据
        if 'lives' not in data or not data['lives']:
            return jsonify({
                'success': False,
                'code': 500,
                'message': '未获取到天气数据',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        live = data['lives'][0]
        
        # 格式化返回数据
        result = {
            'success': True,
            'code': 200,
            'data': {
                'adcode': live.get('adcode', adcode),
                'province': live.get('province', ''),
                'city': live.get('city', ''),
                'district': live.get('district', ''),
                'weather': live.get('weather', ''),
                'temperature': float(live.get('temperature', 0)),
                'humidity': float(live.get('humidity', 0)),
                'wind_direction': live.get('winddirection', ''),
                'wind_power': live.get('windpower', ''),
                'report_time': live.get('reporttime', '')
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # 存入缓存
        weather_cache[cache_key] = (datetime.now().timestamp(), result)
        
        logger.info(f"天气查询成功: {adcode} - {live.get('city')}")
        return jsonify(result)
        
    except requests.exceptions.Timeout:
        logger.error("高德API请求超时")
        return jsonify({
            'success': False,
            'code': 504,
            'message': '请求高德API超时',
            'timestamp': datetime.now().isoformat()
        }), 504
        
    except requests.exceptions.RequestException as e:
        logger.error(f"高德API请求失败: {str(e)}")
        return jsonify({
            'success': False,
            'code': 502,
            'message': f'请求高德API失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 502
        
    except Exception as e:
        logger.error(f"服务器错误: {str(e)}")
        return jsonify({
            'success': False,
            'code': 500,
            'message': f'服务器错误: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/weather/cache/<adcode>', methods=['DELETE'])
def clear_cache(adcode):
    """清除指定地区的缓存"""
    cache_key = f"weather_{adcode}"
    if cache_key in weather_cache:
        del weather_cache[cache_key]
        return jsonify({
            'success': True,
            'message': f'已清除{adcode}的缓存',
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({
            'success': True,
            'message': f'{adcode}无缓存',
            'timestamp': datetime.now().isoformat()
        })


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'code': 404,
        'message': '接口不存在',
        'timestamp': datetime.now().isoformat()
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'code': 405,
        'message': '请求方法不允许',
        'timestamp': datetime.now().isoformat()
    }), 405


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"启动高德天气转发服务...")
    print(f"端口: {port}")
    print(f"调试模式: {debug}")
    print(f"高德API Key: {AMAP_API_KEY[:5]}...")
    print(f"缓存时间: {CACHE_TIMEOUT}秒")
    print("\n测试接口: http://localhost:8000/api/weather/current/110000")
    
    app.run(host='0.0.0.0', port=port, debug=debug)