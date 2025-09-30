import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime
import re
from collections import Counter

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

print("="*80)
print("vivo手机用户画像分析".center(80))
print("="*80)

# 查找已清洗的数据文件
files = [f for f in os.listdir('.') if f.endswith('已清洗.xlsx')]
if not files:
    print("\n⚠️  未找到已清洗的数据文件，使用原始文件...")
    files = [f for f in os.listdir('.') if f.endswith('_FromTB.xlsx') and not f.startswith('~$')]

if not files:
    print("\n❌ 错误：未找到数据文件！")
    exit()

latest_file = max(files, key=lambda f: os.path.getmtime(f))
print(f"\n📁 数据文件: {latest_file}")

# 读取数据
df = pd.read_excel(latest_file, sheet_name='商品评论')
total_reviews = len(df)
print(f"📊 评论总数: {total_reviews:,} 条")

# ============================================================================
# 一、消费能力分析（基于购买配置）
# ============================================================================
print(f"\n{'='*80}")
print("【一、消费能力分析】".center(80))
print(f"{'='*80}")

# 提取内存配置（如 12GB+256GB）
def extract_memory_config(text):
    """从购买记录中提取内存配置"""
    if pd.isna(text):
        return None
    text = str(text)
    # 匹配 XGB+XXGB 格式
    match = re.search(r'(\d+)GB[\+\s]*(\d+)GB', text)
    if match:
        ram = int(match.group(1))
        storage = int(match.group(2))
        return f"{ram}GB+{storage}GB"
    return None

df['内存配置'] = df['购买记录'].apply(extract_memory_config)

# 统计配置分布
config_counts = df['内存配置'].value_counts()
config_percent = (config_counts / total_reviews * 100).round(1)

print("\n▶ 内存配置分布:")
print("-" * 60)
for config, count in config_counts.items():
    percent = config_percent[config]
    bar = "█" * int(percent / 2)
    print(f"  {config:15s} | {count:4d}条 ({percent:5.1f}%) {bar}")

# 配置等级分类
def classify_config_level(config):
    """将配置分为高中低三个等级"""
    if pd.isna(config):
        return "未知"
    
    # 提取存储容量
    match = re.search(r'\+(\d+)GB', str(config))
    if match:
        storage = int(match.group(1))
        if storage >= 512:
            return "高配置"
        elif storage >= 256:
            return "中配置"
        else:
            return "基础配置"
    return "未知"

df['配置等级'] = df['内存配置'].apply(classify_config_level)

level_counts = df['配置等级'].value_counts()
level_percent = (level_counts / total_reviews * 100).round(1)

print("\n▶ 消费能力等级:")
print("-" * 60)
for level in ['高配置', '中配置', '基础配置', '未知']:
    if level in level_counts.index:
        count = level_counts[level]
        percent = level_percent[level]
        print(f"  {level:10s} ({count:4d}条, {percent:5.1f}%)")

# 绘制配置分布饼图
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
colors_config = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7']
plt.pie(config_counts.values, labels=config_counts.index, autopct='%1.1f%%', 
        colors=colors_config, startangle=90)
plt.title('内存配置分布', fontsize=14, fontweight='bold')

plt.subplot(1, 2, 2)
colors_level = ['#ff6b6b', '#feca57', '#48dbfb', '#dfe6e9']
level_data = level_counts.reindex(['高配置', '中配置', '基础配置', '未知'], fill_value=0)
plt.pie(level_data.values, labels=level_data.index, autopct='%1.1f%%',
        colors=colors_level, startangle=90)
plt.title('消费能力等级分布', fontsize=14, fontweight='bold')

plt.tight_layout()
plt.savefig('用户画像_消费能力.png', dpi=300, bbox_inches='tight')
print("\n💾 图表已保存: 用户画像_消费能力.png")

# 消费洞察
print(f"\n💡 消费能力洞察:")
high_config = level_counts.get('高配置', 0)
mid_config = level_counts.get('中配置', 0)
if high_config > mid_config:
    print(f"   - 高配置用户占比最高({level_percent.get('高配置', 0):.1f}%)，说明用户消费能力强")
    print(f"   - 建议：突出旗舰性能、游戏体验等高端卖点")
else:
    print(f"   - 基础/中配置用户占比较高，用户更关注性价比")
    print(f"   - 建议：强调性价比、日常使用足够等卖点")

# ============================================================================
# 二、颜色偏好分析
# ============================================================================
print(f"\n{'='*80}")
print("【二、颜色偏好分析】".center(80))
print(f"{'='*80}")

