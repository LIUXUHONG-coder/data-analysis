import pandas as pd
import jieba
import jieba.analyse
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime
from collections import Counter
import re

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

print("="*80)
print("vivo手机评论词云分析".center(80))
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
# 一、数据预处理
# ============================================================================
print(f"\n{'='*80}")
print("【一、数据预处理与分词】".center(80))
print(f"{'='*80}")

# 合并所有评论文本
all_comments = df['评论内容'].dropna().astype(str).tolist()
text_combined = ' '.join(all_comments)

print(f"\n▶ 文本统计:")
print(f"  总字符数: {len(text_combined):,}")
print(f"  平均评论长度: {len(text_combined)/len(all_comments):.1f} 字")

# 加载停用词列表
print(f"\n▶ 加载停用词表...")
stopwords = set()
stopwords_file = 'stopwords.txt'

if os.path.exists(stopwords_file):
    with open(stopwords_file, 'r', encoding='utf-8') as f:
        for line in f:
            word = line.strip()
            if word:
                stopwords.add(word)
    print(f"  已加载 {len(stopwords)} 个停用词")
else:
    print(f"  ⚠️ 未找到 {stopwords_file}，使用默认停用词")
    # 使用基本停用词
    stopwords = set(['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都'])

# 添加自定义停用词（针对手机评论）
custom_stopwords = set([
    'vivo', 'VIVO', 'Vivo', 'v', 'V', 'x', 'X',
    '手机', '非常', '挺', '比较', '感觉', '觉得', '真的', '确实', '还是',
    '东西', '东东', '宝贝', '收到', '评价',
    '蛮', '一下', '一点', '有点', '这种', '那种',
    '哈哈', '嗯', '嗯嗯', '哈', '呵呵', '啦', '哟', '呀', '哇', '嘿',
])
stopwords.update(custom_stopwords)
print(f"  添加自定义停用词 {len(custom_stopwords)} 个")
print(f"  停用词总数: {len(stopwords)}")

# 自定义词典（添加专业词汇）
custom_words = [
    '性价比', '续航', '拍照', '像素', '电池', '充电', '快充', '运行', '流畅',
    '外观', '颜值', '屏幕', '音质', '音效', '散热', '发热', '信号', '指纹',
    '人脸识别', '解锁', '系统', '处理器', '内存', '存储', '卡顿', '死机',
    '物流', '快递', '包装', '客服', '售后', '活动', '优惠', '划算', '超值'
]

for word in custom_words:
    jieba.add_word(word)

print(f"\n▶ 分词处理中...")
# 分词
words = jieba.lcut(text_combined)

# 过滤
filtered_words = []
for word in words:
    # 过滤条件
    if (len(word) >= 2 and  # 至少2个字符
        word not in stopwords and  # 不在停用词中
        not word.isdigit() and  # 不是纯数字
        not re.match(r'^[a-zA-Z]+$', word) and  # 不是纯英文
        not re.match(r'^[\W_]+$', word)):  # 不是纯符号
        filtered_words.append(word)

print(f"  原始词数: {len(words):,}")
print(f"  过滤后词数: {len(filtered_words):,}")
print(f"  去除率: {(1 - len(filtered_words)/len(words))*100:.1f}%")

# ============================================================================
# 二、词频统计
# ============================================================================
print(f"\n{'='*80}")
print("【二、词频统计】".center(80))
print(f"{'='*80}")

# 统计词频
word_counts = Counter(filtered_words)
top_words = word_counts.most_common(50)

print(f"\n▶ TOP 30 高频词汇:")
print("-" * 80)
print(f"{'排名':<6} {'词汇':<15} {'频次':<10} {'占比':<10} {'频次图':<20}")
print("-" * 80)

total_filtered_words = len(filtered_words)
for i, (word, count) in enumerate(top_words[:30], 1):
    percent = count / total_filtered_words * 100
    bar = "█" * int(count / top_words[0][1] * 20)
    print(f"{i:<6} {word:<15} {count:<10} {percent:>5.2f}%     {bar}")

# ============================================================================
# 三、生成词云图
# ============================================================================
print(f"\n{'='*80}")
print("【三、生成词云图】".center(80))
print(f"{'='*80}")

