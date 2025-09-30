import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime
import re
from collections import Counter

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

print("="*80)
print("vivo手机购买行为分析".center(80))
print("="*80)

# 查找数据文件
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
# 一、数据预处理：提取时间和配置信息
# ============================================================================
print(f"\n{'='*80}")
print("【一、数据预处理】".center(80))
print(f"{'='*80}")

# 提取购买时间
def extract_date(text):
    """从购买记录中提取日期"""
    if pd.isna(text):
        return None
    text = str(text)
    match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
    if match:
        try:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            return pd.Timestamp(year=year, month=month, day=day)
        except:
            return None
    return None

# 提取内存配置
def extract_memory_config(text):
    """从购买记录中提取内存配置"""
    if pd.isna(text):
        return None
    text = str(text)
    match = re.search(r'(\d+)GB[\+\s]*(\d+)GB', text)
    if match:
        ram = int(match.group(1))
        storage = int(match.group(2))
        return f"{ram}GB+{storage}GB"
    return None

df['购买时间'] = df['购买记录'].apply(extract_date)
df['配置'] = df['购买记录'].apply(extract_memory_config)

# 统计提取成功率
time_extracted = df['购买时间'].notna().sum()
config_extracted = df['配置'].notna().sum()

print(f"\n▶ 数据提取结果:")
print(f"  购买时间提取成功: {time_extracted}/{total_reviews} ({time_extracted/total_reviews*100:.1f}%)")
print(f"  配置信息提取成功: {config_extracted}/{total_reviews} ({config_extracted/total_reviews*100:.1f}%)")

# 过滤有效数据
df_valid = df[df['购买时间'].notna() & df['配置'].notna()].copy()
print(f"  有效数据: {len(df_valid)} 条")

# ============================================================================
# 二、时间趋势分析
# ============================================================================
print(f"\n{'='*80}")
print("【二、时间趋势分析】".center(80))
print(f"{'='*80}")

# 2.1 按月份统计
df_valid['月份'] = df_valid['购买时间'].dt.month
df_valid['日'] = df_valid['购买时间'].dt.day
df_valid['星期'] = df_valid['购买时间'].dt.dayofweek  # 0=周一, 6=周日
df_valid['季度'] = df_valid['购买时间'].dt.quarter

month_counts = df_valid['月份'].value_counts().sort_index()
day_counts = df_valid['日'].value_counts().sort_index()
week_counts = df_valid['星期'].value_counts().sort_index()
quarter_counts = df_valid['季度'].value_counts().sort_index()

print(f"\n▶ 按月份分布（TOP 5）:")
print("-" * 60)
for month, count in month_counts.head(5).items():
    percent = count / len(df_valid) * 100
    bar = "█" * int(percent / 3)
    print(f"  {month:2.0f}月: {count:4d}条 ({percent:5.1f}%) {bar}")

# 识别月内高峰日期
print(f"\n▶ 月内日期分布（TOP 10）:")
print("-" * 60)
for day, count in day_counts.head(10).items():
    percent = count / len(df_valid) * 100
    bar = "█" * int(count / day_counts.max() * 15)
    print(f"  {day:2.0f}日: {count:4d}条 ({percent:5.1f}%) {bar}")

# 工资日分析（假设1-5日、20-31日为关键期）
early_month = df_valid[df_valid['日'] <= 5]['日'].count()
mid_month = df_valid[(df_valid['日'] > 5) & (df_valid['日'] <= 19)]['日'].count()
late_month = df_valid[df_valid['日'] > 19]['日'].count()

print(f"\n▶ 月内时段分析:")
print("-" * 60)
print(f"  月初 (1-5日):     {early_month:4d}条 ({early_month/len(df_valid)*100:5.1f}%)")
print(f"  月中 (6-19日):    {mid_month:4d}条 ({mid_month/len(df_valid)*100:5.1f}%)")
print(f"  月末 (20-31日):   {late_month:4d}条 ({late_month/len(df_valid)*100:5.1f}%)")

