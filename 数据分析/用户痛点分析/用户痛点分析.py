import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime
import re
from collections import Counter
from wordcloud import WordCloud

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

print("="*80)
print("vivo手机用户痛点深度分析".center(80))
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
# 一、产品体验痛点分析（按产品模块分类）
# ============================================================================
print(f"\n{'='*80}")
print("【一、产品体验痛点分析】".center(80))
print(f"{'='*80}")

# 定义负面情感词（用于判断语境）
NEGATIVE_WORDS = [
    '差', '不好', '不行', '太差', '很差', '不佳', '失望', '后悔',
    '糟糕', '不满意', '难受', '坑', '坑爹', '垃圾', '烂',
    '不如', '还不如', '比不上', '不值', '缺点', '问题',
    '一般', '不推荐', '不建议', '慢', '小', '低', '弱'
]

# 定义产品模块的负面关键词短语（明确的负面表达）
PRODUCT_PAIN_POINTS = {
    '续航与充电': {
        '关键词': [
            '续航差', '续航不行', '续航短', '续航一般', '掉电快', '掉电', 
            '耗电快', '耗电', '费电', '充电慢', '电池不行', '电池差',
            '不耐用', '电量不足', '电池容量小', '待机短'
        ],
        '严重程度': 5,
        '描述': '电池续航时间短、充电速度慢、掉电快'
    },
    '性能与系统': {
        '关键词': [
            '卡顿', '卡', '很卡', '太卡', '反应慢', '运行慢', '慢',
            '发热', '烫', '烫手', '很烫', '太热', '温度高', '散热差',
            '死机', '闪退', '重启', '黑屏', '掉帧', '延迟', '卡机'
        ],
        '严重程度': 4,
        '描述': '系统运行不流畅、发热严重、性能不足'
    },
    '拍照与显示': {
        '关键词': [
            '拍照差', '拍照不行', '拍照一般', '拍照效果差',
            '模糊', '不清晰', '像素低', '夜拍差', '过曝', '噪点',
            '屏幕差', '屏幕不行', '漏光', '色差', '偏色', '偏黄', 
            '亮度低', '太暗', '刺眼', '显示不好'
        ],
        '严重程度': 3,
        '描述': '拍照效果差、屏幕显示问题'
    },
    '外观与手感': {
        '关键词': [
            '掉漆', '脱漆', '松动', '厚重', '太重', '重', '硌手',
            '做工差', '做工粗糙', '质量差', '质量不行', '质量问题',
            '划痕', '瑕疵', '缝隙大', '不平整'
        ],
        '严重程度': 3,
        '描述': '外观质量问题、手感不佳'
    },
    '信号与网络': {
        '关键词': [
            '信号差', '信号不好', '信号弱', '没信号',
            '断网', '掉线', '网络差', '网络不稳定',
            'WiFi差', 'wifi不行', '连不上'
        ],
        '严重程度': 4,
        '描述': '信号弱、网络连接不稳定'
    },
    '系统BUG': {
        '关键词': [
            'bug', 'BUG', '有bug', '系统bug',
            '广告多', '广告太多', '弹窗多', '弹窗',
            '更新失败', '更新问题', '卡bug'
        ],
        '严重程度': 3,
        '描述': '系统BUG、广告过多'
    },
}

# 定义需要检查负面语境的模糊词
AMBIGUOUS_KEYWORDS = ['卡', '慢', '重', '小', '低', '弱', '一般']

