#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
产品偏好挖掘分析
分析用户对手机核心属性的偏好，为产品设计和宣传提供数据支持
"""

import pandas as pd
import numpy as np
import re
from collections import Counter
from datetime import datetime
import jieba
import jieba.analyse

# 设置jieba分词
jieba.setLogLevel(jieba.logging.INFO)

# 读取数据 - 评论数据在第2个sheet
print("正在读取数据...")
df = pd.read_excel('指定商品_20250930-1555_FromTB_已清洗.xlsx', sheet_name=1)  # sheet_name=1 表示第2个sheet
print(f"数据加载完成，共 {len(df)} 条记录")
print(f"列名: {df.columns.tolist()}\n")

# ================== 1. 核心属性偏好排序 ==================
print("=" * 80)
print("一、核心属性偏好排序分析")
print("=" * 80)

# 定义核心属性关键词
attribute_keywords = {
    '续航': ['续航', '电池', '电量', '耐用', '待机', '省电', '掉电', '耗电', '充电'],
    '性能': ['性能', '流畅', '卡顿', '快', '慢', '运行', '处理器', '芯片', '内存', 'CPU'],
    '拍照': ['拍照', '相机', '摄像', '像素', '清晰', '成像', '镜头', '夜景', '美颜'],
    '外观': ['外观', '颜值', '好看', '漂亮', '设计', '手感', '质感', '轻薄', '颜色'],
    '屏幕': ['屏幕', '显示', '画质', '刷新率', '亮度', '色彩', '护眼'],
    '系统': ['系统', '软件', '功能', '操作', 'UI', '界面', '设置', '更新'],
    '价格': ['价格', '便宜', '贵', '性价比', '划算', '实惠', '优惠', '国补'],
    '音质': ['音质', '音量', '扬声器', '声音', '外放', '耳机'],
    '信号': ['信号', '网络', 'WiFi', '4G', '5G', '通话', '断网'],
    '发热': ['发热', '发烫', '烫手', '散热', '温度', '热'],
}

# 统计每个属性的提及次数
attribute_counts = {attr: 0 for attr in attribute_keywords.keys()}
attribute_positive = {attr: 0 for attr in attribute_keywords.keys()}
attribute_negative = {attr: 0 for attr in attribute_keywords.keys()}

# 正面和负面词汇
positive_words = ['好', '不错', '满意', '棒', '喜欢', '强', '给力', '优秀', '完美', '赞', 
                  '清晰', '流畅', '快', '耐用', '实惠', '舒服', '漂亮', '高']
negative_words = ['差', '不好', '卡', '慢', '烂', '垃圾', '失望', '后悔', '问题', '一般',
                  '糟糕', '难受', '不行', '不足', '弱', '虚标']

# 分析评论
comment_col = None
for col in ['评论内容', '评论', 'comment', 'content']:
    if col in df.columns:
        comment_col = col
        break

if comment_col:
    for idx, row in df.iterrows():
        comment = str(row[comment_col])
        if pd.isna(comment) or comment == 'nan':
            continue
            
        # 统计属性提及
        for attr, keywords in attribute_keywords.items():
            for keyword in keywords:
                if keyword in comment:
                    attribute_counts[attr] += 1
                    
                    # 判断正负面
                    context = comment[max(0, comment.find(keyword)-10):
                                    min(len(comment), comment.find(keyword)+20)]
                    
                    is_positive = any(pw in context for pw in positive_words)
                    is_negative = any(nw in context for nw in negative_words)
                    
                    if is_positive and not is_negative:
                        attribute_positive[attr] += 1
                    elif is_negative and not is_positive:
                        attribute_negative[attr] += 1
                    break

# 计算占比
total_comments = len(df)
attribute_stats = []
for attr in attribute_keywords.keys():
    count = attribute_counts[attr]
    positive = attribute_positive[attr]
    negative = attribute_negative[attr]
    neutral = count - positive - negative
    
    attribute_stats.append({
        '属性': attr,
        '提及次数': count,
        '提及率': f"{count/total_comments*100:.1f}%",
        '正面提及': positive,
        '负面提及': negative,
        '中性提及': neutral,
        '好评率': f"{positive/count*100:.1f}%" if count > 0 else "0%"
    })

# 按提及次数排序
attribute_stats_df = pd.DataFrame(attribute_stats)
attribute_stats_df = attribute_stats_df.sort_values('提及次数', ascending=False)

print("\n核心属性关注度排名:")
print(attribute_stats_df.to_string(index=False))

# ================== 2. 配置偏好分析 ==================
print("\n" + "=" * 80)
print("二、配置偏好分析")
print("=" * 80)

# 尝试找到配置相关列
config_col = None
for col in ['配置', 'sku', '规格', 'specification']:
    if col in df.columns:
        config_col = col
        break

if config_col:
    # 提取内存配置
    df['内存配置'] = df[config_col].apply(lambda x: 
        re.search(r'(\d+GB\+\d+GB)', str(x)).group(1) if re.search(r'(\d+GB\+\d+GB)', str(x)) else '未知')
    
    # 按配置分组分析
    config_groups = df.groupby('内存配置').size().sort_values(ascending=False)
    
    print("\n各配置购买数量:")
    for config, count in config_groups.items():
        print(f"  {config}: {count}条 ({count/total_comments*100:.1f}%)")
    
    # 各配置的关注点差异
    print("\n各配置用户关注点差异:")
    for config in config_groups.head(5).index:
        if config == '未知':
            continue
        config_df = df[df['内存配置'] == config]
        config_comments = ' '.join(config_df[comment_col].dropna().astype(str))
        
        # 统计该配置用户的关注点
        config_attr_counts = {}
        for attr, keywords in attribute_keywords.items():
            count = sum(config_comments.count(kw) for kw in keywords)
            config_attr_counts[attr] = count
        
        # 排序并显示前3
        top_attrs = sorted(config_attr_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        print(f"\n  {config}:")
        for attr, count in top_attrs:
            print(f"    - {attr}: {count}次提及")

# ================== 3. 颜色偏好分析 ==================
print("\n" + "=" * 80)
print("三、颜色偏好分析")
print("=" * 80)

# 提取颜色信息
colors = []
color_patterns = ['星光白', '曜夜黑', '远航蓝', '白', '黑', '蓝', '粉', '绿', '灰', '银']

if config_col:
    for idx, row in df.iterrows():
        config = str(row[config_col])
        for color in color_patterns:
            if color in config:
                colors.append(color)
                break
        else:
            colors.append('未知')
    
    df['颜色'] = colors
    color_groups = df.groupby('颜色').size().sort_values(ascending=False)
    
    print("\n各颜色购买数量:")
    for color, count in color_groups.items():
        if color != '未知':
            print(f"  {color}: {count}条 ({count/total_comments*100:.1f}%)")
    
    # 各颜色用户的评论特点
    print("\n各颜色用户评论特点:")
    for color in color_groups.head(5).index:
        if color == '未知':
            continue
        color_df = df[df['颜色'] == color]
        color_comments = ' '.join(color_df[comment_col].dropna().astype(str))
        
        # 提取高频词
        words = jieba.cut(color_comments)
        word_freq = Counter(words)
        # 过滤停用词和单字
        filtered_words = [(w, c) for w, c in word_freq.items() 
                         if len(w) > 1 and w not in ['手机', '很好', '不错', '非常']]
        top_words = sorted(filtered_words, key=lambda x: x[1], reverse=True)[:5]
        
        print(f"\n  {color}:")
        for word, count in top_words:
            print(f"    - {word}: {count}次")

# ================== 4. 用户画像偏好分析 ==================
print("\n" + "=" * 80)
print("四、用户画像偏好分析")
print("=" * 80)

# 识别用户群体
user_groups = {
    '学生党': ['学生', '上学', '大学', '高中', '宿舍'],
    '职场人': ['工作', '上班', '办公', '职场', '通勤'],
    '长辈用户': ['父母', '爸爸', '妈妈', '爷爷', '奶奶', '老人', '长辈'],
    '游戏玩家': ['游戏', '王者', '吃鸡', '和平精英', '帧率', '打游戏'],
    '摄影爱好者': ['拍照', '摄影', '相机', '美颜', '自拍', '照片']
}

user_group_stats = []
for group, keywords in user_groups.items():
    # 筛选该用户群体
    group_df = df[df[comment_col].apply(
        lambda x: any(kw in str(x) for kw in keywords) if pd.notna(x) else False
    )]
    
    if len(group_df) > 0:
        group_comments = ' '.join(group_df[comment_col].dropna().astype(str))
        
        # 统计该群体的属性关注度
        group_attr_counts = {}
        for attr, kws in attribute_keywords.items():
            count = sum(group_comments.count(kw) for kw in kws)
            group_attr_counts[attr] = count
        
        # 排序
        top_attrs = sorted(group_attr_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        user_group_stats.append({
            '用户群体': group,
            '评论数': len(group_df),
            '占比': f"{len(group_df)/total_comments*100:.1f}%",
            '关注点1': top_attrs[0][0] if len(top_attrs) > 0 else '-',
            '关注点2': top_attrs[1][0] if len(top_attrs) > 1 else '-',
            '关注点3': top_attrs[2][0] if len(top_attrs) > 2 else '-',
        })

user_group_df = pd.DataFrame(user_group_stats)
print("\n用户群体偏好分析:")
print(user_group_df.to_string(index=False))

# ================== 5. 宣传建议 ==================
print("\n" + "=" * 80)
print("五、产品宣传建议")
print("=" * 80)

print("\n1. 核心卖点宣传优先级:")
top_5_attrs = attribute_stats_df.head(5)
for idx, row in top_5_attrs.iterrows():
    print(f"   [{row['属性']}] - 提及率{row['提及率']}, 好评率{row['好评率']}")

print("\n2. 针对性宣传话术建议:")
print("   ▸ 高配置用户(16GB+512GB): 强调'旗舰性能'、'多任务处理'、'游戏流畅'")
print("   ▸ 标配用户(12GB+256GB): 强调'性价比'、'日常够用'、'国补优惠'")
print("   ▸ 游戏玩家: 强调'骁龙芯片'、'高刷屏'、'游戏优化'")
print("   ▸ 长辈用户: 强调'大电池'、'大音量'、'简单易用'")
print("   ▸ 职场人士: 强调'长续航'、'快充'、'商务外观'")

print("\n3. 产品改进建议:")
if attribute_negative['发热'] > 50:
    print("   ⚠ 发热问题突出，需改进散热设计")
if attribute_negative['性能'] > 30:
    print("   ⚠ 性能优化不足，需优化系统流畅度")
if attribute_negative['拍照'] > 20:
    print("   ⚠ 拍照效果需提升，考虑升级相机模组")

# ================== 生成报告 ==================
print("\n" + "=" * 80)
print("正在生成详细报告...")
print("=" * 80)

report_time = datetime.now().strftime("%Y%m%d_%H%M%S")
report_filename = f"产品偏好挖掘报告_{report_time}.txt"

with open(report_filename, 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("                     vivo手机产品偏好挖掘报告\n")
    f.write("=" * 80 + "\n\n")
    f.write(f"分析时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n")
    f.write(f"数据来源: 指定商品_20250930-1555_FromTB_已清洗.xlsx\n")
    f.write(f"样本总数: {total_comments:,} 条评论\n\n")
    
    f.write("一、核心属性偏好排序\n")
    f.write("-" * 80 + "\n\n")
    f.write(attribute_stats_df.to_string(index=False))
    f.write("\n\n")
    
    if config_col:
        f.write("二、配置偏好分析\n")
        f.write("-" * 80 + "\n\n")
        f.write("各配置购买数量:\n")
        for config, count in config_groups.items():
            f.write(f"  {config}: {count}条 ({count/total_comments*100:.1f}%)\n")
        f.write("\n")
    
    f.write("三、用户群体偏好分析\n")
    f.write("-" * 80 + "\n\n")
    f.write(user_group_df.to_string(index=False))
    f.write("\n\n")
    
    f.write("四、产品宣传建议\n")
    f.write("-" * 80 + "\n\n")
    f.write("1. 核心卖点优先级:\n")
    for idx, row in top_5_attrs.iterrows():
        f.write(f"   - {row['属性']}: 提及率{row['提及率']}, 好评率{row['好评率']}\n")
    f.write("\n")
    
    f.write("2. 差异化宣传建议:\n")
    f.write("   高配版: 突出性能和游戏体验\n")
    f.write("   标配版: 突出性价比和实用性\n")
    f.write("   浅色款: 突出外观设计和颜值\n")
    f.write("   深色款: 突出商务质感\n")
    f.write("\n")
    
    f.write("=" * 80 + "\n")
    f.write("报告生成完毕\n")

print(f"\n✓ 报告已保存至: {report_filename}")
print("分析完成！") 