# 星期分析
week_names = {0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五', 5: '周六', 6: '周日'}
print(f"\n▶ 按星期分布:")
print("-" * 60)
for day_num in range(7):
    count = week_counts.get(day_num, 0)
    percent = count / len(df_valid) * 100 if len(df_valid) > 0 else 0
    bar = "█" * int(count / week_counts.max() * 15) if week_counts.max() > 0 else ""
    print(f"  {week_names[day_num]}: {count:4d}条 ({percent:5.1f}%) {bar}")

weekday_total = sum(week_counts.get(i, 0) for i in range(5))
weekend_total = sum(week_counts.get(i, 0) for i in [5, 6])

print(f"\n  工作日总计: {weekday_total}条 ({weekday_total/len(df_valid)*100:.1f}%)")
print(f"  周末总计:   {weekend_total}条 ({weekend_total/len(df_valid)*100:.1f}%)")

# 季度分析
print(f"\n▶ 按季度分布:")
print("-" * 60)
for quarter, count in quarter_counts.items():
    percent = count / len(df_valid) * 100
    bar = "█" * int(percent / 3)
    print(f"  Q{quarter:.0f}: {count:4d}条 ({percent:5.1f}%) {bar}")

# 绘制时间趋势图
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 1. 月份趋势
ax1 = axes[0, 0]
ax1.plot(month_counts.index, month_counts.values, marker='o', linewidth=2.5, 
         markersize=8, color='#3498db')
ax1.fill_between(month_counts.index, month_counts.values, alpha=0.3, color='#3498db')
ax1.set_xlabel('月份', fontsize=12, fontweight='bold')
ax1.set_ylabel('购买数量', fontsize=12, fontweight='bold')
ax1.set_title('月度购买趋势', fontsize=14, fontweight='bold')
ax1.grid(True, alpha=0.3, linestyle='--')
ax1.set_xticks(range(1, 13))

# 2. 月内日期分布
ax2 = axes[0, 1]
ax2.bar(day_counts.index, day_counts.values, color='#2ecc71', alpha=0.7, edgecolor='black')
ax2.set_xlabel('日期', fontsize=12, fontweight='bold')
ax2.set_ylabel('购买数量', fontsize=12, fontweight='bold')
ax2.set_title('月内日期购买分布', fontsize=14, fontweight='bold')
ax2.grid(True, alpha=0.3, axis='y', linestyle='--')
# 标注关键区域
ax2.axvspan(1, 5, alpha=0.2, color='yellow', label='月初')
ax2.axvspan(20, 31, alpha=0.2, color='orange', label='月末')
ax2.legend()

# 3. 星期分布
ax3 = axes[1, 0]
week_data = [week_counts.get(i, 0) for i in range(7)]
week_labels = [week_names[i] for i in range(7)]
colors_week = ['#3498db' if i < 5 else '#e74c3c' for i in range(7)]
bars = ax3.bar(week_labels, week_data, color=colors_week, alpha=0.7, edgecolor='black')
ax3.set_xlabel('星期', fontsize=12, fontweight='bold')
ax3.set_ylabel('购买数量', fontsize=12, fontweight='bold')
ax3.set_title('星期购买分布（蓝=工作日，红=周末）', fontsize=14, fontweight='bold')
ax3.grid(True, alpha=0.3, axis='y', linestyle='--')

# 添加数值标签
for bar in bars:
    height = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., height,
             f'{int(height)}', ha='center', va='bottom', fontsize=9)

# 4. 季度分布
ax4 = axes[1, 1]
quarter_labels = [f'Q{int(q)}' for q in quarter_counts.index]
colors_quarter = ['#e74c3c', '#f39c12', '#2ecc71', '#3498db']
wedges, texts, autotexts = ax4.pie(quarter_counts.values, labels=quarter_labels, 
                                     autopct='%1.1f%%', colors=colors_quarter,
                                     startangle=90, textprops={'fontsize': 11, 'fontweight': 'bold'})
ax4.set_title('季度购买分布', fontsize=14, fontweight='bold')

plt.tight_layout()
time_trend_file = f'购买行为_时间趋势_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
plt.savefig(time_trend_file, dpi=300, bbox_inches='tight')
print(f"\n💾 时间趋势图已保存: {time_trend_file}")

# ============================================================================
# 三、配置选择逻辑分析
# ============================================================================
print(f"\n{'='*80}")
print("【三、配置选择逻辑分析】".center(80))
print(f"{'='*80}")

# 3.1 配置销量统计
config_counts = df_valid['配置'].value_counts()
config_percent = (config_counts / len(df_valid) * 100).round(1)

print(f"\n▶ 配置销量排名:")
print("-" * 60)
for i, (config, count) in enumerate(config_counts.items(), 1):
    percent = config_percent[config]
    bar = "█" * int(percent / 3)
    print(f"  {i}. {config:15s} | {count:4d}条 ({percent:5.1f}%) {bar}")

# 3.2 配置关联的关键词分析
print(f"\n▶ 各配置关联评论关键词分析:")
print("-" * 80)