print(f"\n▶ 正在生成词云图...")

# 创建词频字典
word_freq = dict(word_counts)

# 生成词云（使用默认字体）
wordcloud = WordCloud(
    width=1600,
    height=800,
    background_color='white',
    font_path='C:/Windows/Fonts/simhei.ttf',  # 黑体
    max_words=200,
    relative_scaling=0.5,
    colormap='viridis',
    min_font_size=10,
    random_state=42
).generate_from_frequencies(word_freq)

# 绘制词云图
fig, axes = plt.subplots(1, 2, figsize=(16, 8))

# 左图：词云
ax1 = axes[0]
ax1.imshow(wordcloud, interpolation='bilinear')
ax1.axis('off')
ax1.set_title('评论词云图', fontsize=18, fontweight='bold', pad=20)

# 右图：TOP20词频柱状图
ax2 = axes[1]
top20_words = [w[0] for w in top_words[:20]]
top20_counts = [w[1] for w in top_words[:20]]
colors = plt.cm.viridis(np.linspace(0.3, 0.9, 20))

bars = ax2.barh(range(20), top20_counts, color=colors)
ax2.set_yticks(range(20))
ax2.set_yticklabels(top20_words, fontsize=11)
ax2.set_xlabel('出现次数', fontsize=12)
ax2.set_title('TOP20 高频词汇', fontsize=16, fontweight='bold', pad=15)
ax2.invert_yaxis()

# 添加数值标签
for i, (bar, count) in enumerate(zip(bars, top20_counts)):
    ax2.text(count, i, f' {count}', va='center', fontsize=10)

plt.tight_layout()
wordcloud_file = f'词云图分析_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
plt.savefig(wordcloud_file, dpi=300, bbox_inches='tight')
print(f"✅ 词云图已保存: {wordcloud_file}")

# ============================================================================
# 四、关键词分类分析
# ============================================================================
print(f"\n{'='*80}")
print("【四、关键词分类分析】".center(80))
print(f"{'='*80}")

# 定义关键词分类
keyword_categories = {
    '性能体验': ['流畅', '运行', '卡顿', '速度', '快', '慢', '处理器', '芯片', '性能', '配置'],
    '外观设计': ['外观', '颜值', '好看', '漂亮', '美', '颜色', '手感', '质感', '轻薄', '大气'],
    '拍照功能': ['拍照', '相机', '摄像', '照片', '像素', '清晰', '夜景', '美颜', '镜头'],
    '续航充电': ['续航', '电池', '充电', '快充', '耐用', '电量', '掉电', '耗电'],
    '屏幕显示': ['屏幕', '显示', '画质', '色彩', '亮度', '护眼', '分辨率'],
    '系统软件': ['系统', '软件', '更新', '应用', '界面', '操作', '功能'],
    '服务物流': ['物流', '快递', '包装', '客服', '售后', '服务', '发货', '配送'],
    '性价比': ['性价比', '划算', '值得', '超值', '实惠', '便宜', '价格', '优惠'],
}

print(f"\n▶ 各维度关键词统计:")
print("-" * 80)

category_stats = {}
for category, keywords in keyword_categories.items():
    count = sum(word_counts.get(kw, 0) for kw in keywords)
    category_stats[category] = count
    
    # 显示该类别的高频词
    category_words = [(kw, word_counts.get(kw, 0)) for kw in keywords if word_counts.get(kw, 0) > 0]
    category_words.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n【{category}】 总计: {count} 次")
    if category_words:
        top_5 = category_words[:5]
        top_words_str = '、'.join([f"{w}({c}次)" for w, c in top_5])
        print(f"  高频词: {top_words_str}")

# 绘制分类统计图
plt.figure(figsize=(12, 6))
categories = list(category_stats.keys())
counts = list(category_stats.values())
colors_cat = plt.cm.Set3(np.linspace(0, 1, len(categories)))

bars = plt.bar(categories, counts, color=colors_cat, edgecolor='black', linewidth=1.5)
plt.xlabel('关注维度', fontsize=12, fontweight='bold')
plt.ylabel('提及次数', fontsize=12, fontweight='bold')
plt.title('用户关注维度分析', fontsize=16, fontweight='bold', pad=15)
plt.xticks(rotation=45, ha='right')