# 提取颜色
def extract_color(text):
    """从购买记录中提取颜色"""
    if pd.isna(text):
        return None
    text = str(text)
    
    # 常见颜色关键词
    colors = ['曜夜黑', '星光白', '远航蓝', '幻夜黑', '星空蓝', '流光紫', 
              '黑色', '白色', '蓝色', '紫色', '绿色', '红色', '粉色']
    
    for color in colors:
        if color in text:
            return color
    return "其他"

df['颜色'] = df['购买记录'].apply(extract_color)

# 统计颜色分布
color_counts = df['颜色'].value_counts()
color_percent = (color_counts / total_reviews * 100).round(1)

print("\n▶ 颜色偏好排名:")
print("-" * 60)
for i, (color, count) in enumerate(color_counts.items(), 1):
    percent = color_percent[color]
    bar = "█" * int(percent / 2)
    print(f"  {i}. {color:10s} | {count:4d}条 ({percent:5.1f}%) {bar}")

# 绘制颜色分布图
plt.figure(figsize=(12, 6))

# 条形图
plt.subplot(1, 2, 1)
colors_map = {
    '曜夜黑': '#000000', '幻夜黑': '#1a1a1a', '黑色': '#2c3e50',
    '星光白': '#ecf0f1', '白色': '#bdc3c7',
    '远航蓝': '#3498db', '星空蓝': '#5dade2', '蓝色': '#74b9ff',
    '流光紫': '#9b59b6', '紫色': '#a29bfe',
    '绿色': '#55efc4', '红色': '#ff7675', '粉色': '#fd79a8',
    '其他': '#95a5a6'
}

bar_colors = [colors_map.get(color, '#95a5a6') for color in color_counts.index]
plt.barh(range(len(color_counts)), color_counts.values, color=bar_colors)
plt.yticks(range(len(color_counts)), color_counts.index)
plt.xlabel('数量', fontsize=12)
plt.title('各颜色销量排名', fontsize=14, fontweight='bold')
plt.gca().invert_yaxis()

# 添加数值标签
for i, (color, count) in enumerate(color_counts.items()):
    plt.text(count, i, f' {count}', va='center', fontsize=10)

# 饼图
plt.subplot(1, 2, 2)
# 只显示前5个颜色，其他合并
top_colors = color_counts.head(5)
other_sum = color_counts[5:].sum() if len(color_counts) > 5 else 0
if other_sum > 0:
    top_colors['其他'] = other_sum

pie_colors = [colors_map.get(color, '#95a5a6') for color in top_colors.index]
plt.pie(top_colors.values, labels=top_colors.index, autopct='%1.1f%%',
        colors=pie_colors, startangle=90)
plt.title('颜色偏好占比', fontsize=14, fontweight='bold')

plt.tight_layout()
plt.savefig('用户画像_颜色偏好.png', dpi=300, bbox_inches='tight')
print("\n💾 图表已保存: 用户画像_颜色偏好.png")

# 颜色评价分析
print(f"\n▶ 颜色评价关联分析:")
print("-" * 60)
for color in color_counts.head(3).index:
    if color != '其他':
        color_reviews = df[df['颜色'] == color]['评论内容'].astype(str)
        # 统计正面评价关键词
        positive_keywords = ['好看', '漂亮', '喜欢', '美', '高级', '大气', '显干净', '耐脏']
        positive_count = sum(color_reviews.str.contains('|'.join(positive_keywords), na=False))
        print(f"  {color}: {positive_count}条包含正面评价 ({positive_count/len(color_reviews)*100:.1f}%)")

print(f"\n💡 颜色偏好洞察:")
if len(color_counts) > 0:
    top_color = color_counts.index[0]
    top_percent = color_percent.iloc[0]
    print(f"   - {top_color}最受欢迎({top_percent:.1f}%)，建议加大此颜色备货")
    
    # 分析黑白色系
    dark_colors = ['曜夜黑', '幻夜黑', '黑色']
    light_colors = ['星光白', '白色']
    dark_total = sum(color_counts.get(c, 0) for c in dark_colors)
    light_total = sum(color_counts.get(c, 0) for c in light_colors)
    
    if dark_total > light_total:
        print(f"   - 深色系更受欢迎(占{dark_total/total_reviews*100:.1f}%)，用户偏好沉稳风格")
    else:
        print(f"   - 浅色系更受欢迎(占{light_total/total_reviews*100:.1f}%)，用户偏好简洁风格")

# ============================================================================
# 三、购买场景分析（推测）
# ============================================================================
print(f"\n{'='*80}")
print("【三、购买场景分析】".center(80))
print(f"{'='*80}")