# 定义关键词分类
keyword_groups = {
    '性价比': ['性价比', '划算', '值得', '实惠', '便宜', '超值'],
    '内存够用': ['够用', '足够', '日常', '正常', '满足'],
    '性能强': ['流畅', '快', '强', '强大', '好用', '运行'],
    '存储大': ['内存', '存储', '空间', '大', '视频', '照片'],
    '游戏': ['游戏', '吃鸡', '王者', '打游戏'],
    '拍照': ['拍照', '相机', '清晰', '像素'],
}

config_keywords = {}

for config in config_counts.head(5).index:
    config_reviews = df_valid[df_valid['配置'] == config]['评论内容'].astype(str)
    all_text = ' '.join(config_reviews)
    
    config_keywords[config] = {}
    
    print(f"\n【{config}】")
    print(f"  销量: {config_counts[config]}条 ({config_percent[config]:.1f}%)")
    print(f"  关键词分布:")
    
    for group_name, keywords in keyword_groups.items():
        count = sum(config_reviews.str.contains(kw, na=False).sum() for kw in keywords)
        percent = count / len(config_reviews) * 100 if len(config_reviews) > 0 else 0
        config_keywords[config][group_name] = count
        
        if count > 0:
            print(f"    • {group_name}: {count}次提及 ({percent:.1f}%)")

# 3.3 配置价格感知分析（基于关键词）
print(f"\n▶ 配置价格感知分析:")
print("-" * 80)

price_positive = ['便宜', '实惠', '划算', '值', '超值', '性价比']
price_negative = ['贵', '贵了', '有点贵', '小贵']

for config in config_counts.head(5).index:
    config_reviews = df_valid[df_valid['配置'] == config]['评论内容'].astype(str)
    
    positive_count = sum(config_reviews.str.contains(kw, na=False).sum() for kw in price_positive)
    negative_count = sum(config_reviews.str.contains(kw, na=False).sum() for kw in price_negative)
    
    print(f"\n  {config}:")
    print(f"    正面价格评价: {positive_count}条")
    print(f"    负面价格评价: {negative_count}条")
    
    if positive_count > negative_count * 2:
        print(f"    💡 结论: 价格认可度高，是性价比之选")
    elif negative_count > positive_count:
        print(f"    💡 结论: 价格敏感，可考虑优化定价")
    else:
        print(f"    💡 结论: 价格评价中等")

# 绘制配置分析图
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# 1. 配置销量占比
ax1 = axes[0]
top_configs = config_counts.head(8)
colors_config = plt.cm.Set3(np.linspace(0, 1, len(top_configs)))
wedges, texts, autotexts = ax1.pie(top_configs.values, labels=top_configs.index,
                                     autopct='%1.1f%%', colors=colors_config,
                                     startangle=90, textprops={'fontsize': 10})
ax1.set_title('配置销量占比（TOP 8）', fontsize=14, fontweight='bold')

# 2. 配置关键词热力图（前5个配置）
ax2 = axes[1]
top5_configs = config_counts.head(5).index.tolist()
keyword_names = list(keyword_groups.keys())

# 构建数据矩阵
data_matrix = []
for config in top5_configs:
    row = [config_keywords[config].get(kw, 0) for kw in keyword_names]
    data_matrix.append(row)

data_matrix = np.array(data_matrix)

# 绘制热力图
im = ax2.imshow(data_matrix, cmap='YlOrRd', aspect='auto')

# 设置坐标轴
ax2.set_xticks(np.arange(len(keyword_names)))
ax2.set_yticks(np.arange(len(top5_configs)))
ax2.set_xticklabels(keyword_names, fontsize=10)
ax2.set_yticklabels(top5_configs, fontsize=10)

