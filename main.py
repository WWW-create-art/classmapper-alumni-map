import pandas as pd
import argparse
import os
import webbrowser
import numpy as np
from tqdm import tqdm

# 导入自定义模块
from config import get_user_config
from geolocation import KNOWN_LOCATIONS, load_cache, save_cache, get_school_location, add_location_data
from html_generator import generate_html_template
from utils import open_output_directory


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="生成同学大学分布地图、词云和统计表")
    parser.add_argument("input_path", nargs="?", help="名单文件路径，支持 xlsx/xls/csv")
    parser.add_argument("-o", "--output-dir", default="蹭饭地图结果", help="输出目录")
    parser.add_argument("--no-open", action="store_true", help="生成完成后不自动打开地图和输出目录")
    parser.add_argument("--map-only", action="store_true", help="只生成地图网页，跳过词云和统计表")
    return parser.parse_args(argv)


def read_roster(input_path):
    """读取名单数据。"""
    suffix = os.path.splitext(input_path)[1].lower()
    if suffix == ".csv":
        df = pd.read_csv(input_path)
    else:
        df = pd.read_excel(input_path)

    df.columns = [str(column).strip() for column in df.columns]
    if '姓名' not in df.columns or '学校' not in df.columns:
        raise ValueError("名单文件中必须包含'姓名'和'学校'两列")

    df = df.copy()
    df['姓名'] = df['姓名'].fillna("").astype(str).str.strip()
    df['学校'] = df['学校'].fillna("").astype(str).str.strip()
    df = df[(df['姓名'] != "") & (df['学校'] != "")]
    return df


def main(argv=None):
    """主程序"""
    # 获取用户配置
    args = parse_args(argv)
    try:
        config = get_user_config(args.input_path, args.output_dir)
    except Exception as e:
        print(f"❌ 配置错误: {str(e)}")
        if args.input_path is None:
            input("按Enter键退出...")
        return

    output_dir = config["output_dir"]

    # 读取名单数据
    try:
        df = read_roster(config["input_path"])
        print(f"✅ 成功读取名单数据，共 {len(df)} 条记录")
    except Exception as e:
        print(f"❌ 读取名单文件失败: {str(e)}")
        if args.input_path is None:
            input("按Enter键退出...")
        return
    
    # 加载位置缓存
    cache_path = os.path.join(output_dir, "location_cache.json")
    cache = load_cache(cache_path)
    
    # 获取学校地理位置
    print("正在获取学校地理位置...")
    schools = df['学校'].unique()
    locations = {}
    
    for school in tqdm(schools, desc="处理学校"):
        locations[school] = get_school_location(school, cache)
    
    # 保存缓存
    save_cache(cache, cache_path)
    
    # 添加位置信息到DataFrame
    df = add_location_data(df, locations)
    
    # 准备地图数据
    markers = prepare_map_data(df, locations)
    roster = prepare_roster_data(df, locations)
    center = calculate_map_center(locations)
    location_lookup = {**KNOWN_LOCATIONS, **locations}

    # 生成优化的HTML地图
    map_path = os.path.join(output_dir, "蹭饭地图.html")
    generate_html_template(center, markers, map_path, roster, location_lookup)
    
    wordcloud_path = None
    stats_path = None
    if not args.map_only:
        from visualization import generate_wordcloud, generate_stats

        # 生成词云图
        wordcloud_path = generate_wordcloud(df, output_dir)

        # 生成统计表格
        stats_path = generate_stats(df, output_dir)
    
    # 显示结果
    print("\n" + "=" * 50)
    print("🎉 处理完成！生成的文件:")
    print(f"- 蹭饭地图: {map_path}")
    if wordcloud_path and stats_path:
        print(f"- 学校词云: {wordcloud_path}")
        print(f"- 统计数据: {stats_path}")
    else:
        print("- 已跳过词云和统计表")
    print("=" * 50)
    
    # 尝试打开地图
    try:
        if not args.no_open:
            webbrowser.open(os.path.abspath(map_path))
            print("已尝试在浏览器中打开蹭饭地图")
    except Exception:
        print("⚠️ 无法自动打开地图，请手动打开HTML文件")

    # 打开输出目录
    if not args.no_open:
        open_output_directory(output_dir)

    if args.input_path is None:
        input("\n按Enter键退出程序...")

def prepare_map_data(df, locations):
    """准备地图标记数据"""
    markers = []
    for school, group in df.groupby('学校', sort=False):
        # 获取位置信息
        loc = locations[school]
        lat, lng = loc['coords']
        address = loc['address']

        # 获取该学校的所有学生
        students = group['姓名'].tolist()
        first_order = get_row_order(group.iloc[0], group.index[0])

        markers.append({
            "lat": lat,
            "lng": lng,
            "title": school,
            "students": students,
            "address": address,
            "count": len(students),
            "firstOrder": first_order
        })
    return markers


def prepare_roster_data(df, locations):
    """准备浏览器端可编辑的原始名单数据。"""
    records = []
    for index, row in df.iterrows():
        school = row['学校']
        loc = locations[school]
        lat, lng = loc['coords']
        records.append({
            "order": get_row_order(row, index),
            "name": row['姓名'],
            "school": school,
            "city": loc['city'],
            "address": loc['address'],
            "lat": lat,
            "lng": lng
        })
    return records


def get_row_order(row, index):
    if '序号' in row and pd.notna(row['序号']):
        try:
            return int(row['序号'])
        except (TypeError, ValueError):
            pass
    return int(index) + 1

def calculate_map_center(locations):
    """计算地图中心点"""
    valid_coords = [loc['coords'] for loc in locations.values() if tuple(loc['coords']) != (0, 0)]
    if valid_coords:
        center = np.mean(valid_coords, axis=0).tolist()
    else:
        center = [35.8617, 104.1954]  # 中国中心作为后备
    return center

if __name__ == "__main__":
    main()