# 检查是否为真正的负面评论
def is_negative_context(content, keyword):
    """判断关键词是否出现在负面语境中"""
    # 如果关键词本身就是明确的负面短语，直接返回True
    if any(neg in keyword for neg in ['差', '不行', '不好', '太', '很', '问题']):
        return True
    
    # 如果是模糊词，检查附近是否有负面情感词
    if keyword in AMBIGUOUS_KEYWORDS:
        # 查找关键词位置
        keyword_pos = content.find(keyword)
        if keyword_pos == -1:
            return False
        
        # 检查前后20个字符范围内是否有负面词
        start = max(0, keyword_pos - 20)
        end = min(len(content), keyword_pos + 20)
        context = content[start:end]
        
        # 如果上下文中有负面词，则认为是真正的痛点
        has_negative = any(neg in context for neg in NEGATIVE_WORDS)
        
        # 排除明显的正面表达
        positive_phrases = ['不卡', '流畅', '很好', '不错', '满意', '喜欢', '推荐']
        has_positive = any(pos in context for pos in positive_phrases)
        
        return has_negative and not has_positive
    
    # 其他明确的负面关键词短语直接返回True
    return True

# 检测各模块痛点
print(f"\n▶ 产品模块痛点统计:")
print("-" * 80)
print(f"{'模块':<12} {'负面提及':<10} {'占比':<10} {'严重度':<10} {'典型问题':<30}")
print("-" * 80)

product_pain_stats = {}
for module, info in PRODUCT_PAIN_POINTS.items():
    # 统计提及次数
    count = 0
    all_reviews = []  # 保存所有负面评论
    
    for idx, row in df.iterrows():
        content = str(row.get('评论内容', ''))
        if pd.isna(content) or content == 'nan':
            continue
        
        for keyword in info['关键词']:
            if keyword in content:
                # 检查是否为真正的负面评论
                if is_negative_context(content, keyword):
                    count += 1
                    all_reviews.append({
                        'content': content,
                        'keyword': keyword,
                        'config': row.get('购买记录', ''),
                        'username': row.get('用户名', '未知')
                    })
                    break
    
    percent = count / total_reviews * 100
    severity = info['严重程度']
    
    # 评估优先级
    priority_score = count * severity
    
    product_pain_stats[module] = {
        'count': count,
        'percent': percent,
        'severity': severity,
        'priority': priority_score,
        'reviews': all_reviews,  # 保存所有评论
        'description': info['描述']
    }
    
    severity_label = "⚠️" * severity
    print(f"{module:<12} {count:<10} {percent:>5.1f}%    {severity_label:<10} {info['描述'][:30]}")

# 按优先级排序
sorted_product_pains = sorted(product_pain_stats.items(), 
                              key=lambda x: x[1]['priority'], reverse=True)

print(f"\n▶ 痛点优先级排序（按影响范围×严重程度）:")
print("-" * 80)
for i, (module, stats) in enumerate(sorted_product_pains, 1):
    priority_score = stats['priority']
    print(f"{i}. {module} - 优先级得分: {priority_score:.0f} "
          f"(提及{stats['count']}次 × 严重度{stats['severity']})")
    
    # 显示前3条样本
    if stats['reviews'] and i <= 3:
        print(f"   典型样本:")
        for j, review in enumerate(stats['reviews'][:3], 1):
            print(f"     {j}) [{review['keyword']}] {review['content'][:70]}...")

# ============================================================================
# 二、购买决策痛点分析
# ============================================================================
print(f"\n{'='*80}")
print("【二、购买决策痛点分析】".center(80))
print(f"{'='*80}")

# 2.1 配置选择困难
print(f"\n▶ 痛点1：配置选择困难")
print("-" * 80)

config_confusion_keywords = ['纠结', '不知道', '选哪个', '该买', '差别', '区别']
config_confusion_count = 0
config_confusion_samples = []

for idx, row in df.iterrows():
    content = str(row.get('评论内容', ''))
    if pd.isna(content):
        continue
    
    for keyword in config_confusion_keywords:
        if keyword in content:
            config_confusion_count += 1
            if len(config_confusion_samples) < 3:
                config_confusion_samples.append(content)
            break

