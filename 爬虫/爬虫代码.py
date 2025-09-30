# 代码说明：
'''
代码功能： 基于ChromeDriver爬取taobao（淘宝）平台商品列表数据
输入参数:  KEYWORLD --> 搜索商品“关键词”；
          pageStart --> 爬取起始页；
          pageEnd --> 爬取终止页；
输出文件：爬取商品列表数据
        'Page'        ：页码
        'Num'         ：序号
        'title'       ：商品标题
        'Price'       ：商品价格
        'Deal'        ：商品销量
        'Location'    ：地理位置
        'Shop'        ：商品
        'IsPostFree'  ：是否包邮
        'Title_URL'   ：商品详细页链接
        'Shop_URL'    ：商铺链接
        'Img_URL'     ：图片链接
'''
# 声明第三方库/头文件
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from pyquery import PyQuery as pq
import time
import random                       #用于随机等待，降低反爬风险
import re                           #用于正则表达式匹配
import openpyxl as op               #导入Excel读写库
 
# 全局变量
count = 1                                   # 写入Excel商品计数
review_count = 1                            # 写入Excel评论计数
 
print("\n" + "="*60)
print("淘宝商品信息爬虫 v2.0")
print("功能：爬取商品基本信息 + 商品评论（可选）")
print("="*60 + "\n")

# 选择爬取模式
print("请选择爬取模式：")
print("1. 搜索关键词爬取")
print("2. 指定店铺商品爬取")
crawl_mode = input("输入模式编号（1或2，默认1）：").strip() or "1"

if crawl_mode == "2":
    # 指定店铺模式
    SHOP_URL = input('输入店铺商品链接：').strip()
    KEYWORD = "指定商品"
    pageStart = 1
    pageEnd = 1
    LIMIT_PRODUCTS = 1
    print(f"\n模式：指定店铺商品爬取")
else:
    # 搜索模式
    SHOP_URL = None
    KEYWORD = input('输入搜索的商品关键词Keyword：')# 要搜索的商品的关键词
    pageStart = int(input('输入爬取的起始页PageStart：'))# 爬取起始页
    pageEnd = int(input('输入爬取的终止页PageEnd：'))# 爬取终止页
    
    # 如果只爬取1页，询问是否限制商品数量
    if pageStart == pageEnd:
        limit_input = input(f'爬取商品数量（直接回车爬取整页，默认约44个）：').strip()
        LIMIT_PRODUCTS = int(limit_input) if limit_input else None
        if LIMIT_PRODUCTS:
            print(f"将爬取前 {LIMIT_PRODUCTS} 个商品")
    else:
        LIMIT_PRODUCTS = None

CRAWL_REVIEWS = input('是否爬取商品评论？(y/n)：').lower() == 'y'  # 是否爬取评论

if CRAWL_REVIEWS:
    print("\n提示：评论爬取会显著增加运行时间（每个商品约需30-60秒）")
    if LIMIT_PRODUCTS:
        print(f"预计总时间：约{LIMIT_PRODUCTS * 0.8}分钟\n")
    else:
        print(f"预计总时间：约{(pageEnd-pageStart+1)*44*0.8}分钟（假设每页44个商品）\n")
    
    print("⚠️  反爬提示：")
    print("   - 爬取评论时可能触发淘宝滑块验证")
    print("   - 程序会自动检测并等待您手动完成验证")
    print("   - 完成验证后程序会自动继续")
    print("   - 为降低反爬风险，每个商品间会随机等待3-6秒\n")
 
# 启动ChromeDriver服务
print("正在启动Chrome浏览器...")
options = webdriver.ChromeOptions()
# 关闭自动测试状态显示 // 会导致浏览器报：请停用开发者模式
options.add_experimental_option("excludeSwitches", ['enable-automation'])

# 尝试多种方式启动 ChromeDriver
import os
try:
    # 方式1: 如果当前目录有 chromedriver.exe，优先使用
    local_chromedriver = os.path.join(os.getcwd(), 'chromedriver.exe')
    if os.path.exists(local_chromedriver):
        print(f"使用本地 ChromeDriver: {local_chromedriver}")
        service = Service(local_chromedriver)
        driver = webdriver.Chrome(service=service, options=options)
    else:
        # 方式2: 使用 webdriver-manager 自动下载
        print("尝试自动下载 ChromeDriver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
except Exception as e:
    print(f"启动失败: {e}")
    print("\n请手动下载 ChromeDriver:")
    print("1. 访问: https://googlechromelabs.github.io/chrome-for-testing/")
    print("2. 下载 Chrome 140 版本对应的 chromedriver-win64.zip")
    print("3. 解压后将 chromedriver.exe 放到当前目录:")
    print(f"   {os.getcwd()}")
    print("4. 重新运行程序")
    exit(1)

print("Chrome浏览器启动成功！")
# 反爬机制
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument",
                       {"source": """Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"""})
# 窗口最大化
driver.maximize_window()
print("正在打开淘宝页面...")

# 根据模式选择打开的页面
if SHOP_URL:
    # 指定商品模式：直接打开淘宝首页
    driver.get('https://www.taobao.com/')
else:
    # 搜索模式：打开淘宝搜索页
    driver.get('https://s.taobao.com/')

# wait是Selenium中的一个等待类，用于在特定条件满足之前等待一定的时间(这里是20秒)。
# 如果一直到等待时间都没满足则会捕获TimeoutException异常
wait = WebDriverWait(driver,20)

# 等待用户登录
print("\n" + "="*60)
print("请在浏览器中完成以下操作：")
print("1. 登录淘宝账号（输入手机号和验证码）")
print("2. 完成任何验证（滑块、点选等）")
if SHOP_URL:
    print("3. 确保已经登录淘宝")
else:
    print("3. 确保已经进入淘宝搜索页面")
print("="*60)
input("完成登录后，按 Enter 键继续...")
 
 
 
