import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager
from wordcloud import WordCloud


FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]


def find_chinese_font():
    """寻找系统可用中文字体。"""
    for font_path in FONT_CANDIDATES:
        if os.path.exists(font_path):
            return font_path
    return None


def configure_matplotlib_font(font_path):
    if not font_path:
        return

    font_prop = font_manager.FontProperties(fname=font_path)
    plt.rcParams["font.sans-serif"] = [font_prop.get_name()]
    plt.rcParams["axes.unicode_minus"] = False


def generate_wordcloud(df, output_dir):
    """生成学校分布词云图。"""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "学校分布词云.png")
    school_counts = df["学校"].value_counts().to_dict()
    font_path = find_chinese_font()

    try:
        wordcloud = WordCloud(
            font_path=font_path,
            width=1200,
            height=700,
            background_color="white",
            max_words=100,
            colormap="tab20",
            prefer_horizontal=0.95,
            margin=8,
        )
        wordcloud.generate_from_frequencies(school_counts)
        wordcloud.to_file(output_path)
    except Exception as exc:
        print(f"⚠️ 词云生成失败，已改为柱状图: {exc}")
        generate_school_bar_chart(df, output_path, font_path)

    print(f"✅ 已生成学校分布词云: {output_path}")
    return output_path


def generate_school_bar_chart(df, output_path, font_path=None):
    configure_matplotlib_font(font_path)
    school_counts = df["学校"].value_counts().sort_values(ascending=True)

    fig_height = max(5, len(school_counts) * 0.45)
    plt.figure(figsize=(11, fig_height))
    bars = plt.barh(school_counts.index, school_counts.values, color="#4C78A8")
    plt.title("学校分布")
    plt.xlabel("人数")
    plt.grid(axis="x", alpha=0.25)

    for bar in bars:
        width = bar.get_width()
        plt.text(width + 0.03, bar.get_y() + bar.get_height() / 2, int(width), va="center")

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()


def generate_stats(df, output_dir):
    """生成城市、学校和原始数据统计表。"""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "大学分布统计.xlsx")

    total = len(df)
    city_stats = (
        df.groupby("城市", dropna=False)
        .agg(
            人数=("姓名", "count"),
            学校数=("学校", "nunique"),
            学校列表=("学校", lambda values: "、".join(sorted(set(values)))),
            同学=("姓名", lambda values: "、".join(values)),
        )
        .reset_index()
        .sort_values(["人数", "城市"], ascending=[False, True])
    )
    city_stats["占比"] = city_stats["人数"].map(lambda count: f"{count / total:.1%}")

    school_stats = (
        df.groupby("学校", dropna=False)
        .agg(
            人数=("姓名", "count"),
            城市=("城市", "first"),
            同学=("姓名", lambda values: "、".join(values)),
        )
        .reset_index()
        .sort_values(["人数", "学校"], ascending=[False, True])
    )
    school_stats["占比"] = school_stats["人数"].map(lambda count: f"{count / total:.1%}")

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        city_stats.to_excel(writer, sheet_name="城市分布统计", index=False)
        school_stats.to_excel(writer, sheet_name="学校分布统计", index=False)
        df.to_excel(writer, sheet_name="原始数据", index=False)

        for worksheet in writer.book.worksheets:
            worksheet.freeze_panes = "A2"
            for column_cells in worksheet.columns:
                max_length = max(len(str(cell.value or "")) for cell in column_cells)
                column_letter = column_cells[0].column_letter
                worksheet.column_dimensions[column_letter].width = min(max(max_length + 2, 10), 42)

    print(f"✅ 已生成统计数据: {output_path}")
    return output_path
