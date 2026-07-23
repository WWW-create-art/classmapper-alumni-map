import os

SUPPORTED_INPUT_SUFFIXES = ('.xlsx', '.xls', '.csv')


def is_supported_input(path):
    """判断输入文件是否存在且格式可读。"""
    return os.path.isfile(path) and path.lower().endswith(SUPPORTED_INPUT_SUFFIXES)


def clean_path(path):
    """清理拖拽或命令行传入的路径。"""
    return path.strip().strip('"').strip("'")


def get_user_config(input_path=None, output_dir="蹭饭地图结果"):
    """获取用户配置信息"""
    config = {
        "input_path": clean_path(input_path) if input_path else "",
        "output_dir": output_dir
    }

    print("=" * 50)
    print("同学蹭饭地图生成器 v1.5")
    print("=" * 50)

    if config["input_path"]:
        if not is_supported_input(config["input_path"]):
            raise FileNotFoundError(f"输入文件不存在或格式不支持: {config['input_path']}")
        os.makedirs(config["output_dir"], exist_ok=True)
        return config

    # 获取名单文件路径
    while not config["input_path"]:
        path = clean_path(input("请输入名单文件路径（支持xlsx/xls/csv，直接拖拽文件到此处或输入路径）："))
        if is_supported_input(path):
            config["input_path"] = path
        else:
            print("❌ 文件不存在或不是支持的名单文件，请重新输入")

    # 创建输出目录
    os.makedirs(config["output_dir"], exist_ok=True)

    return config