print(f"  提及配置选择困难: {config_confusion_count}条 ({config_confusion_count/total_reviews*100:.1f}%)")
if config_confusion_samples:
    print(f"  典型评论:")
    for i, sample in enumerate(config_confusion_samples, 1):
        print(f"    {i}. {sample[:80]}...")

# 2.2 价格感知失衡
print(f"\n▶ 痛点2：价格感知失衡")
print("-" * 80)

price_pain_keywords = {
    '负面': ['贵', '亏', '降价', '不值', '价格高', '太贵'],
    '正面': ['便宜', '实惠', '划算', '值', '超值', '性价比']
}

price_negative_count = 0
price_positive_count = 0
price_negative_samples = []

for idx, row in df.iterrows():
    content = str(row.get('评论内容', ''))
    if pd.isna(content):
        continue
    
    for keyword in price_pain_keywords['负面']:
        if keyword in content:
            price_negative_count += 1
            if len(price_negative_samples) < 3:
                price_negative_samples.append(content)
            break
    
    for keyword in price_pain_keywords['正面']:
        if keyword in content:
            price_positive_count += 1
            break

print(f"  价格负面评价: {price_negative_count}条 ({price_negative_count/total_reviews*100:.1f}%)")
print(f"  价格正面评价: {price_positive_count}条 ({price_positive_count/total_reviews*100:.1f}%)")
print(f"  正负比: {price_positive_count}:{price_negative_count}")

if price_negative_count > price_positive_count * 0.3:
    print(f"  ⚠️ 价格感知存在问题，负面评价占比较高")
else:
    print(f"  ✓ 价格认可度较好")

# 2.3 颜色信息不符
print(f"\n▶ 痛点3：颜色/外观与预期不符")
print("-" * 80)

# 提取颜色
def extract_color(text):
    if pd.isna(text):
        return None
    text = str(text)
    colors = ['曜夜黑', '星光白', '远航蓝', '幻夜黑', '星空蓝', '流光紫', 
              '黑色', '白色', '蓝色', '紫色', '绿色']
    for color in colors:
        if color in text:
            return color
    return None

df['颜色'] = df['购买记录'].apply(extract_color)

color_mismatch_keywords = ['不一样', '色差', '偏黄', '偏色', '和图片', '和照片', '和宣传']
color_mismatch_stats = {}

for color in df['颜色'].dropna().unique():
    color_df = df[df['颜色'] == color]
    mismatch_count = 0
    samples = []
    
    for idx, row in color_df.iterrows():
        content = str(row.get('评论内容', ''))
        if pd.isna(content):
            continue
        
        for keyword in color_mismatch_keywords:
            if keyword in content:
                mismatch_count += 1
                if len(samples) < 2:
                    samples.append(content)
                break
    
    if mismatch_count > 0:
        color_mismatch_stats[color] = {
            'count': mismatch_count,
            'percent': mismatch_count / len(color_df) * 100,
            'samples': samples
        }

if color_mismatch_stats:
    sorted_color_issues = sorted(color_mismatch_stats.items(), 
                                 key=lambda x: x[1]['count'], reverse=True)
    for color, stats in sorted_color_issues:
        print(f"  {color}: {stats['count']}条反馈色差问题 ({stats['percent']:.1f}%)")
else:
    print(f"  ✓ 未发现明显的颜色信息不符问题")

# ============================================================================
# 三、使用场景痛点分析（按人群细分）
# ============================================================================
print(f"\n{'='*80}")
print("【三、使用场景痛点分析（按人群）】".center(80))
print(f"{'='*80}")