# 旋转x轴标签
plt.setp(ax2.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

# 添加数值标签
for i in range(len(top5_configs)):
    for j in range(len(keyword_names)):
        text = ax2.text(j, i, int(data_matrix[i, j]),
                       ha="center", va="center", color="black", fontsize=9)

ax2.set_title('各配置关键词提及次数热力图', fontsize=14, fontweight='bold')
fig.colorbar(im, ax=ax2, label='提及次数')

plt.tight_layout()
config_analysis_file = f'购买行为_配置分析_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
plt.savefig(config_analysis_file, dpi=300, bbox_inches='tight')
print(f"\n💾 配置分析图已保存: {config_analysis_file}")

# ============================================================================
# 四、购买决策洞察
# ============================================================================
print(f"\n{'='*80}")
print("【四、购买决策洞察】".center(80))
print(f"{'='*80}")

insights = []

# 1. 时间规律洞察
if late_month > mid_month * 1.2:
    insight = "💡 月末（20-31日）销量明显高于月中，推测与发薪日相关"
    print(f"\n{insight}")
    print(f"   建议: 在每月20-25日推出限时优惠、分期免息活动")
    insights.append(insight)
elif early_month > late_month * 1.2:
    insight = "💡 月初销量较高，可能与促销活动或预算周期相关"
    print(f"\n{insight}")
    insights.append(insight)

if weekend_total > weekday_total / 5 * 2 * 1.3:
    insight = "💡 周末销量显著高于工作日，用户有更多时间决策"
    print(f"\n{insight}")
    print(f"   建议: 周末加大直播带货力度，增加客服在线时间")
    insights.append(insight)
elif weekday_total > weekend_total * 2:
    insight = "💡 工作日销量高于周末，用户利用碎片时间购物"
    print(f"\n{insight}")
    print(f"   建议: 工作日推送精准营销信息")
    insights.append(insight)

# 2. 配置选择洞察
top_config = config_counts.index[0]
top_config_percent = config_percent.iloc[0]

if top_config_percent > 40:
    insight = f"💡 {top_config}配置占比{top_config_percent:.1f}%，是绝对主力"
    print(f"\n{insight}")
    print(f"   建议: 作为主推款，保证库存充足")
    insights.append(insight)

# 3. 性价比配置识别
for config in config_counts.head(3).index:
    if config in config_keywords:
        price_ratio = config_keywords[config].get('性价比', 0)
        if price_ratio > len(df_valid[df_valid['配置'] == config]) * 0.1:
            insight = f"💡 {config}被频繁提及'性价比'，是用户心中的性价比之选"
            print(f"\n{insight}")
            print(f"   建议: 营销时突出'性价比最优解'标签")
            insights.append(insight)
            break

# ============================================================================
# 五、生成分析报告
# ============================================================================
print(f"\n{'='*80}")
print("【五、生成分析报告】".center(80))
print(f"{'='*80}")

report_file = f'购买行为分析报告_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
with open(report_file, 'w', encoding='utf-8') as f:
    f.write("="*80 + "\n")
    f.write("vivo手机购买行为分析报告\n".center(80))
    f.write("="*80 + "\n\n")
    f.write(f"分析时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n")
    f.write(f"数据来源: {latest_file}\n")
    f.write(f"有效样本: {len(df_valid):,} 条\n\n")
    
    f.write("一、时间趋势分析\n")
    f.write("-" * 80 + "\n\n")
    
    f.write("1.1 月内时段分布\n")
    f.write(f"  月初 (1-5日):   {early_month}条 ({early_month/len(df_valid)*100:.1f}%)\n")
    f.write(f"  月中 (6-19日):  {mid_month}条 ({mid_month/len(df_valid)*100:.1f}%)\n")
    f.write(f"  月末 (20-31日): {late_month}条 ({late_month/len(df_valid)*100:.1f}%)\n\n")
    
    f.write("1.2 星期分布\n")
    f.write(f"  工作日: {weekday_total}条 ({weekday_total/len(df_valid)*100:.1f}%)\n")
    f.write(f"  周末:   {weekend_total}条 ({weekend_total/len(df_valid)*100:.1f}%)\n\n")
    
    f.write("1.3 季度分布\n")
    for quarter, count in quarter_counts.items():
        f.write(f"  Q{quarter:.0f}: {count}条 ({count/len(df_valid)*100:.1f}%)\n")
    f.write("\n")
    
    f.write("二、配置选择分析\n")
    f.write("-" * 80 + "\n\n")
    
    f.write("2.1 配置销量排名\n")
    for i, (config, count) in enumerate(config_counts.items(), 1):
        f.write(f"  {i}. {config}: {count}条 ({config_percent[config]:.1f}%)\n")
    f.write("\n")
    
    f.write("2.2 TOP 3配置关键词分析\n")
    for config in config_counts.head(3).index:
        f.write(f"\n  {config} ({config_counts[config]}条, {config_percent[config]:.1f}%):\n")
        if config in config_keywords:
            for kw_group, count in config_keywords[config].items():
                if count > 0:
                    f.write(f"    • {kw_group}: {count}次\n")
    
    f.write("\n三、购买决策洞察\n")
    f.write("-" * 80 + "\n")
    for i, insight in enumerate(insights, 1):
        f.write(f"\n{i}. {insight}\n")
    
    f.write("\n" + "="*80 + "\n")
    f.write("报告生成完毕\n")

print(f"\n✅ 分析完成！")
print(f"   - 时间趋势图: {time_trend_file}")
print(f"   - 配置分析图: {config_analysis_file}")
print(f"   - 分析报告: {report_file}")
print(f"\n{'='*80}")