# 输入“关键词”，搜索
def search_goods():
    try:
        print("正在搜索: {}".format(KEYWORD))
        # 找到搜索“输入框”
        # input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#q")))
        input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="q"]')))
        # 找到“搜索”按钮
        # submit = wait.until(
        #     EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_TSearchForm > div.search-button > button')))
        submit = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="J_SearchForm"]/div/div[1]/button')))
        # 输入框写入"关键词KeyWord"
        input.send_keys(KEYWORD)
        # 点击"搜索"按键
        submit.click()
        print("已点击搜索按钮，等待页面加载...")
        # 搜索商品后等待5秒，如有滑块或验证，请手动处理
        time.sleep(5)
        
        # 自动检测验证码
        has_verification = detect_and_wait_for_verification(driver, "搜索结果页")
        
        if not has_verification:
            # 如果没有自动检测到验证，再询问用户
            print("\n如果出现滑块验证或其他验证，请在浏览器中手动完成...")
            user_input = input("验证完成后，按 Enter 键继续（如已完成验证直接按Enter）...")
        
        print("搜索完成！")
    except Exception as exc:
        print("search_goods函数错误！Error：{}".format(exc))
 
# 翻页至第pageStar页
def turn_pageStart():
    try:
        print("正在翻转:第{}页".format(pageStart))
        # 滑动到页面底端
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # 滑动到底部后停留3s
        time.sleep(3)
        # 找到输入“页面”的表单，输入“起始页”
        pageInput = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="search-content-leftWrap"]/div[3]/div[3]/div/div/span[3]/input')))
        pageInput.send_keys(pageStart)
        # 找到页面跳转的“确定”按钮，并且点击
        admit = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="search-content-leftWrap"]/div[3]/div[3]/div/div/button[3]')))
        admit.click()
        print("已翻至:第{}页".format(pageStart))
    except Exception as exc:
        print("turn_pageStart函数错误！Error：{}".format(exc))
        
# 翻页函数
def page_turning(page_number):
    try:
        print("正在翻页: 第{}页".format(page_number))
        # 强制等待2秒后翻页
        time.sleep(2)
        # 找到"下一页"的按钮
        submit = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="search-content-leftWrap"]/div[3]/div[3]/div/div/button[2]')))
        submit.click()
        # 判断页数是否相等
        wait.until(EC.text_to_be_present_in_element((By.XPATH, '//*[@id="search-content-leftWrap"]/div[3]/div[3]/div/div/span[1]/em'), str(page_number)))
        print("已翻至: 第{}页".format(page_number))

        clicked = False
        matched_i = None
        matched_j = None
        for i in range(10):
            for j in range(10):
                xpath = f'//*[@id="search-content-leftWrap"]/div[{i}]/div[{j}]/div/div/button[2]'
                elements = driver.find_elements(By.XPATH, xpath)
                if elements:
                    try:
                        submit = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                        submit.click()
                        print(f"点击\"下一页\"按钮成功，使用的XPath: {xpath}")
                        matched_i = i
                        matched_j = j
                        clicked = True
                        break
                    except:
                        continue
            if clicked:
                break

    except Exception as exc:
        print("page_turning函数错误！Error：{}".format(exc))
 