# 定义人群标签和对应痛点
USER_GROUPS = {
    '学生党': {
        '识别关键词': ['学生', '上课', '宿舍', '同学', '课'],
        '核心痛点': ['游戏发热', '续航差', '价格高']
    },
    '职场人': {
        '识别关键词': ['上班', '工作', '公司', '通勤', '办公'],
        '核心痛点': ['多开卡顿', '充电慢', '重量重']
    },
    '长辈用户': {
        '识别关键词': ['爸妈', '父母', '妈妈', '爸爸', '老人', '长辈'],
        '核心痛点': ['操作复杂', '字体小', '声音小']
    },
    '游戏玩家': {
        '识别关键词': ['游戏', '吃鸡', '王者', '打游戏', '开黑'],
        '核心痛点': ['发热', '掉帧', '卡顿']
    },
    '摄影爱好者': {
        '识别关键词': ['拍照', '摄影', '相机', '拍风景', '拍人'],
        '核心痛点': ['拍照差', '存储不够', '色彩失真']
    },
}

print(f"\n▶ 不同人群的痛点分布:")
print("-" * 80)

user_group_pain_stats = {}

for group, info in USER_GROUPS.items():
    # 识别该人群的评论
    group_reviews = []
    for idx, row in df.iterrows():
        content = str(row.get('评论内容', ''))
        if pd.isna(content):
            continue
        
        for keyword in info['识别关键词']:
            if keyword in content:
                group_reviews.append({
                    'content': content,
                    'config': row.get('购买记录', '')
                })
                break
    
    if len(group_reviews) == 0:
        continue
    
    # 统计该人群的痛点
    group_pains = Counter()
    for review in group_reviews:
        content = review['content']
        for module, module_info in PRODUCT_PAIN_POINTS.items():
            for keyword in module_info['关键词']:
                if keyword in content:
                    group_pains[module] += 1
                    break
    
    user_group_pain_stats[group] = {
        'count': len(group_reviews),
        'percent': len(group_reviews) / total_reviews * 100,
        'pains': group_pains,
        'reviews': group_reviews  # 保存所有评论
    }
    
    print(f"\n【{group}】(识别到{len(group_reviews)}条评论, 占{len(group_reviews)/total_reviews*100:.1f}%)")
    
    if group_pains:
        top_pains = group_pains.most_common(3)
        print(f"  核心痛点:")
        for i, (pain, count) in enumerate(top_pains, 1):
            print(f"    {i}. {pain}: {count}次提及")
    
    if user_group_pain_stats[group]['reviews']:
        print(f"  典型评论（前2条）:")
        for i, sample in enumerate(user_group_pain_stats[group]['reviews'][:2], 1):
            print(f"    {i}. {sample['content'][:70]}...")

# ============================================================================
# 四、配置关联痛点分析（归因分析）
# ============================================================================
print(f"\n{'='*80}")
print("【四、配置关联痛点分析（归因分析）】".center(80))
print(f"{'='*80}")

# 提取配置信息
def extract_memory_config(text):
    if pd.isna(text):
        return None
    text = str(text)
    match = re.search(r'(\d+)GB[\+\s]*(\d+)GB', text)
    if match:
        ram = int(match.group(1))
        storage = int(match.group(2))
        return f"{ram}GB+{storage}GB"
    return None

df['配置'] = df['购买记录'].apply(extract_memory_config)

print(f"\n▶ 不同配置的痛点差异:")
print("-" * 80)

config_pain_comparison = {}
config_counts = df['配置'].value_counts()

for config in config_counts.head(3).index:
    config_df = df[df['配置'] == config]
    config_total = len(config_df)
    
    # 统计该配置的痛点分布
    config_pains = Counter()
    for idx, row in config_df.iterrows():
        content = str(row.get('评论内容', ''))
        if pd.isna(content):
            continue
        
        for module, module_info in PRODUCT_PAIN_POINTS.items():
            for keyword in module_info['关键词']:
                if keyword in content:
                    config_pains[module] += 1
                    break
    
    config_pain_comparison[config] = config_pains
    
    print(f"\n【{config}】(共{config_total}条评论)")
    if config_pains:
        top_pains = config_pains.most_common(5)
        for i, (pain, count) in enumerate(top_pains, 1):
            percent = count / config_total * 100
            print(f"  {i}. {pain}: {count}次 ({percent:.1f}%)")