# 3.1 时间维度分析
print("\n▶ 时间维度分析:")
print("-" * 60)

# 提取购买时间
def extract_date(text):
    """从购买记录中提取日期"""
    if pd.isna(text):
        return None
    text = str(text)
    # 匹配 YYYY年MM月DD日 格式
    match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        try:
            return pd.Timestamp(year=year, month=month, day=day)
        except:
            return None
    return None

df['购买时间'] = df['购买记录'].apply(extract_date)

# 按月份统计
df['购买月份'] = df['购买时间'].dt.month
month_counts = df['购买月份'].value_counts().sort_index()

# 按星期统计
df['购买星期'] = df['购买时间'].dt.dayofweek  # 0=周一, 6=周日
week_map = {0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五', 5: '周六', 6: '周日'}
df['购买星期名'] = df['购买星期'].map(week_map)
weekday_counts = df['购买星期名'].value_counts()

print(f"  月份分布:")
for month, count in month_counts.items():
    if pd.notna(month):
        percent = count / len(df[df['购买月份'].notna()]) * 100
        bar = "█" * int(percent / 3)
        print(f"    {month:2.0f}月: {count:4d}条 ({percent:5.1f}%) {bar}")

# 定义特殊日期识别规则（全局变量）
SPECIAL_DATE_RULES = {
    '618大促': '6月15日-20日',
    '双11大促': '11月9日-12日',
    '春节': '1-2月1日-15日（春节前后）',
    '国庆': '10月1日-7日'
}

# 识别节假日和大促
def identify_special_day(date):
    """识别节假日和电商大促"""
    if pd.isna(date):
        return "普通日"
    
    month = date.month
    day = date.day
    
    # 618大促
    if month == 6 and 15 <= day <= 20:
        return "618大促"
    # 双11
    elif month == 11 and 9 <= day <= 12:
        return "双11大促"
    # 春节
    elif month in [1, 2] and day <= 15:
        return "春节"
    # 国庆
    elif month == 10 and day <= 7:
        return "国庆"
    # 其他
    else:
        return "普通日"

df['特殊日期'] = df['购买时间'].apply(identify_special_day)
special_counts = df['特殊日期'].value_counts()

print(f"\n  【特殊日期识别规则】")
print("  " + "-" * 76)
print(f"  说明: 基于购买记录中的日期（格式：YYYY年MM月DD日）进行识别\n")
for day_type, date_range in SPECIAL_DATE_RULES.items():
    if day_type in special_counts.index:
        count = special_counts[day_type]
        percent = count / total_reviews * 100
        print(f"  • {day_type} ({count}条, {percent:.1f}%)")
        print(f"    识别范围: {date_range}")

# 显示普通日
if '普通日' in special_counts.index:
    count = special_counts['普通日']
    percent = count / total_reviews * 100
    print(f"  • 普通日 ({count}条, {percent:.1f}%)")
    print(f"    说明: 不在以上特殊日期范围内的日期")

# 3.2 评论维度分析
print(f"\n▶ 用户身份识别（基于评论内容）:")
print("-" * 60)

# 定义用户群体分类关键词（全局变量，方便在报告中引用）
USER_GROUP_KEYWORDS = {
    '学生群体': ['学生', '上学', '课', '宿舍', '同学', '考试', '作业'],
    '孝心消费': ['爸妈', '父母', '妈妈', '爸爸', '老人', '长辈'],
    '职场人士': ['上班', '工作', '公司', '通勤', '办公'],
    '游戏玩家': ['游戏', '吃鸡', '王者', '打游戏', '开黑']
}

# 识别用户群体
def identify_user_group(text):
    """从评论中识别用户群体"""
    if pd.isna(text):
        return "未知"
    text = str(text)
    
    # 学生群体关键词
    if any(word in text for word in USER_GROUP_KEYWORDS['学生群体']):
        return "学生群体"
    # 给父母买
    elif any(word in text for word in USER_GROUP_KEYWORDS['孝心消费']):
        return "孝心消费"
    # 职场人士
    elif any(word in text for word in USER_GROUP_KEYWORDS['职场人士']):
        return "职场人士"
    # 游戏玩家
    elif any(word in text for word in USER_GROUP_KEYWORDS['游戏玩家']):
        return "游戏玩家"
    else:
        return "普通用户"

df['用户群体'] = df['评论内容'].apply(identify_user_group)
group_counts = df['用户群体'].value_counts()

print(f"\n  【用户群体分类标准】")
print("  " + "-" * 76)
for group, keywords in USER_GROUP_KEYWORDS.items():
    if group in group_counts.index:
        count = group_counts[group]
        percent = count / total_reviews * 100
        keyword_str = '、'.join(keywords)
        print(f"  • {group} ({count}条, {percent:.1f}%)")
        print(f"    关键词: {keyword_str}")

# 显示普通用户
if '普通用户' in group_counts.index:
    count = group_counts['普通用户']
    percent = count / total_reviews * 100
    print(f"  • 普通用户 ({count}条, {percent:.1f}%)")
    print(f"    说明: 未匹配以上任何关键词的用户")

# 绘制购买场景图表
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 1. 月份趋势
ax1 = axes[0, 0]
if len(month_counts) > 0:
    ax1.plot(month_counts.index, month_counts.values, marker='o', linewidth=2, markersize=8)
    ax1.fill_between(month_counts.index, month_counts.values, alpha=0.3)
    ax1.set_xlabel('月份', fontsize=12)
    ax1.set_ylabel('评论数量', fontsize=12)
    ax1.set_title('购买时间分布（按月）', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)

# 2. 星期分布
ax2 = axes[0, 1]
week_order = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
week_data = [weekday_counts.get(day, 0) for day in week_order]
colors_week = ['#3498db' if i < 5 else '#e74c3c' for i in range(7)]
ax2.bar(week_order, week_data, color=colors_week)
ax2.set_xlabel('星期', fontsize=12)
ax2.set_ylabel('评论数量', fontsize=12)
ax2.set_title('购买时间分布（按星期）', fontsize=14, fontweight='bold')
ax2.tick_params(axis='x', rotation=45)

# 3. 特殊日期
ax3 = axes[1, 0]
colors_special = ['#e74c3c', '#f39c12', '#3498db', '#2ecc71', '#95a5a6']
ax3.pie(special_counts.values, labels=special_counts.index, autopct='%1.1f%%',
        colors=colors_special, startangle=90)
ax3.set_title('特殊日期占比', fontsize=14, fontweight='bold')

# 4. 用户群体
ax4 = axes[1, 1]
colors_group = ['#3498db', '#e74c3c', '#f39c12', '#2ecc71', '#9b59b6']
ax4.barh(range(len(group_counts)), group_counts.values, color=colors_group)
ax4.set_yticks(range(len(group_counts)))
ax4.set_yticklabels(group_counts.index)
ax4.set_xlabel('数量', fontsize=12)
ax4.set_title('用户群体分布', fontsize=14, fontweight='bold')
ax4.invert_yaxis()

# 添加数值标签
for i, count in enumerate(group_counts.values):
    ax4.text(count, i, f' {count}', va='center', fontsize=10)

plt.tight_layout()
plt.savefig('用户画像_购买场景.png', dpi=300, bbox_inches='tight')
print("\n💾 图表已保存: 用户画像_购买场景.png")

print(f"\n💡 购买场景洞察:")
# 节假日分析
promo_reviews = special_counts.get('618大促', 0) + special_counts.get('双11大促', 0)
if promo_reviews > 0:
    promo_percent = promo_reviews / total_reviews * 100
    print(f"   - 节假日/大促期间销量占{promo_percent:.1f}%，用户偏好大促购买")
    print(f"   - 建议：加大618/双11促销力度")

# 工作日 vs 周末
weekday_total = sum(weekday_counts.get(day, 0) for day in ['周一', '周二', '周三', '周四', '周五'])
weekend_total = sum(weekday_counts.get(day, 0) for day in ['周六', '周日'])
if weekday_total > weekend_total:
    print(f"   - 工作日下单更多，用户利用碎片时间购物")
else:
    print(f"   - 周末下单更多，用户有充足时间比较选择")

# 用户群体分析
if '学生群体' in group_counts.index and group_counts['学生群体'] / total_reviews > 0.1:
    print(f"   - 学生群体占比{group_counts['学生群体']/total_reviews*100:.1f}%，建议强调学生党用")

# ============================================================================
# 生成综合报告
# ============================================================================
print(f"\n{'='*80}")
print("【用户画像综合报告】".center(80))
print(f"{'='*80}")

report_file = f'用户画像分析报告_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
with open(report_file, 'w', encoding='utf-8') as f:
    f.write("="*80 + "\n")
    f.write("vivo手机用户画像分析报告\n".center(80))
    f.write("="*80 + "\n\n")
    f.write(f"分析时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n")
    f.write(f"数据来源: {latest_file}\n")
    f.write(f"样本数量: {total_reviews:,} 条评论\n\n")
    
    f.write("一、消费能力画像\n")
    f.write("-" * 80 + "\n")
    f.write("分类标准: 基于购买配置（内存+存储容量）\n")
    f.write("  • 高配置: 存储容量 ≥ 512GB\n")
    f.write("  • 中配置: 存储容量 256GB\n")
    f.write("  • 基础配置: 存储容量 < 256GB\n\n")
    f.write("分布情况:\n")
    for level in ['高配置', '中配置', '基础配置']:
        if level in level_counts.index:
            f.write(f"  {level}: {level_counts[level]}条 ({level_percent[level]:.1f}%)\n")
    f.write("\n详细配置分布:\n")
    for config, count in config_counts.items():
        f.write(f"  {config}: {count}条 ({config_percent[config]:.1f}%)\n")
    f.write("\n")
    
    f.write("二、颜色偏好画像\n")
    f.write("-" * 80 + "\n")
    f.write("提取方式: 从购买记录中识别颜色关键词\n\n")
    f.write("TOP5颜色:\n")
    for i, (color, count) in enumerate(color_counts.head(5).items(), 1):
        f.write(f"  {i}. {color}: {count}条 ({color_percent[color]:.1f}%)\n")
    f.write("\n")
    
    f.write("三、购买场景画像\n")
    f.write("-" * 80 + "\n")
    
    f.write("\n3.1 用户群体分类\n")
    f.write("识别方式: 基于评论内容中的关键词匹配\n\n")
    for group, keywords in USER_GROUP_KEYWORDS.items():
        if group in group_counts.index:
            count = group_counts[group]
            percent = count / total_reviews * 100
            keyword_str = '、'.join(keywords)
            f.write(f"• {group} ({count}条, {percent:.1f}%)\n")
            f.write(f"  关键词: {keyword_str}\n\n")
    
    if '普通用户' in group_counts.index:
        count = group_counts['普通用户']
        percent = count / total_reviews * 100
        f.write(f"• 普通用户 ({count}条, {percent:.1f}%)\n")
        f.write(f"  说明: 未匹配以上任何关键词的用户\n\n")
    
    f.write("\n3.2 特殊日期分布\n")
    f.write("识别方式: 基于购买记录中的日期（格式：YYYY年MM月DD日）\n\n")
    for day_type, date_range in SPECIAL_DATE_RULES.items():
        if day_type in special_counts.index:
            count = special_counts[day_type]
            percent = count / total_reviews * 100
            f.write(f"• {day_type} ({count}条, {percent:.1f}%)\n")
            f.write(f"  识别范围: {date_range}\n\n")
    
    if '普通日' in special_counts.index:
        count = special_counts['普通日']
        percent = count / total_reviews * 100
        f.write(f"• 普通日 ({count}条, {percent:.1f}%)\n")
        f.write(f"  说明: 不在以上特殊日期范围内的日期\n\n")
    
    f.write("\n" + "="*80 + "\n")
    f.write("分析方法说明:\n")
    f.write("-" * 80 + "\n")
    f.write("1. 消费能力: 通过正则表达式提取购买记录中的配置信息（如 12GB+256GB）\n")
    f.write("2. 颜色偏好: 从购买记录中匹配常见颜色关键词\n")
    f.write("3. 购买时间: 从购买记录中提取日期并按月份、星期、特殊日期统计\n")
    f.write("4. 用户群体: 在评论内容中搜索特定关键词组合进行分类\n")
    
    # 添加分类样本示例
    f.write("\n" + "="*80 + "\n")
    f.write("用户群体分类样本示例:\n")
    f.write("-" * 80 + "\n")
    
    for group, keywords in USER_GROUP_KEYWORDS.items():
        if group in group_counts.index and group_counts[group] > 0:
            f.write(f"\n【{group}】\n")
            group_samples = df[df['用户群体'] == group]['评论内容'].head(2)
            for i, sample in enumerate(group_samples, 1):
                sample_text = str(sample)[:80] + '...' if len(str(sample)) > 80 else str(sample)
                f.write(f"  样本{i}: {sample_text}\n")
    
    f.write("\n" + "="*80 + "\n")
    f.write("报告生成完毕\n")

print(f"\n✅ 分析完成！")
print(f"   - 图表文件: 用户画像_消费能力.png")
print(f"   - 图表文件: 用户画像_颜色偏好.png")
print(f"   - 图表文件: 用户画像_购买场景.png")
print(f"   - 报告文件: {report_file}")
print(f"\n{'='*80}")