# 获取每一页的商品信息；
def get_goods(page):
    try:
        # 声明全局变量count
        global count
        
        # 滚动页面多次，确保所有商品都加载出来
        print(f"\n正在加载第{page}页的所有商品...")
        for i in range(5):  # 分5次滚动
            scroll_height = (i + 1) * (driver.execute_script("return document.body.scrollHeight") // 5)
            driver.execute_script(f"window.scrollTo(0, {scroll_height});")
            time.sleep(1.5)  # 每次滚动后等待1.5秒
        
        # 滚动到底部
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        # 再滚回顶部，确保所有内容都已渲染
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        print("页面加载完成，开始提取商品信息...")
        
        # 获取html网页
        html = driver.page_source
        doc = pq(html)
        # 提取所有商品的共同父元素的类选择器
        items = list(doc('div.content--CUnfXXxv > div > div').items())
        print(f"共找到 {len(items)} 个元素块")
        
        extracted_count = 0  # 实际提取的商品数
        for item in items:
            # 跳过非商品元素
            if item.find('.title--RoseSo8H').text() == '大家都在搜':
                continue
            elif item.find('.headTitleText--hxVemljn').text() == '对本次搜索体验满意吗':
                continue
            
            # 尝试提取商品信息，如果失败则跳过
            try:
                # 定位商品标题
                title = item.find('.title--qJ7Xg_90 span').text()
                if not title:  # 如果标题为空，跳过
                    continue
                
                # 定位价格
                price_text = item.find('.innerPriceWrapper--aAJhHXD4').text()
                if price_text:
                    price = float(price_text.replace('\n', '').replace('\r', ''))
                else:
                    price = 0
                
                # 定位交易量
                deal_text = item.find('.realSales--XZJiepmt').text()
                if deal_text:
                    deal = deal_text.replace("万","0000")                 # "万"字替换为0000
                    deal = deal.split("人")[0]                       # 以"人"分隔
                    deal = deal.split("+")[0]                        # 以"+"分隔
                    try:
                        deal = int(deal)
                    except:
                        deal = 0
                else:
                    deal = 0
                
                # 定位所在地信息
                location = item.find('.procity--wlcT2xH9 span').text() or "未知"
                
                # 定位店名
                shop = item.find('.shopNameText--DmtlsDKm').text() or "未知"
                
                # 定位包邮的位置
                postText = item.find('.subIconWrapper--Vl8zAdQn').text()
                postText = "包邮" if "包邮" in postText else "/"
                
                # 定位商品url
                t_url_elem = item.find('.doubleCardWrapperAdapt--mEcC7olq')
                t_url = t_url_elem.attr('href') if t_url_elem else ""
                
                # 定位店名url
                shop_url_elem = item.find('.TextAndPic--grkZAtsC a')
                shop_url = shop_url_elem.attr('href') if shop_url_elem else ""
                
                # 定位商品图片url
                img_elem = item.find('.mainPicAdaptWrapper--V_ayd2hD img')
                img_url = img_elem.attr('src') if img_elem else ""
                
                # 构建商品信息字典
                product = {
                    'Page':         page,
                    'Num':          count-1,
                    'title':        title,
                    'price':        price,
                    'deal':         deal,
                    'location':     location,
                    'shop':         shop,
                    'isPostFree':   postText,
                    'url':          t_url,
                    'shop_url':     shop_url,
                    'img_url':      img_url
                }
                print(f"[{extracted_count + 1}] {title[:30]}... - ¥{price}")
                
                # 商品信息写入Excel表格中
                wb.cell(row=count, column=1, value=count-1)                 # 序号
                wb.cell(row=count, column=2, value=title)               # 标题
                wb.cell(row=count, column=3, value=price)               # 价格
                wb.cell(row=count, column=4, value=deal)           # 付款人数
                wb.cell(row=count, column=5, value=location)            # 地理位置
                wb.cell(row=count, column=6, value=shop)                # 店铺名称
                wb.cell(row=count, column=7, value=postText)            # 是否包邮
                wb.cell(row=count, column=8, value=t_url)               # 商品链接
                wb.cell(row=count, column=9, value=shop_url)           # 商铺链接
                wb.cell(row=count, column=10, value=img_url)            # 图片链接
                
                product_num = count - 1  # 商品序号
                count += 1                                              # 下一行
                extracted_count += 1
                
                # 如果启用了评论爬取，则爬取该商品的评论
                if CRAWL_REVIEWS and t_url:
                    global review_count
                    print(f"  └─ 开始爬取商品评论...")
                    
                    # 随机等待3-6秒，模拟人工操作，降低反爬风险
                    wait_time = random.uniform(3, 6)
                    print(f"  └─ 等待 {wait_time:.1f} 秒（模拟人工操作，降低反爬风险）...")
                    time.sleep(wait_time)
                    
                    reviews = get_product_reviews(t_url, title, product_num)
                    
                    # 将评论写入评论Sheet
                    for review in reviews:
                        wb_review.cell(row=review_count, column=1, value=review['product_num'])      # 商品序号
                        wb_review.cell(row=review_count, column=2, value=title[:50])                # 商品标题（截取）
                        wb_review.cell(row=review_count, column=3, value=review['username'])        # 用户名
                        wb_review.cell(row=review_count, column=4, value=review['purchase_info'])   # 购买记录（含时间）
                        wb_review.cell(row=review_count, column=5, value=review['content'])         # 评论内容
                        review_count += 1
                    
                    print(f"  └─ 该商品评论已保存 ({len(reviews)}条)\n")
                
                # 检查是否达到限制数量
                if LIMIT_PRODUCTS and extracted_count >= LIMIT_PRODUCTS:
                    print(f"✓ 已达到指定数量 {LIMIT_PRODUCTS} 个商品，停止爬取本页")
                    break
                
            except Exception as item_exc:
                # 单个商品提取失败不影响其他商品
                print(f"跳过一个商品（提取失败）: {item_exc}")
                continue
        
        print(f"第{page}页提取完成，共提取 {extracted_count} 个商品\n")
        
    except Exception as exc:
        print("get_goods函数错误！Error：{}".format(exc))
 
# 检测并等待用户完成验证码
def detect_and_wait_for_verification(driver, page_name="当前页面"):
    """
    检测页面是否出现验证码，如果有则等待用户手动完成
    :param driver: webdriver实例
    :param page_name: 页面名称（用于提示）
    :return: 是否检测到验证码
    """
    try:
        # 更精确的验证码检测 - 只检测真正的验证框特征
        has_verification = False
        
        # 1. 检查是否有明确的验证iframe（最可靠）
        iframes = driver.find_elements(By.TAG_NAME, 'iframe')
        for iframe in iframes:
            try:
                iframe_src = iframe.get_attribute('src') or ''
                iframe_id = iframe.get_attribute('id') or ''
                # 淘宝验证框的特征
                if any(keyword in iframe_src.lower() for keyword in ['verify', 'captcha', 'nocaptcha', 'checkcode']):
                    has_verification = True
                    break
                if any(keyword in iframe_id.lower() for keyword in ['verify', 'captcha', 'nc_']):
                    has_verification = True
                    break
            except:
                pass
        
        # 2. 检查是否有验证滑块元素（通过class名）
        if not has_verification:
            try:
                verification_elements = driver.find_elements(By.CSS_SELECTOR, 
                    'div[class*="nc_"], div[class*="verify"], div[class*="captcha"], div[id*="nc_"]')
                for elem in verification_elements:
                    try:
                        if elem.is_displayed() and elem.size['height'] > 30:  # 验证框通常有一定高度
                            # 进一步检查是否包含滑块文本
                            elem_text = elem.text.lower()
                            if any(word in elem_text for word in ['拖动', '滑块', '向右', 'slide']):
                                has_verification = True
                                break
                    except:
                        pass
            except:
                pass
        
        # 3. 只有在明确检测到验证元素时才报警（不再用关键词匹配，太容易误报）
        
        if has_verification:
            print(f"\n    ⚠️  检测到{page_name}可能出现验证码！")
            print(f"    ⚠️  请检查浏览器：")
            print(f"         - 如果确实有验证码：请手动完成滑块验证")
            print(f"         - 如果没有验证码（误报）：等待5秒后自动继续")
            print(f"    ⏳ 等待中（5秒后自动检查）...")
            time.sleep(5)  # 先等5秒，给用户时间看清楚
            
            # 再次检查确认
            still_has = False
            try:
                iframes = driver.find_elements(By.TAG_NAME, 'iframe')
                for iframe in iframes:
                    iframe_src = iframe.get_attribute('src') or ''
                    if any(k in iframe_src.lower() for k in ['verify', 'captcha', 'nocaptcha']):
                        still_has = True
                        break
            except:
                pass
            
            if not still_has:
                print(f"    ✓ 未检测到验证码，继续爬取...")
                return False
            
            print(f"    ⚠️  确认存在验证码，请完成验证")
            print(f"    ⏳ 等待验证完成...")
            
            # 等待用户完成验证（最多等待120秒，每10秒检查一次）
            max_wait = 120
            wait_interval = 10
            elapsed = 0
            
            while elapsed < max_wait:
                time.sleep(wait_interval)
                elapsed += wait_interval
                
                # 再次检查验证码是否还存在（用相同的精确方法）
                still_has_verification = False
                
                # 重新检查iframe
                iframes = driver.find_elements(By.TAG_NAME, 'iframe')
                for iframe in iframes:
                    try:
                        iframe_src = iframe.get_attribute('src') or ''
                        iframe_id = iframe.get_attribute('id') or ''
                        if any(keyword in iframe_src.lower() for keyword in ['verify', 'captcha', 'nocaptcha', 'checkcode']):
                            still_has_verification = True
                            break
                        if any(keyword in iframe_id.lower() for keyword in ['verify', 'captcha', 'nc_']):
                            still_has_verification = True
                            break
                    except:
                        pass
                
                # 重新检查验证元素
                if not still_has_verification:
                    try:
                        verification_elements = driver.find_elements(By.CSS_SELECTOR, 
                            'div[class*="nc_"], div[class*="verify"], div[class*="captcha"]')
                        for elem in verification_elements:
                            try:
                                if elem.is_displayed() and elem.size['height'] > 30:
                                    elem_text = elem.text.lower()
                                    if any(word in elem_text for word in ['拖动', '滑块', '向右', 'slide']):
                                        still_has_verification = True
                                        break
                            except:
                                pass
                    except:
                        pass
                
                if not still_has_verification:
                    print(f"    ✓ 验证完成！继续爬取...")
                    time.sleep(2)  # 等待页面稳定
                    return True
                else:
                    print(f"    ⏳ 仍在等待验证... ({elapsed}秒)")
            
            print(f"    ⚠️  等待超时，继续尝试爬取...")
            return False
        
        return False
        
    except Exception as e:
        print(f"    ⚠️  验证检测出错：{e}")
        return False

# 直接爬取指定商品
def crawl_direct_product():
    try:
        global count, review_count
        print(f"\n正在访问指定商品链接...")
        
        # 直接打开商品链接
        if not SHOP_URL.startswith('http'):
            url = 'https:' + SHOP_URL
        else:
            url = SHOP_URL
            
        driver.get(url)
        time.sleep(5)
        
        print(f"页面加载完成")
        
        # 获取商品标题
        html = driver.page_source
        doc = pq(html)
        title = doc('title').text() or "指定商品"
        
        print(f"[1] {title}")
        
        # 写入商品基本信息
        wb.cell(row=count, column=1, value=count-1)
        wb.cell(row=count, column=2, value=title)
        wb.cell(row=count, column=8, value=url)
        
        product_num = count - 1
        count += 1
        
        # 如果启用了评论爬取
        if CRAWL_REVIEWS:
            print(f"  └─ 开始爬取商品评论...")
            reviews = get_product_reviews(url, title, product_num)
            
            # 将评论写入评论Sheet
            for review in reviews:
                wb_review.cell(row=review_count, column=1, value=review['product_num'])
                wb_review.cell(row=review_count, column=2, value=title[:50])
                wb_review.cell(row=review_count, column=3, value=review['username'])
                wb_review.cell(row=review_count, column=4, value=review['purchase_info'])   # 购买记录（含时间）
                wb_review.cell(row=review_count, column=5, value=review['content'])         # 评论内容
                review_count += 1
            
            print(f"  └─ 该商品评论已保存 ({len(reviews)}条)\n")
            
    except Exception as exc:
        print(f"crawl_direct_product函数错误！Error：{exc}")

# 爬虫main函数
def Crawer_main():
    try:
        # 判断是否是指定商品模式
        if SHOP_URL:
            crawl_direct_product()
        else:
            # 搜索KEYWORD
            search_goods()
            # 判断pageStart是否为第1页
            if pageStart != 1:
                turn_pageStart()
            # 爬取PageStart的商品信息
            get_goods(pageStart)
            # 从PageStart+1爬取到PageEnd
            for i in range(pageStart + 1, pageEnd+1):
                page_turning(i)
                get_goods(i)
    except Exception as exc:
        print("Crawer_main函数错误！Error：{}".format(exc))

# 爬取商品评论（滚动加载全部）
def get_product_reviews(product_url, product_title, product_num):
    """
    打开商品详情页，滚动加载并爬取所有评论
    :param product_url: 商品详情页链接
    :param product_title: 商品标题（用于显示）
    :param product_num: 商品序号（用于关联）
    :return: 评论列表
    """
    reviews = []
    main_window = None
    
    try:
        print(f"    ↳ 正在打开商品详情页...")
        
        # 检查URL是否有效
        if not product_url or product_url == "":
            print(f"    ↳ 错误：商品链接为空，跳过该商品")
            return reviews
        
        # 补全URL（如果是相对路径）
        if not product_url.startswith('http'):
            product_url = 'https:' + product_url
        
        # 记录当前窗口句柄
        main_window = driver.current_window_handle
        
        # 在新标签页打开商品详情页
        driver.execute_script(f"window.open('{product_url}', '_blank');")
        time.sleep(3)  # 等待新标签页打开
        
        # 切换到新标签页
        all_windows = driver.window_handles
        if len(all_windows) <= 1:
            print(f"    ↳ 错误：新标签页未打开，跳过该商品")
            return reviews
            
        for window in all_windows:
            if window != main_window:
                driver.switch_to.window(window)
                break
        
        time.sleep(3)  # 等待页面加载
        
        # 检测是否出现验证码
        verification_detected = detect_and_wait_for_verification(driver, "商品详情页")
        
        # 关闭可能出现的弹窗
        print(f"    ↳ 尝试关闭弹窗...")
        try:
            # 常见弹窗关闭按钮
            close_selectors = [
                "//div[contains(@class, 'close')]",
                "//a[contains(@class, 'close')]",
                "//span[contains(@class, 'close')]",
                "//i[contains(@class, 'close')]",
            ]
            for selector in close_selectors:
                try:
                    close_buttons = driver.find_elements(By.XPATH, selector)
                    for btn in close_buttons[:2]:
                        try:
                            if btn.is_displayed():
                                btn.click()
                                time.sleep(0.5)
                                print(f"    ↳ 已关闭一个弹窗")
                        except:
                            pass
                except:
                    pass
        except Exception as e:
            pass
        
        # 滚动到评论区域（分多次慢慢滚动）
        print(f"    ↳ 滚动到评论区域...")
        for i in range(6):  # 滚动6次，确保滚到评论位置
            driver.execute_script(f"window.scrollTo(0, {(i+1) * 600});")
            time.sleep(1.5)
        
        # 寻找并点击"查看全部评价"按钮
        print(f"    ↳ 寻找'查看全部评价'按钮...")
        review_button_found = False
        
        try:
            # 方法1：通过文本内容查找
            review_button_texts = ['查看全部评价', '全部评论', '查看评论', '全部评价', '累计评价']
            for text in review_button_texts:
                try:
                    buttons = driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
                    for btn in buttons:
                        try:
                            if btn.is_displayed():
                                # 滚动到按钮位置
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                time.sleep(1)
                                btn.click()
                                time.sleep(3)
                                print(f"    ↳ 已点击'{text}'按钮")
                                review_button_found = True
                                break
                        except:
                            continue
                    if review_button_found:
                        break
                except:
                    continue
            
            # 方法2：如果文本查找失败，尝试通过类名查找
            if not review_button_found:
                try:
                    button_selectors = [
                        "div.ShowButton--fMu7HZNs",
                        "div[class*='ShowButton']",
                        "div[class*='showButton']"
                    ]
                    for selector in button_selectors:
                        buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                        if buttons:
                            for btn in buttons:
                                try:
                                    if btn.is_displayed():
                                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                        time.sleep(1)
                                        btn.click()
                                        time.sleep(3)
                                        print(f"    ↳ 已点击评价按钮（通过类名）")
                                        review_button_found = True
                                        break
                                except:
                                    continue
                            if review_button_found:
                                break
                except:
                    pass
                    
        except Exception as e:
            pass
        
        if not review_button_found:
            print(f"    ↳ 未找到'查看全部评价'按钮，尝试直接提取当前页面评论")
        
        # 检测是否出现验证码（点击评论按钮后）
        time.sleep(2)
        detect_and_wait_for_verification(driver, "评论页面")
        
        # 检查是否打开了新页面/标签
        time.sleep(2)
        current_windows = driver.window_handles
        if len(current_windows) > len([main_window]):
            # 打开了新标签页，切换过去
            for window in current_windows:
                if window != main_window and window != driver.current_window_handle:
                    driver.switch_to.window(window)
                    print(f"    ↳ 检测到新标签页，已切换")
                    time.sleep(2)
                    break
        
        # 寻找评论容器（可能是弹窗、侧边栏等）
        print(f"    ↳ 正在定位评论容器...")
        review_container = None
        container_selectors = [
            'div[class*="Comments--"]',  # 评论容器
            'div[class*="comments"]',
            'div[class*="review"]',
            'div.beautify-scroll-bar',  # 带滚动条的容器
            'div[class*="drawer"]',  # 抽屉/侧边栏
            'div[class*="modal"]',  # 模态框
            'div[class*="panel"]',  # 面板
        ]
        
        for selector in container_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    # 检查元素是否可滚动（有overflow属性）
                    overflow = driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).overflowY;", elem
                    )
                    if overflow in ['auto', 'scroll']:
                        review_container = elem
                        print(f"    ↳ 找到可滚动评论容器：{selector}")
                        break
                if review_container:
                    break
            except:
                continue
        
        # 先尝试点击"加载更多"按钮（如果存在）
        try:
            print(f"    ↳ 尝试点击'加载更多'按钮...")
            load_more_texts = ['加载更多', '查看更多', '展开更多', '点击加载更多']
            for text in load_more_texts:
                try:
                    buttons = driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
                    for btn in buttons[:2]:  # 最多点击2个
                        try:
                            if btn.is_displayed():
                                btn.click()
                                time.sleep(2)
                                print(f"    ↳ 已点击'{text}'按钮")
                        except:
                            pass
                except:
                    pass
        except:
            pass
        
        # 滚动加载所有评论（优化滚动策略）
        print(f"    ↳ 开始滚动加载所有评论...")
        scroll_attempts = 0
        max_scrolls = 500  # 增加到500次滚动，确保加载全部评论（5000+条）
        unchanged_count = 0  # 记录高度未变化的次数
        no_new_reviews_count = 0  # 记录评论数量未增加的次数
        
        if review_container:
            # 滚动评论容器
            print(f"    ↳ 滚动评论容器（左侧面板）...")
            last_height = driver.execute_script("return arguments[0].scrollHeight;", review_container)
            last_review_count = 0
            
            while scroll_attempts < max_scrolls:
                # 滚动容器到底部
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", review_container)
                time.sleep(1.5)  # 优化等待时间
                
                # 每滚动15次，尝试点击"加载更多"按钮
                if scroll_attempts % 15 == 0 and scroll_attempts > 0:
                    try:
                        load_more = driver.find_elements(By.XPATH, "//*[contains(text(), '加载更多') or contains(text(), '查看更多')]")
                        for btn in load_more[:1]:
                            try:
                                if btn.is_displayed():
                                    btn.click()
                                    time.sleep(1)
                            except:
                                pass
                    except:
                        pass
                
                # 计算新的滚动高度
                new_height = driver.execute_script("return arguments[0].scrollHeight;", review_container)
                
                # 获取当前评论数量（用于显示进度和判断）
                current_reviews = len(driver.find_elements(By.CSS_SELECTOR, 'div.Comment--H5QmJwe9, div[class*="Comment--"]'))
                
                # 检查评论数量是否增加
                if current_reviews > last_review_count:
                    no_new_reviews_count = 0  # 有新评论，重置计数
                    last_review_count = current_reviews
                else:
                    no_new_reviews_count += 1
                
                # 如果高度没变且评论数量没变，连续10次才停止
                if new_height == last_height:
                    unchanged_count += 1
                    if unchanged_count >= 8 and no_new_reviews_count >= 8:
                        print(f"    ↳ 容器已滚动到底部（高度和评论数连续未变化，共{current_reviews}条）")
                        break
                    elif unchanged_count >= 8:
                        print(f"    ↳ 高度未变化（{unchanged_count}次），但可能还有评论，继续...")
                else:
                    unchanged_count = 0
                    last_height = new_height
                
                scroll_attempts += 1
                if scroll_attempts % 20 == 0:  # 每20次显示一次进度
                    print(f"    ↳ 第{scroll_attempts}次滚动，已加载 {current_reviews} 条评论...")
                    # 每滚动50次检测一次验证码（降低检测频率）
                    if scroll_attempts % 50 == 0:
                        detect_and_wait_for_verification(driver, "评论滚动中")
        else:
            # 没找到容器，滚动整个页面
            print(f"    ↳ 未找到评论容器，滚动整个页面...")
            last_height = driver.execute_script("return document.body.scrollHeight")
            last_review_count = 0
            
            while scroll_attempts < max_scrolls:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)
                
                # 每滚动15次，尝试点击"加载更多"按钮
                if scroll_attempts % 15 == 0 and scroll_attempts > 0:
                    try:
                        load_more = driver.find_elements(By.XPATH, "//*[contains(text(), '加载更多') or contains(text(), '查看更多')]")
                        for btn in load_more[:1]:
                            try:
                                if btn.is_displayed():
                                    btn.click()
                                    time.sleep(1)
                            except:
                                pass
                    except:
                        pass
                
                new_height = driver.execute_script("return document.body.scrollHeight")
                current_reviews = len(driver.find_elements(By.CSS_SELECTOR, 'div.Comment--H5QmJwe9, div[class*="Comment--"]'))
                
                # 检查评论数量是否增加
                if current_reviews > last_review_count:
                    no_new_reviews_count = 0
                    last_review_count = current_reviews
                else:
                    no_new_reviews_count += 1
                
                if new_height == last_height:
                    unchanged_count += 1
                    if unchanged_count >= 8 and no_new_reviews_count >= 8:
                        print(f"    ↳ 已滚动到底部（高度和评论数连续未变化，共{current_reviews}条）")
                        break
                    elif unchanged_count >= 8:
                        print(f"    ↳ 高度未变化（{unchanged_count}次），但可能还有评论，继续...")
                else:
                    unchanged_count = 0
                    last_height = new_height
                
                scroll_attempts += 1
                if scroll_attempts % 20 == 0:
                    print(f"    ↳ 第{scroll_attempts}次滚动，已加载 {current_reviews} 条评论...")
                    # 每滚动50次检测一次验证码（降低检测频率）
                    if scroll_attempts % 50 == 0:
                        detect_and_wait_for_verification(driver, "评论滚动中")
        
        # 提取评论信息
        print(f"    ↳ 正在提取评论...")
        html = driver.page_source
        doc = pq(html)
        
        # 淘宝/天猫评论的常见选择器（按优先级排序）
        review_selectors = [
            'div.Comment--H5QmJwe9',  # 新版淘宝评论项
            'div[class*="Comment--"]',  # 模糊匹配评论项
            'div.rate-grid',  # 旧版淘宝评论容器
            'div.J_KgRate_ReviewItem',  # 天猫评论
            'div.rate-item',  # 评论项
            'div.commentItem',  # 通用评论项
            'div[class*="comment"]',  # 模糊匹配包含comment的类
        ]
        
        review_items = []
        used_selector = None
        for selector in review_selectors:
            review_items = list(doc(selector).items())
            if len(review_items) > 0:
                used_selector = selector
                print(f"    ↳ 使用选择器 '{selector}' 找到 {len(review_items)} 条评论")
                break
        
        if len(review_items) == 0:
            print(f"    ↳ ⚠️ 警告：未找到评论元素，可能页面结构已变化")
            # 保存页面HTML用于调试（仅在没找到评论时）
            debug_file = f'debug_product_{product_num}.html'
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"    ↳ 已保存页面HTML到 {debug_file}")
            print(f"    ↳ 可以打开此文件，搜索评论文本，查看实际的HTML结构")
            print(f"    ↳ 如果看到评论，请将评论元素的class名称反馈，以便更新选择器")
        
        # 评论去重集合（使用内容hash）
        seen_reviews = set()
        extracted_reviews = []
        skipped_seller_replies = 0
        skipped_duplicates = 0
        missing_purchase_samples = []  # 保存缺失购买记录的样本
        
        # 提取评论内容（支持多种HTML结构）
        for idx, item in enumerate(review_items):
            try:
                # 首先检查是否是商家回复（需要跳过）
                item_html = item.html()
                seller_reply_indicators = [
                    '卖家回复', '店家回复', '商家回复', '掌柜回复',
                    'seller', 'reply', 'shopReply', '回复内容'
                ]
                
                # 检查整个item的文本
                item_text = item.text()
                is_seller_reply = False
                
                # 如果这是一个纯粹的商家回复块（不包含买家评论）
                for indicator in seller_reply_indicators:
                    if indicator in item_text:
                        # 进一步检查：是否有买家评论内容
                        # 如果整个块主要是商家回复，跳过
                        if item_text.startswith(indicator) or len(item_text) < 20:
                            is_seller_reply = True
                            break
                
                if is_seller_reply:
                    skipped_seller_replies += 1
                    continue
                
                # 提取评论用户名（多种可能的选择器）
                username_selectors = [
                    '.userNick--L1gNFN4c',  # 新版淘宝
                    '.header--nYbpA78v .username',
                    '.rate-user-info',
                    '.tb-rate-user',
                    '.user-name',
                    'div[class*="userNick"]',
                    'div[class*="username"]',
                    'span[class*="user"]'
                ]
                username = "匿名用户"
                for selector in username_selectors:
                    username_elem = item.find(selector).text()
                    if username_elem and username_elem.strip():
                        username = username_elem.strip()
                        break
                
                # 提取评论内容（多种可能的选择器）
                content_selectors = [
                    '.content--wJnWgVVD',  # 新版淘宝
                    '.reviewDetail--BmRBV0Aq',
                    '.rate-content',
                    '.J_KgRate_ReviewContent',
                    '.comment-content',
                    'div[class*="content"]',
                    'div[class*="reviewDetail"]'
                ]
                content = ""
                for selector in content_selectors:
                    content_elem = item.find(selector).text()
                    if content_elem and content_elem.strip():
                        content = content_elem.strip()
                        break
                
                # 提取评论时间（扩展选择器）
                time_selectors = [
                    '.date--kEq7WUd3',  # 新版淘宝
                    '.time--xmsIQ6o3',  # 新版淘宝时间
                    '.rate-date',
                    '.tm-rate-date',
                    '.comment-time',
                    'span[class*="date"]',
                    'span[class*="time"]',
                    'div[class*="date"]',
                    'div[class*="time"]',
                    '.header--nYbpA78v span:last-child',  # 头部最后一个span可能是时间
                ]
                review_time = ""
                for selector in time_selectors:
                    time_elem = item.find(selector).text()
                    if time_elem and time_elem.strip():
                        review_time = time_elem.strip()
                        break
                
                # 提取购买记录（规格信息）- 扩展选择器
                purchase_selectors = [
                    '.meta--PLijz6qf',  # ✅ 新版淘宝购买记录（包含时间+规格）- 最优先！
                    '.attribute--wPXM_ggZ',  # 新版淘宝
                    '.subInfo--Y53eXpAX',  # 新版淘宝子信息
                    '.text--YbMC04EH',  # 规格文本
                    'div[class*="meta--"]',  # 模糊匹配meta类
                    '.rate-sku',
                    '.sku-info',
                    '.tm-rate-sku',
                    '.rate-append-sku',
                    'div[class*="attribute"]',
                    'div[class*="sku"]',
                    'div[class*="subInfo"]',
                    'div[class*="text--"]',
                    'span[class*="sku"]',
                ]
                purchase_info = ""
                for selector in purchase_selectors:
                    sku_elem = item.find(selector).text()
                    if sku_elem and sku_elem.strip():
                        purchase_info = sku_elem.strip()
                        break
                
                # 如果没找到规格，尝试更智能的提取方法
                if not purchase_info:
                    try:
                        all_text = item.text()
                        lines = all_text.split('\n')
                        
                        # 方法1：寻找包含常见规格关键词的行
                        for line in lines:
                            line = line.strip()
                            # 排除商家回复内容
                            if any(word in line for word in ['卖家回复', '店家回复', '商家回复', '掌柜回复']):
                                continue
                            # 排除用户名和评论内容
                            if line == username or line == content:
                                continue
                            # 检查规格关键词
                            if any(keyword in line for keyword in ['颜色', '尺码', 'GB', '版本', '规格', '套餐', '型号', 
                                                                     '内存', '存储', '配置', 'RAM', '官方', '标配']):
                                purchase_info = line
                                break
                        
                        # 方法2：如果还没找到，寻找日期格式（如"2025年9月20日"）
                        if not purchase_info:
                            for line in lines:
                                line = line.strip()
                                # 匹配日期格式
                                if re.search(r'\d{4}年\d{1,2}月\d{1,2}日', line) or re.search(r'\d{4}-\d{2}-\d{2}', line):
                                    # 排除商家回复
                                    if not any(word in line for word in ['卖家回复', '店家回复']):
                                        purchase_info = line
                                        break
                        
                        # 方法3：如果还没找到，尝试找包含"/"或"·"分隔符的行（常见规格格式）
                        if not purchase_info:
                            for line in lines:
                                line = line.strip()
                                # 跳过太短或太长的行
                                if len(line) < 5 or len(line) > 150:
                                    continue
                                # 排除用户名、评论内容、商家回复
                                if line == username or line == content:
                                    continue
                                if any(word in line for word in ['卖家回复', '店家回复']):
                                    continue
                                # 包含分隔符且不是评论内容
                                if ('/' in line or '·' in line) and not any(word in line for word in ['很', '非常', '不错', '好', '差']):
                                    purchase_info = line
                                    break
                    except:
                        pass
                
                # 过滤购买记录中的商家回复内容
                if purchase_info:
                    # 如果购买记录中包含商家回复关键词，尝试清理
                    for reply_word in ['卖家回复', '店家回复', '商家回复', '掌柜回复']:
                        if reply_word in purchase_info:
                            # 尝试分割并只保留第一部分（买家信息）
                            parts = purchase_info.split(reply_word)
                            if parts[0].strip():
                                purchase_info = parts[0].strip()
                            else:
                                purchase_info = ""  # 清空，因为可能全是商家回复
                            break
                
                # 合并日期和规格信息（如：2025年9月9日 · 幻夜黑 / 官方标配 / 6GB+128GB）
                # 检查购买记录是否已经包含日期（避免重复）
                has_date_in_purchase = False
                if purchase_info:
                    has_date_in_purchase = bool(re.search(r'\d{4}年\d{1,2}月\d{1,2}日', purchase_info))
                
                if review_time and purchase_info and not has_date_in_purchase:
                    # 购买记录中没有日期，需要合并
                    purchase_info = f"{review_time} · {purchase_info}"
                elif review_time and not purchase_info:
                    # 只有时间，没有规格
                    purchase_info = review_time
                # 如果购买记录已包含日期，保持原样
                
                if content:  # 只保存有内容的评论
                    # 去重检查（基于内容+用户名）
                    review_hash = hash(f"{username}|{content}")
                    if review_hash in seen_reviews:
                        skipped_duplicates += 1
                        continue
                    seen_reviews.add(review_hash)
                    
                    # 如果没有购买记录，保存前5条样本HTML用于调试
                    if not purchase_info and len(missing_purchase_samples) < 5:
                        sample_data = {
                            'index': len(extracted_reviews) + 1,
                            'username': username,
                            'content': content[:50],
                            'html': item.html(),
                            'text': item.text()
                        }
                        missing_purchase_samples.append(sample_data)
                    
                    # 保存评论
                    review_data = {
                        'product_num': product_num,
                        'username': username.strip(),
                        'content': content.strip(),
                        'purchase_info': purchase_info.strip(),
                        'time': review_time.strip()
                    }
                    extracted_reviews.append(review_data)
                    
                    # 显示简要信息（调试模式显示更多信息）
                    if purchase_info or review_time:
                        info_display = f" | 购买: {purchase_info[:30] if purchase_info else '无'}"
                    else:
                        info_display = " | ⚠️未提取到购买记录"
                    
                    if len(extracted_reviews) <= 3 or len(extracted_reviews) % 100 == 0:  # 前3条和每100条显示一次
                        print(f"        [{len(extracted_reviews)}] {username}: {content[:30]}...{info_display}")
                    
            except Exception as e:
                # 单条评论提取失败不影响其他评论
                continue
        
        # 将去重后的评论赋值给reviews
        reviews = extracted_reviews
        
        # 统计信息
        print(f"    ↳ 成功提取 {len(reviews)} 条有效评论")
        if skipped_seller_replies > 0:
            print(f"    ↳ 跳过商家回复块：{skipped_seller_replies} 个")
        if skipped_duplicates > 0:
            print(f"    ↳ 跳过重复评论：{skipped_duplicates} 条")
        if len(reviews) > 0:
            # 统计有购买记录的评论数量
            with_purchase_info = sum(1 for r in reviews if r['purchase_info'])
            with_time = sum(1 for r in reviews if r['time'])
            print(f"    ↳ 包含购买记录：{with_purchase_info} 条（{with_purchase_info*100//len(reviews)}%）")
            print(f"    ↳ 包含时间信息：{with_time} 条（{with_time*100//len(reviews)}%）")
            
            # 如果有缺失购买记录的情况，保存调试文件
            if missing_purchase_samples:
                debug_file = f'debug_missing_purchase_{product_num}.html'
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write('<!-- 缺失购买记录的评论样本 -->\n')
                    f.write('<!-- 请查看这些HTML结构，找到购买记录/规格信息的class名称 -->\n\n')
                    for i, sample in enumerate(missing_purchase_samples):
                        f.write(f'\n\n<!-- ========== 样本 {i+1} ========== -->\n')
                        f.write(f'<!-- 用户名: {sample["username"]} -->\n')
                        f.write(f'<!-- 评论: {sample["content"]} -->\n')
                        f.write(f'<!-- 完整文本:\n{sample["text"]}\n-->\n\n')
                        f.write(sample['html'])
                        f.write('\n\n')
                print(f"    ↳ ⚠️ 已保存 {len(missing_purchase_samples)} 条缺失购买记录的样本到: {debug_file}")
                print(f"    ↳    请打开该文件，查找购买记录（如日期、颜色、规格）所在的class名称")
        
    except Exception as exc:
        print(f"    ↳ 爬取评论失败：{exc}")
        print(f"    ↳ 商品链接：{product_url}")
        print(f"    ↳ 跳过该商品的评论采集")
    
    finally:
        # 关闭详情页标签和评论页标签，返回搜索列表页
        try:
            # 关闭所有除主窗口外的标签页
            if main_window:
                all_windows = driver.window_handles
                for window in all_windows:
                    if window != main_window:
                        try:
                            driver.switch_to.window(window)
                            driver.close()
                        except:
                            pass
                
                # 切回主窗口
                driver.switch_to.window(main_window)
                time.sleep(1)
                print(f"    ↳ 已返回搜索列表页\n")
        except Exception as e:
            print(f"    ↳ 返回主窗口失败：{e}")
    
    return reviews