# 归因分析示例
print(f"\n▶ 痛点归因洞察:")
print("-" * 80)

# 分析高配置vs低配置的痛点差异
if len(config_pain_comparison) >= 2:
    configs = list(config_pain_comparison.keys())[:2]
    config1, config2 = configs[0], configs[1]
    
    # 提取RAM大小用于比较
    ram1 = int(re.search(r'(\d+)GB', config1).group(1))
    ram2 = int(re.search(r'(\d+)GB', config2).group(1))
    
    high_config = config1 if ram1 > ram2 else config2
    low_config = config2 if ram1 > ram2 else config1
    
    high_pains = config_pain_comparison[high_config]
    low_pains = config_pain_comparison[low_config]
    
    # 分析发热问题
    high_heat = high_pains.get('性能与系统', 0) / len(df[df['配置'] == high_config]) * 100
    low_heat = low_pains.get('性能与系统', 0) / len(df[df['配置'] == low_config]) * 100
    
    if high_heat > low_heat * 1.5:
        print(f"💡 发现：{high_config}配置的发热问题({high_heat:.1f}%)明显高于{low_config}({low_heat:.1f}%)")
        print(f"   归因：高性能配置功耗控制不足，建议优化电源管理策略")

# ============================================================================
# 五、生成可视化图表
# ============================================================================
print(f"\n{'='*80}")
print("【五、生成可视化图表】".center(80))
print(f"{'='*80}")

fig = plt.figure(figsize=(16, 12))

# 1. 产品模块痛点分布
ax1 = plt.subplot(2, 3, 1)
modules = [item[0] for item in sorted_product_pains]
counts = [item[1]['count'] for item in sorted_product_pains]
colors_pain = ['#e74c3c' if item[1]['priority'] > 200 else '#f39c12' if item[1]['priority'] > 100 else '#95a5a6' 
               for item in sorted_product_pains]

bars = ax1.barh(range(len(modules)), counts, color=colors_pain, alpha=0.8, edgecolor='black')
ax1.set_yticks(range(len(modules)))
ax1.set_yticklabels(modules, fontsize=10)
ax1.set_xlabel('提及次数', fontsize=11, fontweight='bold')
ax1.set_title('产品模块痛点分布', fontsize=13, fontweight='bold')
ax1.invert_yaxis()

for i, (bar, count) in enumerate(zip(bars, counts)):
    ax1.text(count, i, f' {count}', va='center', fontsize=9)

# 2. 痛点优先级矩阵
ax2 = plt.subplot(2, 3, 2)
x_data = [item[1]['percent'] for item in sorted_product_pains]
y_data = [item[1]['severity'] for item in sorted_product_pains]
sizes = [item[1]['count'] * 2 for item in sorted_product_pains]
labels = [item[0] for item in sorted_product_pains]

scatter = ax2.scatter(x_data, y_data, s=sizes, alpha=0.6, c=range(len(x_data)), 
                     cmap='RdYlGn_r', edgecolors='black', linewidth=1.5)

for i, label in enumerate(labels):
    ax2.annotate(label, (x_data[i], y_data[i]), fontsize=8, 
                ha='center', va='center')

ax2.set_xlabel('负面提及占比 (%)', fontsize=11, fontweight='bold')
ax2.set_ylabel('严重程度', fontsize=11, fontweight='bold')
ax2.set_title('痛点优先级矩阵\n(气泡大小=提及次数)', fontsize=13, fontweight='bold')
ax2.grid(True, alpha=0.3, linestyle='--')

# 3. 价格感知对比
ax3 = plt.subplot(2, 3, 3)
price_data = [price_positive_count, price_negative_count]
price_labels = ['正面评价', '负面评价']
price_colors = ['#2ecc71', '#e74c3c']

wedges, texts, autotexts = ax3.pie(price_data, labels=price_labels, autopct='%1.1f%%',
                                    colors=price_colors, startangle=90,
                                    textprops={'fontsize': 11, 'fontweight': 'bold'})