# 添加数值标签
for bar, count in zip(bars, counts):
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height,
             f'{int(count)}',
             ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.tight_layout()
category_file = f'关键词分类统计_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
plt.savefig(category_file, dpi=300, bbox_inches='tight')
print(f"\n💾 分类统计图已保存: {category_file}")

# ============================================================================
# 五、生成分析报告
# ============================================================================
print(f"\n{'='*80}")
print("【五、生成分析报告】".center(80))
print(f"{'='*80}")

report_file = f'词云分析报告_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
with open(report_file, 'w', encoding='utf-8') as f:
    f.write("="*80 + "\n")
    f.write("vivo手机评论词云分析报告\n".center(80))
    f.write("="*80 + "\n\n")
    f.write(f"分析时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n")
    f.write(f"数据来源: {latest_file}\n")
    f.write(f"样本数量: {total_reviews:,} 条评论\n\n")
    
    f.write("一、文本分析概况\n")
    f.write("-" * 80 + "\n")
    f.write(f"总字符数: {len(text_combined):,}\n")
    f.write(f"平均评论长度: {len(text_combined)/len(all_comments):.1f} 字\n")
    f.write(f"分词总数: {len(words):,}\n")
    f.write(f"有效词汇数: {len(filtered_words):,}\n")
    f.write(f"去重后词汇数: {len(word_counts):,}\n\n")
    
    f.write("二、TOP 50 高频词汇\n")
    f.write("-" * 80 + "\n")
    f.write(f"{'排名':<6} {'词汇':<15} {'频次':<10} {'占比':<10}\n")
    f.write("-" * 80 + "\n")
    for i, (word, count) in enumerate(top_words, 1):
        percent = count / total_filtered_words * 100
        f.write(f"{i:<6} {word:<15} {count:<10} {percent:>5.2f}%\n")
    
    f.write("\n三、用户关注维度分析\n")
    f.write("-" * 80 + "\n")
    sorted_categories = sorted(category_stats.items(), key=lambda x: x[1], reverse=True)
    for i, (category, count) in enumerate(sorted_categories, 1):
        percent = count / sum(category_stats.values()) * 100
        f.write(f"\n{i}. {category} ({count}次, 占{percent:.1f}%)\n")
        
        # 显示该类别的高频词
        keywords = keyword_categories[category]
        category_words = [(kw, word_counts.get(kw, 0)) for kw in keywords if word_counts.get(kw, 0) > 0]
        category_words.sort(key=lambda x: x[1], reverse=True)
        if category_words:
            f.write("   关键词: ")
            f.write('、'.join([f"{w}({c})" for w, c in category_words[:10]]))
            f.write("\n")
    
    f.write("\n四、关键发现\n")
    f.write("-" * 80 + "\n")
    
    # 自动生成洞察
    top_category = sorted_categories[0][0]
    top_category_percent = sorted_categories[0][1] / sum(category_stats.values()) * 100
    f.write(f"1. 用户最关注【{top_category}】维度，提及次数占{top_category_percent:.1f}%\n")
    
    # 分析高频词
    if '流畅' in [w[0] for w in top_words[:20]]:
        f.write(f"2. '流畅'一词高频出现，说明用户对系统流畅度非常关注\n")
    
    if '外观' in [w[0] for w in top_words[:20]] or '颜值' in [w[0] for w in top_words[:20]]:
        f.write(f"3. 外观颜值是用户重点评价对象，建议加强外观设计宣传\n")
    
    if category_stats.get('续航充电', 0) > category_stats.get('拍照功能', 0):
        f.write(f"4. 用户对续航的关注度超过拍照功能\n")
    
    f.write("\n" + "="*80 + "\n")
    f.write("报告生成完毕\n")

print(f"\n✅ 分析完成！")
print(f"   - 词云图文件: {wordcloud_file}")
print(f"   - 分类统计图: {category_file}")
print(f"   - 分析报告: {report_file}")
print(f"\n{'='*80}")