if __name__ == '__main__':
    # 建立Excel表格
    try:
        ws = op.Workbook()                                  # 创建Workbook
        wb = ws.create_sheet(index=0, title='商品列表')      # 创建商品列表worksheet
        # Excel第一行：表头
        title_list = ['Num', 'title', 'Price', 'Deal', 'Location', 'Shop', 'IsPostFree', 'Title_URL',
                      'Shop_URL', 'Img_URL']
        for i in range(0, len(title_list)):
            wb.cell(row=count, column=i + 1, value=title_list[i])
        count += 1  # 从第二行开始写爬取数据
        
        # 如果启用评论爬取，创建评论Sheet
        if CRAWL_REVIEWS:
            wb_review = ws.create_sheet(index=1, title='商品评论')  # 创建评论worksheet
            review_title_list = ['商品序号', '商品标题', '用户名', '购买记录', '评论内容']
            for i in range(0, len(review_title_list)):
                wb_review.cell(row=review_count, column=i + 1, value=review_title_list[i])
            review_count += 1  # 从第二行开始写评论数据
            print(f"\n已启用评论爬取功能！评论将保存到单独的Sheet中。\n")
            print(f"注意：购买记录列包含时间和规格信息（如：2025年9月20日 · 星空蓝 / 12GB+256GB）\n")
        else:
            wb_review = None  # 不爬取评论时设为None
            print(f"\n未启用评论爬取，仅爬取商品基本信息。\n")
            
    except Exception as exc:
        print("Excel建立失败！Error：{}".format(exc))
 
    # 开始爬取数据
    Crawer_main()
 
    # 删除默认创建的Sheet
    try:
        default_sheet = ws['Sheet']
        ws.remove(default_sheet)
    except:
        pass
    
    # 保存Excel表格
    data = time.strftime('%Y%m%d-%H%M', time.localtime(time.time()))
    Filename = "{}_{}_FromTB.xlsx".format(KEYWORD,data)
    ws.save(filename = Filename)
    print("\n" + "="*60)
    print(f"✓ 文件保存成功：{Filename}")
    print(f"✓ 商品数量：{count - 2} 个")
    if CRAWL_REVIEWS:
        print(f"✓ 评论数量：{review_count - 2} 条")
    print("="*60)
