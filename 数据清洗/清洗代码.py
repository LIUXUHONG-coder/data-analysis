import pandas as pd
import os
from datetime import datetime
import re

print("="*80)
print("淘宝评论数据清洗工具".center(80))
print("="*80)

# 查找最新的Excel文件
files = [f for f in os.listdir('.') if f.endswith('_FromTB.xlsx') and not f.startswith('~$') and '已清洗' not in f]
if not files:
    print("\n❌ 错误：未找到爬取的数据文件！")
    exit()

latest_file = max(files, key=lambda f: os.path.getmtime(f))
print(f"\n📁 原始文件: {latest_file}")
print(f"   文件大小: {os.path.getsize(latest_file)/1024:.2f} KB")

# 读取数据
try:
    df_review = pd.read_excel(latest_file, sheet_name='商品评论')
    original_count = len(df_review)
    print(f"\n📊 原始数据统计:")
    print(f"   - 评论总数: {original_count:,} 条")
    print(f"   - 平均长度: {df_review['评论内容'].astype(str).str.len().mean():.0f} 字")
    
    # 统计清洗前的问题
    print(f"\n🔍 清洗前数据质量:")
    seller_reply_count = df_review['评论内容'].astype(str).str.contains('商家回复|店家回复|卖家回复', na=False).sum()
    more_tag_count = df_review['评论内容'].astype(str).str.contains('更多', na=False).sum()
    newline_count = df_review['评论内容'].astype(str).str.contains('\n|\r', na=False, regex=True).sum()
    short_count = (df_review['评论内容'].astype(str).str.len() < 5).sum()
    
    print(f"   - 包含商家回复: {seller_reply_count} 条 ({seller_reply_count/original_count*100:.1f}%)")
    print(f"   - 包含'更多'标记: {more_tag_count} 条 ({more_tag_count/original_count*100:.1f}%)")
    print(f"   - 包含换行符: {newline_count} 条 ({newline_count/original_count*100:.1f}%)")
    print(f"   - 异常短评论(<5字): {short_count} 条 ({short_count/original_count*100:.1f}%)")
    
    # 开始清洗
    print(f"\n{'='*80}")
    print("开始数据清洗...".center(80))
    print(f"{'='*80}")
    
    # 步骤1: 移除商家回复
    print(f"\n[1/7] 移除商家回复...")
    def remove_seller_reply(text):
        if pd.isna(text):
            return text
        text = str(text)
        # 移除"商家回复："及之后的所有内容（包括前面的换行符）
        patterns = [
            r'\s*\n\s*商家回复[:：].*',
            r'\s*商家回复[:：].*',
            r'\s*\n\s*店家回复[:：].*',
            r'\s*店家回复[:：].*',
            r'\s*\n\s*卖家回复[:：].*',
            r'\s*卖家回复[:：].*'
        ]
        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.DOTALL)
        return text.strip()
    
    before = df_review['评论内容'].astype(str).str.contains('商家回复', na=False).sum()
    df_review['评论内容'] = df_review['评论内容'].apply(remove_seller_reply)
    after = df_review['评论内容'].astype(str).str.contains('商家回复', na=False).sum()
    print(f"      ✓ 移除了 {before - after} 条评论中的商家回复")
    
    # 步骤2: 移除"更多"标记
    print(f"[2/7] 移除'更多'标记...")
    before = df_review['评论内容'].astype(str).str.contains('更多', na=False).sum()
    df_review['评论内容'] = df_review['评论内容'].astype(str).str.replace(r'\s*\n\s*更多\s*$', '', regex=True)
    df_review['评论内容'] = df_review['评论内容'].astype(str).str.replace(r'\s*更多\s*$', '', regex=True)
    after = df_review['评论内容'].astype(str).str.contains('更多', na=False).sum()
    print(f"      ✓ 清理了 {before - after} 条评论中的'更多'标记")
    
    # 步骤3: 清理换行符
    print(f"[3/7] 清理换行符...")
    before = df_review['评论内容'].astype(str).str.contains('\n|\r', na=False, regex=True).sum()
    df_review['评论内容'] = df_review['评论内容'].astype(str).str.replace('\n', ' ')
    df_review['评论内容'] = df_review['评论内容'].astype(str).str.replace('\r', ' ')
    after = df_review['评论内容'].astype(str).str.contains('\n|\r', na=False, regex=True).sum()
    print(f"      ✓ 清理了 {before - after} 条评论中的换行符")
    
    # 步骤4: 清理多余空白
    print(f"[4/7] 清理多余空白字符...")
    df_review['评论内容'] = df_review['评论内容'].astype(str).str.replace(r'\s+', ' ', regex=True)
    df_review['评论内容'] = df_review['评论内容'].astype(str).str.strip()
    print(f"      ✓ 完成")
    
    # 步骤5: 移除重复的评论内容（同一句话重复出现两次）
    print(f"[5/7] 检测并移除重复内容...")
    def remove_duplicate_content(text):
        if pd.isna(text) or text == '':
            return text
        text = str(text).strip()
        # 检查是否前半部分和后半部分相同
        length = len(text)
        if length > 40:  # 只处理较长的文本
            mid = length // 2
            first_half = text[:mid].strip()
            second_half = text[mid:mid*2].strip()
            # 如果前半部分和后半部分完全相同，只保留前半部分
            if first_half == second_half and len(first_half) > 20:
                return first_half
        return text
    
    before_lengths = df_review['评论内容'].astype(str).str.len().sum()
    df_review['评论内容'] = df_review['评论内容'].apply(remove_duplicate_content)
    after_lengths = df_review['评论内容'].astype(str).str.len().sum()
    reduced_chars = before_lengths - after_lengths
    print(f"      ✓ 移除了约 {reduced_chars:,} 个重复字符")
    
    # 步骤6: 移除异常短评论（少于3字）
    print(f"[6/7] 移除异常短评论...")
    before_count = len(df_review)
    df_review['评论长度_temp'] = df_review['评论内容'].astype(str).str.len()
    short_reviews = df_review[df_review['评论长度_temp'] < 3]
    if len(short_reviews) > 0:
        print(f"\n      以下评论将被移除:")
        for idx, row in short_reviews.iterrows():
            print(f"         - [{row['用户名']}]: {row['评论内容']} (长度: {row['评论长度_temp']}字)")
    
    df_review = df_review[df_review['评论长度_temp'] >= 3]
    df_review = df_review.drop(columns=['评论长度_temp'])
    removed_count = before_count - len(df_review)
    print(f"\n      ✓ 移除 {removed_count} 条异常短评论")
    
    # 步骤7: 移除完全重复的评论
    print(f"[7/7] 移除完全重复的评论...")
    before_count = len(df_review)
    df_review = df_review.drop_duplicates(subset=['评论内容'], keep='first')
    dedup_count = before_count - len(df_review)
    print(f"      ✓ 移除 {dedup_count} 条重复评论")
    
    # 重新编号
    df_review = df_review.reset_index(drop=True)
    
    # 清洗后统计
    cleaned_count = len(df_review)
    removed_total = original_count - cleaned_count
    
    print(f"\n{'='*80}")
    print("清洗完成！".center(80))
    print(f"{'='*80}")
    
    print(f"\n📊 清洗结果统计:")
    print(f"   ├─ 原始评论: {original_count:,} 条")
    print(f"   ├─ 清洗后: {cleaned_count:,} 条")
    print(f"   ├─ 移除: {removed_total} 条 ({removed_total/original_count*100:.2f}%)")
    print(f"   └─ 保留率: {cleaned_count/original_count*100:.1f}%")
    
    # 清洗后质量检查
    print(f"\n🔍 清洗后数据质量:")
    seller_reply_count_after = df_review['评论内容'].astype(str).str.contains('商家回复|店家回复|卖家回复', na=False).sum()
    more_tag_count_after = df_review['评论内容'].astype(str).str.contains('更多', na=False).sum()
    newline_count_after = df_review['评论内容'].astype(str).str.contains('\n|\r', na=False, regex=True).sum()
    short_count_after = (df_review['评论内容'].astype(str).str.len() < 5).sum()
    avg_length = df_review['评论内容'].astype(str).str.len().mean()
    
    print(f"   ├─ 包含商家回复: {seller_reply_count_after} 条 ({seller_reply_count_after/cleaned_count*100:.1f}%)")
    print(f"   ├─ 包含'更多'标记: {more_tag_count_after} 条 ({more_tag_count_after/cleaned_count*100:.1f}%)")
    print(f"   ├─ 包含换行符: {newline_count_after} 条 ({newline_count_after/cleaned_count*100:.1f}%)")
    print(f"   ├─ 异常短评论(<5字): {short_count_after} 条 ({short_count_after/cleaned_count*100:.1f}%)")
    print(f"   └─ 平均长度: {avg_length:.0f} 字")
    
    # 保存清洗后的数据
    output_file = latest_file.replace('.xlsx', '_已清洗.xlsx')
    
    # 读取所有Sheet
    all_sheets = pd.read_excel(latest_file, sheet_name=None)
    
    # 替换商品评论Sheet
    all_sheets['商品评论'] = df_review
    
    # 保存到新文件
    print(f"\n💾 保存清洗后的数据...")
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        for sheet_name, df in all_sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"\n✅ 清洗完成！")
    print(f"   - 输出文件: {output_file}")
    print(f"   - 文件大小: {os.path.getsize(output_file)/1024:.2f} KB")
    
    # 显示清洗后的样本
    print(f"\n📝 清洗后的数据样本（前5条）:")
    print("="*80)
    for idx, row in df_review.head(5).iterrows():
        print(f"\n第{idx+1}条:")
        print(f"   用户: {row['用户名']}")
        print(f"   购买: {row['购买记录']}")
        content = row['评论内容'][:100] + '...' if len(row['评论内容']) > 100 else row['评论内容']
        print(f"   内容: {content}")
        print(f"   长度: {len(row['评论内容'])} 字")
    
    # 生成清洗日志
    log_file = f'数据清洗日志_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("数据清洗日志\n".center(80))
        f.write("="*80 + "\n")
        f.write(f"\n清洗时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n")
        f.write(f"原始文件: {latest_file}\n")
        f.write(f"输出文件: {output_file}\n\n")
        f.write(f"原始数据: {original_count:,} 条\n")
        f.write(f"清洗后: {cleaned_count:,} 条\n")
        f.write(f"移除: {removed_total} 条 ({removed_total/original_count*100:.2f}%)\n")
        f.write(f"保留率: {cleaned_count/original_count*100:.1f}%\n\n")
        f.write("清洗操作:\n")
        f.write(f"  1. 移除商家回复\n")
        f.write(f"  2. 移除'更多'标记\n")
        f.write(f"  3. 清理换行符\n")
        f.write(f"  4. 清理多余空白\n")
        f.write(f"  5. 移除重复内容\n")
        f.write(f"  6. 移除异常短评论\n")
        f.write(f"  7. 移除完全重复评论\n")
    
    print(f"\n📄 清洗日志已保存到: {log_file}")
    
    print(f"\n{'='*80}")
    
except Exception as e:
    print(f"\n❌ 清洗失败: {e}")
    import traceback
    traceback.print_exc() 