ax3.set_title('价格感知分析', fontsize=13, fontweight='bold')

# 4. 人群痛点热力图
ax4 = plt.subplot(2, 3, 4)

if user_group_pain_stats:
    groups = list(user_group_pain_stats.keys())
    all_pain_modules = list(PRODUCT_PAIN_POINTS.keys())
    
    # 构建热力图数据
    heatmap_data = []
    for group in groups:
        row = []
        group_total = user_group_pain_stats[group]['count']
        for module in all_pain_modules:
            count = user_group_pain_stats[group]['pains'].get(module, 0)
            percent = (count / group_total * 100) if group_total > 0 else 0
            row.append(percent)
        heatmap_data.append(row)
    
    heatmap_data = np.array(heatmap_data)
    
    im = ax4.imshow(heatmap_data, cmap='YlOrRd', aspect='auto')
    ax4.set_xticks(np.arange(len(all_pain_modules)))
    ax4.set_yticks(np.arange(len(groups)))
    ax4.set_xticklabels(all_pain_modules, rotation=45, ha='right', fontsize=9)
    ax4.set_yticklabels(groups, fontsize=10)
    
    # 添加数值
    for i in range(len(groups)):
        for j in range(len(all_pain_modules)):
            if heatmap_data[i, j] > 0:
                text = ax4.text(j, i, f'{heatmap_data[i, j]:.0f}%',
                               ha="center", va="center", color="black", fontsize=8)
    
    ax4.set_title('不同人群痛点分布热力图', fontsize=13, fontweight='bold')
    plt.colorbar(im, ax=ax4, label='提及占比(%)')

# 5. 配置关联痛点对比
ax5 = plt.subplot(2, 3, 5)

if len(config_pain_comparison) >= 2:
    configs_to_compare = list(config_pain_comparison.keys())[:3]
    pain_modules = list(set().union(*[set(config_pain_comparison[c].keys()) for c in configs_to_compare]))
    
    x = np.arange(len(pain_modules))
    width = 0.25
    
    for i, config in enumerate(configs_to_compare):
        counts = [config_pain_comparison[config].get(module, 0) for module in pain_modules]
        ax5.bar(x + i * width, counts, width, label=config, alpha=0.8, edgecolor='black')
    
    ax5.set_xlabel('痛点模块', fontsize=11, fontweight='bold')
    ax5.set_ylabel('提及次数', fontsize=11, fontweight='bold')
    ax5.set_title('不同配置痛点对比', fontsize=13, fontweight='bold')
    ax5.set_xticks(x + width)
    ax5.set_xticklabels(pain_modules, rotation=45, ha='right', fontsize=9)
    ax5.legend(fontsize=9)
    ax5.grid(True, alpha=0.3, axis='y', linestyle='--')

# 6. 痛点词云
ax6 = plt.subplot(2, 3, 6)

all_pain_keywords = []
for module_info in PRODUCT_PAIN_POINTS.values():
    all_pain_keywords.extend(module_info['关键词'])

pain_keyword_freq = {}
for keyword in all_pain_keywords:
    count = df['评论内容'].astype(str).str.contains(keyword, na=False).sum()
    if count > 0:
        pain_keyword_freq[keyword] = count

if pain_keyword_freq:
    wordcloud = WordCloud(
        width=500,
        height=400,
        background_color='white',
        font_path='C:/Windows/Fonts/simhei.ttf',
        max_words=40,
        colormap='Reds',
        relative_scaling=0.5
    ).generate_from_frequencies(pain_keyword_freq)
    
    ax6.imshow(wordcloud, interpolation='bilinear')
    ax6.axis('off')
    ax6.set_title('痛点关键词词云', fontsize=13, fontweight='bold')

