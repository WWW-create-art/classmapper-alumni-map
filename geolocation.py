import json
import os
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    from geopy.geocoders import Nominatim
except ImportError:
    Nominatim = None


KNOWN_LOCATIONS = {
    "南京航空航天大学": {
        "city": "南京市",
        "coords": [32.0328, 118.8125],
        "address": "南京航空航天大学，南京市",
    },
    "南京大学": {
        "city": "南京市",
        "coords": [32.0584, 118.7965],
        "address": "南京大学，南京市",
    },
    "上海交通大学": {
        "city": "上海市",
        "coords": [31.0246, 121.4338],
        "address": "上海交通大学，上海市",
    },
    "中国社会科学院大学": {
        "city": "北京市",
        "coords": [39.7337, 116.1610],
        "address": "中国社会科学院大学，北京市",
    },
    "浙江大学": {
        "city": "杭州市",
        "coords": [30.3081, 120.0868],
        "address": "浙江大学，杭州市",
    },
    "复旦大学": {
        "city": "上海市",
        "coords": [31.2988, 121.5030],
        "address": "复旦大学，上海市",
    },
    "浙江（未注明学校）": {
        "city": "浙江省",
        "coords": [30.2741, 120.1551],
        "address": "浙江省杭州市（未注明学校）",
    },
    "对外经济贸易大学": {
        "city": "北京市",
        "coords": [39.9828, 116.4277],
        "address": "对外经济贸易大学，北京市",
    },
    "重庆大学": {
        "city": "重庆市",
        "coords": [29.5743, 106.4681],
        "address": "重庆大学，重庆市",
    },
    "湖南大学": {
        "city": "长沙市",
        "coords": [28.1790, 112.9460],
        "address": "湖南大学，长沙市",
    },
    "西安电子科技大学": {
        "city": "西安市",
        "coords": [34.1263, 108.8353],
        "address": "西安电子科技大学，西安市",
    },
    "四川大学": {
        "city": "成都市",
        "coords": [30.6346, 104.0872],
        "address": "四川大学，成都市",
    },
    "北京中医药大学": {
        "city": "北京市",
        "coords": [39.9525, 116.4238],
        "address": "北京中医药大学，北京市",
    },
    "中山大学": {
        "city": "广州市",
        "coords": [23.0962, 113.2988],
        "address": "中山大学，广州市",
    },
    "华南理工大学": {
        "city": "广州市",
        "coords": [23.160342, 113.3372426],
        "address": "华南理工大学，广州市",
    },
    "浙江警察学院": {
        "city": "杭州市",
        "coords": [30.1510, 120.0909],
        "address": "浙江警察学院，杭州市",
    },
    "华东师范大学": {
        "city": "上海市",
        "coords": [31.2288, 121.4020],
        "address": "华东师范大学，上海市",
    },
}


def get_school_location(school_name, cache):
    """获取学校地理位置（使用缓存机制）"""
    if school_name in KNOWN_LOCATIONS:
        result = KNOWN_LOCATIONS[school_name]
        cache[school_name] = result
        print(f"✅ 使用内置定位: {school_name} -> {result['address']}")
        return result

    # 检查缓存
    if school_name in cache:
        return cache[school_name]
    
    location = None
    city = "未知"
    coords = (0, 0)
    
    # 尝试多种查询格式
    queries = [
        f"{school_name}大学, 中国",
        f"{school_name}, 中国",
        school_name + "大学",
        school_name
    ]
    
    for query in queries:
        try:
            location = geocode_query(query)
            if location:
                break
        except Exception as e:
            print(f"⚠️ 查询'{school_name}'时出错: {str(e)}")
            continue
    
    if location:
        city = extract_city_name(location.address)
        address = format_school_address(school_name, city)
        coords = (location.latitude, location.longitude)
        print(f"✅ 定位成功: {school_name} -> {address}")
    else:
        print(f"⚠️ 无法定位: {school_name}")
        address = "未知位置"
    
    # 保存到缓存
    result = {"city": city, "coords": coords, "address": address}
    cache[school_name] = result
    return result


def geocode_query(query):
    if Nominatim is not None:
        geolocator = Nominatim(user_agent="cengfan_map_app")
        return geolocator.geocode(query, country_codes="cn", timeout=10)

    params = urlencode({
        "q": query,
        "format": "json",
        "limit": 1,
        "countrycodes": "cn",
        "accept-language": "zh-CN",
    })
    request = Request(
        f"https://nominatim.openstreetmap.org/search?{params}",
        headers={"User-Agent": "cengfan_map_app"},
    )
    with urlopen(request, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))
    if not data:
        return None
    return SimpleLocation(
        float(data[0]["lat"]),
        float(data[0]["lon"]),
        data[0].get("display_name", ""),
    )


class SimpleLocation:
    def __init__(self, latitude, longitude, address):
        self.latitude = latitude
        self.longitude = longitude
        self.address = address


def extract_city_name(address):
    """从定位服务返回的长地址中提取城市，避免把街道和校区写进地图。"""
    text = str(address or "")
    parts = [part.strip(" ,，") for part in re.split(r"[,，]", text) if part.strip(" ,，")]
    for part in reversed(parts):
        match = re.search(r"([\u4e00-\u9fff]{2,12}(?:市|自治州|地区|盟))$", part)
        if match:
            return match.group(1)

    match = re.search(r"([\u4e00-\u9fff]{2,12}市)", text)
    if match:
        return match.group(1)
    return "未知"


def format_school_address(school_name, city):
    if city and city != "未知":
        return f"{school_name}，{city}"
    return school_name

def load_cache(cache_path):
    """加载位置缓存"""
    cache = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding='utf-8') as f:
                cache = json.load(f)
            print(f"✅ 已加载缓存 ({len(cache)} 条记录)")
        except:  # noqa: E722
            pass
    return cache

def save_cache(cache, cache_path):
    """保存位置缓存"""
    cache_dir = os.path.dirname(cache_path)
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
    with open(cache_path, "w", encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    print(f"✅ 位置缓存已保存: {cache_path}")

def add_location_data(df, locations):
    """添加位置信息到DataFrame"""
    df['城市'] = df['学校'].map(lambda x: locations[x]['city'])
    df['经纬度'] = df['学校'].map(lambda x: locations[x]['coords'])
    return df