plt.tight_layout()
pain_chart_file = f'用户痛点深度分析_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
plt.savefig(pain_chart_file, dpi=300, bbox_inches='tight')
print(f"\n💾 痛点分析图已保存: {pain_chart_file}")

# ============================================================================
# 六、生成改进建议
# ============================================================================
print(f"\n{'='*80}")
print("【六、改进建议】".center(80))
print(f"{'='*80}")

recommendations = []

# 针对TOP 3产品痛点
print(f"\n▶ 产品体验改进建议:")
for i, (module, stats) in enumerate(sorted_product_pains[:3], 1):
    count = stats['count']
    percent = stats['percent']
    
    print(f"\n{i}. 针对【{module}】({count}次, {percent:.1f}%)")
    
    if '续航' in module:
        suggestion = "优化电池管理算法，增加省电模式；考虑提升电池容量"
        action = "软件团队优化后台耗电，硬件团队评估电池升级方案"
    elif '性能' in module:
        suggestion = "优化系统性能，改进散热设计，减少后台进程"
        action = "系统团队进行性能调优，硬件团队改进散热方案"
    elif '拍照' in module:
        suggestion = "升级相机算法，特别是夜拍和HDR场景"
        action = "相机团队优化算法，增加专业模式"
    elif '外观' in module:
        suggestion = "提高生产质检标准，改进涂层工艺"
        action = "供应链加强质检，优化表面处理工艺"
    elif '信号' in module:
        suggestion = "优化信号算法，改进天线设计"
        action = "硬件团队优化天线布局，软件优化网络切换逻辑"
    else:
        suggestion = "持续关注用户反馈，及时优化改进"
        action = "建立用户反馈跟踪机制"
    
    print(f"   💡 建议: {suggestion}")
    print(f"   🎯 行动: {action}")
    
    recommendations.append({
        'category': module,
        'type': '产品体验',
        'count': count,
        'percent': percent,
        'suggestion': suggestion,
        'action': action
    })

# 针对购买决策痛点
print(f"\n▶ 购买决策改进建议:")

if config_confusion_count > total_reviews * 0.05:
    print(f"\n• 配置选择困难 ({config_confusion_count}条, {config_confusion_count/total_reviews*100:.1f}%)")
    print(f"   💡 建议: 在商品页增加'配置选购指南'，明确标注各配置适用人群")
    print(f"   🎯 行动: 产品页面增加'日常使用选6+128G，游戏玩家选12+256G'等推荐语")
    
    recommendations.append({
        'category': '配置选择',
        'type': '购买决策',
        'count': config_confusion_count,
        'percent': config_confusion_count/total_reviews*100,
        'suggestion': '增加配置选购指南，降低用户决策成本',
        'action': '商品详情页增加配置推荐和对比说明'
    })

if price_negative_count > price_positive_count * 0.3:
    print(f"\n• 价格感知失衡 ({price_negative_count}条负面)")
    print(f"   💡 建议: 实施价格保护政策，突出产品差异化优势")
    print(f"   🎯 行动: 推出7天保价服务，商品页强调独特卖点")
    
    recommendations.append({
        'category': '价格感知',
        'type': '购买决策',
        'count': price_negative_count,
        'percent': price_negative_count/total_reviews*100,
        'suggestion': '实施价格保护，突出差异化价值',
        'action': '推出保价服务，优化商品页卖点展示'
    })

# ============================================================================
# 七、生成分析报告
# ============================================================================
print(f"\n{'='*80}")
print("【七、生成分析报告】".center(80))
print(f"{'='*80}")

report_file = f'用户痛点深度分析报告_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
with open(report_file, 'w', encoding='utf-8') as f:
    f.write("="*80 + "\n")
    f.write("vivo手机用户痛点深度分析报告\n".center(80))
    f.write("="*80 + "\n\n")
    f.write(f"分析时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n")
    f.write(f"数据来源: {latest_file}\n")
    f.write(f"样本总数: {total_reviews:,} 条评论\n\n")
    
    f.write("一、产品体验痛点（按优先级排序）\n")
    f.write("-" * 80 + "\n\n")
    
    for i, (module, stats) in enumerate(sorted_product_pains, 1):
        f.write(f"{i}. {module}\n")
        f.write(f"   提及次数: {stats['count']}次 ({stats['percent']:.1f}%)\n")
        f.write(f"   严重程度: {'⚠️' * stats['severity']}\n")
        f.write(f"   优先级得分: {stats['priority']:.0f}\n")
        f.write(f"   问题描述: {stats['description']}\n")
        f.write("\n")
        
        if stats['reviews']:
            f.write(f"   所有负面评论明细:\n")
            f.write("   " + "-" * 76 + "\n")
            for j, review in enumerate(stats['reviews'], 1):
                f.write(f"   [{j}] 用户: {review['username']}\n")
                f.write(f"       配置: {review['config'][:60]}\n")
                f.write(f"       关键词: 【{review['keyword']}】\n")
                f.write(f"       评论: {review['content']}\n")
                f.write("   " + "-" * 76 + "\n")
        f.write("\n")
    
    f.write("二、购买决策痛点\n")
    f.write("-" * 80 + "\n\n")
    
    f.write(f"1. 配置选择困难: {config_confusion_count}条 ({config_confusion_count/total_reviews*100:.1f}%)\n")
    f.write(f"2. 价格负面评价: {price_negative_count}条 ({price_negative_count/total_reviews*100:.1f}%)\n")
    f.write(f"   价格正面评价: {price_positive_count}条 ({price_positive_count/total_reviews*100:.1f}%)\n\n")
    
    f.write("三、使用场景痛点（按人群）\n")
    f.write("-" * 80 + "\n\n")
    
    for group, stats in user_group_pain_stats.items():
        f.write(f"【{group}】({stats['count']}条评论, {stats['percent']:.1f}%)\n")
        if stats['pains']:
            top_pains = stats['pains'].most_common(3)
            f.write(f"  核心痛点: ")
            f.write('、'.join([f"{p[0]}({p[1]}次)" for p in top_pains]))
            f.write("\n\n")
        
        # 添加该人群的所有评论
        if stats['reviews']:
            f.write(f"  该人群所有评论明细:\n")
            f.write("  " + "-" * 76 + "\n")
            for j, review in enumerate(stats['reviews'], 1):
                f.write(f"  [{j}] 配置: {review['config'][:60]}\n")
                f.write(f"      评论: {review['content']}\n")
                f.write("  " + "-" * 76 + "\n")
            f.write("\n")
    
    f.write("四、配置关联痛点分析\n")
    f.write("-" * 80 + "\n\n")
    
    for config, pains in list(config_pain_comparison.items())[:3]:
        config_total = len(df[df['配置'] == config])
        f.write(f"{config} (共{config_total}条评论):\n")
        top_pains = pains.most_common(5)
        for i, (pain, count) in enumerate(top_pains, 1):
            f.write(f"  {i}. {pain}: {count}次 ({count/config_total*100:.1f}%)\n")
        f.write("\n")
    
    f.write("五、改进建议汇总\n")
    f.write("-" * 80 + "\n\n")
    
    for i, rec in enumerate(recommendations, 1):
        f.write(f"{i}. 【{rec['category']}】({rec['type']})\n")
        f.write(f"   影响范围: {rec['count']}条评论 ({rec['percent']:.1f}%)\n")
        f.write(f"   改进建议: {rec['suggestion']}\n")
        f.write(f"   行动计划: {rec['action']}\n\n")
    
    f.write("="*80 + "\n")
    f.write("报告生成完毕\n")

print(f"\n✅ 分析完成！")
print(f"   - 痛点分析图: {pain_chart_file}")
print(f"   - 分析报告: {report_file}")
print(f"\n{'='*80}") 