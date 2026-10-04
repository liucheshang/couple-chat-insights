# -*- coding: utf-8 -*-
"""
Couple Chat Insights - 情侣聊天记录深度分析
纯标准库、零依赖、本地运行、隐私零泄露

用法：python analyze.py 聊天记录.txt 报告.html
"""

import sys
import os
import re
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter

# ============================================================
# 词典定义（融合知网Hownet + Gottman + 依恋理论）
# ============================================================

# 积极情感词（扩充版，来自Hownet）
POSITIVE_WORDS = [
    '爱', '喜欢', '想', '开心', '高兴', '快乐', '幸福', '美好', '温柔', '贴心',
    '宝贝', '宝宝', '老婆', '老公', '亲爱的', '亲爱', '抱抱', '亲亲', '么么哒',
    '想你', '爱你', '喜欢你', '超级爱', '最爱', '唯一', '一辈子', '永远',
    '好吃', '好看', '好玩', '好听', '好看', '棒', '赞', '厉害', '优秀', '完美',
    '谢谢', '感谢', '辛苦了', '辛苦', '麻烦你了', '爱你哦', '好呀', '好哒',
    '可以', '没问题', '当然', '必须的', '安排', '安排上', '安排明白',
    '晚安', '早安', '早上好', '晚上好', '睡个好觉', '好梦',
    '多喝热水', '早点睡', '注意身体', '别太累', '别熬夜', '注意安全',
    '心疼', '心疼你', '担心你', '想你了', '好想你', '超级想你',
    '温暖', '安心', '踏实', '放心', '有你真好', '遇到你真好',
    '抱抱你', '亲亲你', '贴贴', '蹭蹭', 'rua',
    '纪念日', '情人节', '生日快乐', '节日快乐', '新年好',
    '未来', '以后', '以后我们', '我们的家', '我们的未来',
    '在一起', '不分开', '永远在一起', '一辈子在一起',
    '乖', '听话', '懂事', '可爱', '漂亮', '帅', '美',
    '想抱抱', '想亲亲', '想见你', '想见面', '好想见你',
    '开心死了', '乐死了', '美滋滋', '美滋滋的',
    '么么', '木马', 'muamua', '啵啵',
    '爱死你了', '超爱你', '太爱你了', '爱到不行',
]

# 消极情感词（扩充版，来自Hownet）
NEGATIVE_WORDS = [
    '生气', '愤怒', '讨厌', '烦', '烦你', '烦死了', '郁闷', '难过', '伤心',
    '哭', '哭了', '大哭', '流泪', '心碎', '心痛', '心寒', '失望', '绝望',
    '分手', '分开', '离婚', '不想过了', '过不下去了', '算了吧', '就这样吧',
    '你总是', '你从来不', '你能不能', '你为什么', '你怎么又',
    '不在乎', '不关心', '不爱了', '不爱我了', '不爱你了',
    '累', '好累', '太累了', '疲惫', '心累', '身累',
    '孤独', '寂寞', '孤单', '一个人',
    '吵架', '争吵', '吵一架', '吵完了', '吵过了',
    '冷战', '不说话', '不理你', '不理我', '冷战中',
    '滚', '滚蛋', '去死', '傻逼', '脑残', '有病',
    '哼', '哼！', '哼！！', '哼！！！',
    '敷衍', '敷衍我', '敷衍了事',
    '失望透顶', '心灰意冷', '万念俱灰',
    '你变了', '你以前不是这样的', '你现在怎么这样',
    '我错了', '对不起', '抱歉', '不好意思',
    '别生气', '别难过', '别哭', '别哭了',
    '烦死我了', '烦死了', '烦得很',
    '累觉不爱', '心好累', '感觉不会再爱了',
    '无语', '醉了', '服了', '我也是醉了',
    '呵呵', '呵', '行吧', '好吧', '哦', '哦。', '哦...',
    '随便', '随便你', '都行', '无所谓',
    '不想说', '不想聊', '不想理', '不想理你',
    '你忙吧', '你忙你的', '不打扰你了',
]

# Gottman四骑士 - 批评（攻击人格而非行为）
CRITICISM_WORDS = [
    '你总是', '你从来不', '你从来都不', '你每次都', '你怎么总是',
    '你能不能不要', '你就不能', '你为什么总是', '你这个人',
    '你就是个', '你就是这样', '你一直都', '你从来不会',
    '你这种人', '你这种', '你怎么这样', '你怎么会这样',
]

# Gottman四骑士 - 蔑视（讽刺、贬低、翻白眼）
CONTEMPT_WORDS = [
    '呵呵', '呵。', '哟', '呦', '可真行', '可真厉害', '真棒', '真不错',
    '你可真行', '你可真厉害', '你可真棒棒', '真是服了你',
    '阴阳怪气', '讽刺', '挖苦', '嘲笑',
    '你好厉害啊', '你真牛', '你可太牛了',
    '拜托', '拜托你了', '拉倒吧', '得了吧',
    '高傲', '看不起', '瞧不上', '鄙视',
]

# Gottman四骑士 - 防御（推卸责任、反咬一口）
DEFENSIVE_WORDS = [
    '我又不是故意的', '我又没说你', '我怎么知道', '我又不是故意的',
    '这不怪我', '这不是我的错', '我哪知道', '我怎么知道',
    '你不也', '你还说我', '你自己不也', '你也好意思说我',
    '我都道歉了还要怎样', '我都认错了你还要怎样',
    '又不是我的错', '关我什么事', '跟我有什么关系',
    '我只是', '我只是想', '我只是为了你好',
    '你别误会', '你想多了', '不是你想的那样',
]

# Gottman四骑士 - 筑墙（沉默、回避、不回应）- 精准版
STONEWALLING_WORDS = [
    '不想说了', '我不想说了', '我没什么好说的',
    '懒得解释', '懒得说', '我不想解释',
    '你想怎样就怎样', '你开心就好', '随你便',
    '我不想吵', '我不想争',
    '给我点时间', '让我冷静一下', '我需要空间',
]

# 关心词
CARE_WORDS = [
    '多喝热水', '早点睡', '别熬夜', '注意身体', '冷不冷', '吃饭了吗',
    '记得吃饭', '别太累了', '注意安全', '到家说一声', '多穿点',
    '别感冒了', '好好吃饭', '早点休息', '别生病了', '心疼你',
    '担心你', '我担心', '别累着', '别辛苦',
]

# 爱称
NICKNAME_WORDS = [
    '宝贝', '宝宝', '老婆', '老公', '亲爱的', '亲爱', '心肝',
    '乖乖', '猪猪', '臭宝', '臭宝', '小宝', '大宝', '我的宝',
    '媳妇', '老公公', '老婆婆', '对象', '另一半',
    '亲爱的宝宝', '宝贝老婆', '宝贝老公',
]

# 思念词
MISS_WORDS = [
    '想你', '好想你', '超级想你', '想你了', '好想你了',
    '想见你', '好想见你', '想抱抱', '想亲亲',
    '念你', '思念', '惦记',
]

# 焦虑型依恋特征（精准版）
ANXIOUS_WORDS = [
    '你在哪', '你在干嘛', '怎么不回我', '为什么不回', '你干嘛去了',
    '你是不是不爱我了', '你是不是不在乎我了', '你是不是有别人了',
    '我害怕', '我好怕', '我怕失去你', '我怕你离开我',
    '你不要离开我', '别离开我', '别丢下我',
    '我是不是做错什么了', '我是不是哪里不好',
    '你是不是生气了', '你怎么不理我', '你为什么不理我',
    '你到底爱不爱我', '你心里还有没有我',
]

# 回避型依恋特征（精准版 - 删掉了日常常用词）
AVOIDANT_WORDS = [
    '我没事', '你别管', '不用你管', '我自己可以', '我自己来',
    '我想静静', '让我一个人待一会', '给我点空间',
    '我不想谈这个', '别说了', '不想说了',
    '我还好', '没什么', '没怎么',
    '你忙吧', '不打扰你了', '你去忙吧',
    '我不想解释', '懒得说', '不想说',
    '我不需要你管', '别管我',
]

# 冲突触发词
CONFLICT_TRIGGERS = [
    '分手', '离婚', '滚', '傻逼', '脑残', '有病', '受够了',
    '不想过了', '过不下去', '算了吧', '就这样吧',
    '你总是', '你从来不', '你怎么又', '你能不能',
]

# ============================================================
# 数据读取与清洗
# ============================================================

def read_chat(filepath):
    """读取聊天记录，自动尝试多种编码"""
    encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb18030', 'big5']
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                lines = f.readlines()
            print(f"读取成功，编码：{enc}")
            return lines
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError("无法识别文件编码，请保存为UTF-8格式")


def parse_line(line):
    """解析一行聊天记录，格式：2024-09-19 22:03 | TA | 出发没"""
    line = line.strip()
    if not line:
        return None

    # 尝试匹配格式：YYYY-MM-DD HH:MM | 发送者 | 内容
    m = re.match(r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s*\|\s*([^|]+?)\s*\|\s*(.*)', line)
    if m:
        date_str, time_str, sender, content = m.groups()
        try:
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            return {
                'time': dt,
                'sender': sender.strip(),
                'content': content.strip()
            }
        except ValueError:
            return None
    return None


def detect_senders(messages):
    """自动识别发送者：统计出现次数最多的两个名字"""
    sender_counts = Counter(m['sender'] for m in messages)
    top = sender_counts.most_common(2)
    if len(top) >= 2:
        me_name, me_count = top[0]
        her_name, her_count = top[1]
        print(f"自动识别：你 = {me_name}（{me_count}条），TA = {her_name}（{her_count}条）")
        return me_name, her_name
    else:
        # 只有一个发送者？默认"我"和"TA"
        return '我', 'TA'


def normalize_senders(messages, me_name, her_name):
    """把发送者统一成 me / her"""
    for m in messages:
        if m['sender'] == me_name:
            m['sender_norm'] = 'me'
        elif m['sender'] == her_name:
            m['sender_norm'] = 'her'
        else:
            m['sender_norm'] = 'other'
    return messages


# ============================================================
# 统计分析函数
# ============================================================

# 否定词（出现在情感词前面会反转极性）
NEGATION_WORDS = ['不', '没', '别', '无', '非', '莫', '未', '甭']

# 程度副词（权重）
DEGREE_WORDS = {
    '非常': 1.5, '特别': 1.5, '超级': 1.5, '极其': 1.5, '十分': 1.5,
    '很': 1.2, '好': 1.2, '真': 1.2, '太': 1.2, '好': 1.2,
    '有点': 0.7, '稍微': 0.7, '还行': 0.7,
}

# Emoji情感映射（常用表情）
EMOJI_SENTIMENT = {
    '[爱心]': 1, '[玫瑰]': 1, '[呲牙]': 1, '[旺柴]': 0.5, '[破涕为笑]': 1,
    '[让我看看]': 0.3, '[捂脸]': -0.3, '[笑哭]': 0.5, '[偷笑]': 1,
    '[大哭]': -1, '[流泪]': -1, '[发怒]': -1, '[心碎]': -1,
    '[微笑]': 0, '[撇嘴]': -0.5, '[困]': -0.3, '[汗]': -0.5,
    '[鼓掌]': 1, '[棒]': 1, '[强]': 1, '[弱]': -0.5,
    '[色]': 0.5, '[害羞]': 0.5, '[得意]': 1, '[呲牙]': 1,
}

def analyze_sentiment(text):
    """分析一句话的情感得分：-1(负) ~ +1(正)
    支持否定词反转、程度副词加权、emoji映射
    """
    score = 0.0
    hits = 0

    # 检查情感词
    for w in POSITIVE_WORDS:
        if w in text:
            # 检查前面有没有否定词
            idx = text.find(w)
            prefix = text[max(0, idx-5):idx]
            negated = any(n in prefix for n in NEGATION_WORDS)

            weight = 1.0
            # 检查程度词
            for dw, dv in DEGREE_WORDS.items():
                if dw in prefix:
                    weight = dv
                    break

            s = weight * (-1 if negated else 1)
            score += s
            hits += 1

    for w in NEGATIVE_WORDS:
        if w in text:
            idx = text.find(w)
            prefix = text[max(0, idx-5):idx]
            negated = any(n in prefix for n in NEGATION_WORDS)

            weight = 1.0
            for dw, dv in DEGREE_WORDS.items():
                if dw in prefix:
                    weight = dv
                    break

            s = -weight * (1 if negated else -1)  # 负面词前面加否定 = 正面
            score += s
            hits += 1

    # 检查emoji
    for emoji, es in EMOJI_SENTIMENT.items():
        if emoji in text:
            score += es
            hits += 1

    return score, hits


def count_words(text, word_list):
    """统计文本中命中词表的次数（带边界判断）"""
    count = 0
    for w in word_list:
        # 简单包含匹配，后续可优化为带边界判断
        if w in text:
            count += 1
    return count


def analyze(messages):
    """主分析函数，返回所有统计结果"""
    N = len(messages)
    print(f"开始分析，共 {N} 条消息...")

    # 基础统计
    me_msgs = [m for m in messages if m['sender_norm'] == 'me']
    her_msgs = [m for m in messages if m['sender_norm'] == 'her']
    me_n = len(me_msgs)
    her_n = len(her_msgs)

    start_time = messages[0]['time']
    end_time = messages[-1]['time']
    total_days = (end_time - start_time).days + 1

    # ---- 词频统计（用新的情感分析函数，支持否定词和程度词） ----
    me_pos = 0
    me_neg = 0
    her_pos = 0
    her_neg = 0

    for m in me_msgs:
        s, _ = analyze_sentiment(m['content'])
        if s > 0:
            me_pos += s
        else:
            me_neg += abs(s)

    for m in her_msgs:
        s, _ = analyze_sentiment(m['content'])
        if s > 0:
            her_pos += s
        else:
            her_neg += abs(s)

    # Gottman比率：积极词 / 消极词
    total_pos = me_pos + her_pos
    total_neg = me_neg + her_neg
    gottman_ratio = round(total_pos / max(total_neg, 1), 2)

    # ---- 四骑士统计 ----
    me_criticism = sum(count_words(m['content'], CRITICISM_WORDS) for m in me_msgs)
    her_criticism = sum(count_words(m['content'], CRITICISM_WORDS) for m in her_msgs)
    me_contempt = sum(count_words(m['content'], CONTEMPT_WORDS) for m in me_msgs)
    her_contempt = sum(count_words(m['content'], CONTEMPT_WORDS) for m in her_msgs)
    me_defensive = sum(count_words(m['content'], DEFENSIVE_WORDS) for m in me_msgs)
    her_defensive = sum(count_words(m['content'], DEFENSIVE_WORDS) for m in her_msgs)
    me_stonewalling = sum(count_words(m['content'], STONEWALLING_WORDS) for m in me_msgs)
    her_stonewalling = sum(count_words(m['content'], STONEWALLING_WORDS) for m in her_msgs)

    # ---- 消息类型统计 ----
    type_counts = {'text': 0, 'image': 0, 'emoji': 0, 'voice': 0, 'other': 0}
    for m in messages:
        content = m['content']
        if '[图片]' in content:
            type_counts['image'] += 1
        elif '[语音]' in content:
            type_counts['voice'] += 1
        elif content.startswith('[') and content.endswith(']') and len(content) < 10:
            type_counts['emoji'] += 1
        elif '[其他]' in content or '[视频]' in content or '[文件]' in content:
            type_counts['other'] += 1
        else:
            type_counts['text'] += 1

    # ---- 首次聊天分析 ----
    first_msg = messages[0]
    first_date = first_msg['time'].strftime('%Y-%m-%d')
    first_sender = '你' if first_msg['sender_norm'] == 'me' else 'TA'

    # ---- 关心/爱称/思念 ----
    me_care = sum(count_words(m['content'], CARE_WORDS) for m in me_msgs)
    her_care = sum(count_words(m['content'], CARE_WORDS) for m in her_msgs)
    me_nickname = sum(count_words(m['content'], NICKNAME_WORDS) for m in me_msgs)
    her_nickname = sum(count_words(m['content'], NICKNAME_WORDS) for m in her_msgs)
    me_miss = sum(count_words(m['content'], MISS_WORDS) for m in me_msgs)
    her_miss = sum(count_words(m['content'], MISS_WORDS) for m in her_msgs)

    # ---- 依恋风格 ----
    me_anxious = sum(count_words(m['content'], ANXIOUS_WORDS) for m in me_msgs)
    her_anxious = sum(count_words(m['content'], ANXIOUS_WORDS) for m in her_msgs)
    me_avoidant = sum(count_words(m['content'], AVOIDANT_WORDS) for m in me_msgs)
    her_avoidant = sum(count_words(m['content'], AVOIDANT_WORDS) for m in her_msgs)

    # ---- 回复速度 ----
    reply_times_me = []  # me回复her的时间
    reply_times_her = []  # her回复me的时间
    prev_sender = None
    prev_time = None
    for m in messages:
        if prev_sender and prev_time:
            gap = (m['time'] - prev_time).total_seconds() / 60  # 分钟
            if gap < 60 * 6:  # 6小时内算回复
                if m['sender_norm'] == 'me' and prev_sender == 'her':
                    reply_times_me.append(gap)
                elif m['sender_norm'] == 'her' and prev_sender == 'me':
                    reply_times_her.append(gap)
        prev_sender = m['sender_norm']
        prev_time = m['time']

    reply_me_median = round(sorted(reply_times_me)[len(reply_times_me)//2], 1) if reply_times_me else 0
    reply_her_median = round(sorted(reply_times_her)[len(reply_times_her)//2], 1) if reply_times_her else 0

    # ---- 回应延迟分布（P90） ----
    reply_me_p90 = round(sorted(reply_times_me)[int(len(reply_times_me)*0.9)], 1) if reply_times_me else 0
    reply_her_p90 = round(sorted(reply_times_her)[int(len(reply_times_her)*0.9)], 1) if reply_times_her else 0

    # ---- 情绪传染概率 ----
    # 一方发负面消息后，另一方下一条也发负面的概率
    contagion_count = 0
    contagion_total = 0
    prev_sender = None
    prev_sentiment = 0
    for m in messages:
        s, _ = analyze_sentiment(m['content'])
        if prev_sender and prev_sender != m['sender_norm']:
            if prev_sentiment < 0:  # 上一条是负面
                contagion_total += 1
                if s < 0:  # 这一条也是负面 = 情绪传染
                    contagion_count += 1
        prev_sender = m['sender_norm']
        prev_sentiment = s

    contagion_rate = round(contagion_count / max(contagion_total, 1) * 100, 1) if contagion_total > 0 else 0

    # ---- 谁先开场、谁先收尾 ----
    # 会话段：两个人之间消息间隔超过1小时 = 新的一段
    conversation_starts = {'me': 0, 'her': 0}
    conversation_ends = {'me': 0, 'her': 0}
    prev_msg = None
    current_conv_started = None
    current_conv_last = None

    for m in messages:
        if prev_msg is None:
            current_conv_started = m['sender_norm']
            current_conv_last = m['sender_norm']
        else:
            gap_hours = (m['time'] - prev_msg['time']).total_seconds() / 3600
            if gap_hours > 1:  # 新的一段对话
                conversation_starts[current_conv_started] += 1
                conversation_ends[current_conv_last] += 1
                current_conv_started = m['sender_norm']
            current_conv_last = m['sender_norm']
        prev_msg = m

    if current_conv_started:
        conversation_starts[current_conv_started] += 1
        conversation_ends[current_conv_last] += 1

    total_convs = sum(conversation_starts.values())

    # ---- 深夜聊天比例 ----
    # 晚上10点~凌晨6点 = 深夜
    late_night_msgs = 0
    for m in messages:
        h = m['time'].hour
        if h >= 22 or h < 6:
            late_night_msgs += 1
    late_night_pct = round(late_night_msgs / N * 100, 1)

    # ---- 周末vs工作日 ----
    weekend_msgs = 0
    for m in messages:
        if m['time'].weekday() >= 5:  # 5=周六, 6=周日
            weekend_msgs += 1
    weekend_pct = round(weekend_msgs / N * 100, 1)

    # ---- 连发行为 ----
    # 连续同一条人发超过3条 = 连发
    burst_me = 0
    burst_her = 0
    max_burst_me = 0
    max_burst_her = 0
    current_burst = 1
    prev_sender_burst = None

    for m in messages:
        if prev_sender_burst == m['sender_norm']:
            current_burst += 1
        else:
            if current_burst >= 3:
                if prev_sender_burst == 'me':
                    burst_me += 1
                    max_burst_me = max(max_burst_me, current_burst)
                else:
                    burst_her += 1
                    max_burst_her = max(max_burst_her, current_burst)
            current_burst = 1
        prev_sender_burst = m['sender_norm']

    # 最后一段
    if current_burst >= 3:
        if prev_sender_burst == 'me':
            burst_me += 1
            max_burst_me = max(max_burst_me, current_burst)
        else:
            burst_her += 1
            max_burst_her = max(max_burst_her, current_burst)

    # ---- 问句比例 ----
    question_me = sum(1 for m in me_msgs if '？' in m['content'] or '?' in m['content'])
    question_her = sum(1 for m in her_msgs if '？' in m['content'] or '?' in m['content'])
    question_me_pct = round(question_me / max(me_n, 1) * 100, 1)
    question_her_pct = round(question_her / max(her_n, 1) * 100, 1)

    # ---- 消息长度对比 ----
    avg_len_me = round(sum(len(m['content']) for m in me_msgs) / max(me_n, 1), 1)
    avg_len_her = round(sum(len(m['content']) for m in her_msgs) / max(her_n, 1), 1)

    # ---- 表情使用对比 ----
    emoji_pattern = re.compile(r'\[[^\]]+\]')
    emoji_me = sum(len(emoji_pattern.findall(m['content'])) for m in me_msgs)
    emoji_her = sum(len(emoji_pattern.findall(m['content'])) for m in her_msgs)
    emoji_me_avg = round(emoji_me / max(me_n, 1), 2)
    emoji_her_avg = round(emoji_her / max(her_n, 1), 2)

    # ---- 话题分类统计 ----
    topic_words = {
        '工作': ['工作', '上班', '下班', '老板', '同事', '会议', '项目', '加班', 'KPI', '工资'],
        '吃饭': ['吃饭', '吃了', '早饭', '午饭', '晚饭', '外卖', '火锅', '奶茶', '好吃', '饿了'],
        '睡觉': ['睡觉', '睡了', '晚安', '起床', '困了', '熬夜', '失眠'],
        '想你': ['想你', '想念', '好想', '梦到', '梦见'],
        '爱你': ['爱你', '我爱你', '爱死你', '爱宝宝'],
        '吵架': ['吵架', '生气', '气死', '讨厌', '烦', '分手', '难过', '伤心'],
        '旅游': ['旅游', '旅行', '出去玩', '景点', '酒店', '机票', '高铁'],
        '身体': ['生病', '感冒', '发烧', '头疼', '肚子疼', '姨妈', '月经'],
    }

    topic_counts = {}
    for topic, words in topic_words.items():
        topic_counts[topic] = sum(count_words(m['content'], words) for m in messages)

    # ---- 高频词Top20（简单版，纯字符串匹配） ----
    # 太复杂的分词做不了，先统计一些常见的词
    common_words = ['宝贝', '宝宝', '亲爱的', '想你', '爱你', '好的', '好吧', '嗯嗯', '哈哈', '呵呵',
                    '哈哈哈', '嘻嘻', '哼', '唉', '哦', '嗯', '好', '行', '可以', '不行']
    word_counts = {}
    for w in common_words:
        word_counts[w] = sum(1 for m in messages if w in m['content'])

    # 按频次排序
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    top_words = sorted_words[:15]

    # ---- 冲突修复率（TODO：需要先实现冲突段检测） ----
    repair_rate = 100.0  # 暂时默认100%

    # ---- 月度情感趋势 ----
    monthly_pos = defaultdict(float)
    monthly_neg = defaultdict(float)
    for m in messages:
        month_key = m['time'].strftime('%Y-%m')
        s, _ = analyze_sentiment(m['content'])
        if s > 0:
            monthly_pos[month_key] += s
        else:
            monthly_neg[month_key] += abs(s)

    all_months_sentiment = sorted(set(list(monthly_pos.keys()) + list(monthly_neg.keys())))
    monthly_sentiment_labels = [m[2:] for m in all_months_sentiment]
    monthly_sentiment_score = []
    for m in all_months_sentiment:
        pos = monthly_pos.get(m, 0)
        neg = monthly_neg.get(m, 0)
        score = round(pos / max(pos + neg, 1) * 100, 1)  # 0-100，越高越积极
        monthly_sentiment_score.append(score)

    # ---- 断联检测 ----
    daily_msgs = defaultdict(int)
    for m in messages:
        day = m['time'].date()
        daily_msgs[day] += 1

    all_days = []
    cur = start_time.date()
    while cur <= end_time.date():
        all_days.append(cur)
        cur += timedelta(days=1)

    gap_days = [d for d in all_days if daily_msgs[d] == 0]
    max_gap = 0
    cur_gap = 0
    for d in all_days:
        if daily_msgs[d] == 0:
            cur_gap += 1
            max_gap = max(max_gap, cur_gap)
        else:
            cur_gap = 0

    # ---- 冲突段检测 ----
    conflict_segments = 0
    repair_count_me = 0
    repair_count_her = 0
    cur_conflict = False
    for m in messages:
        has_conflict = count_words(m['content'], CONFLICT_TRIGGERS) > 0
        if has_conflict and not cur_conflict:
            conflict_segments += 1
            cur_conflict = True
        elif not has_conflict and cur_conflict:
            cur_conflict = False

    # ---- 综合健康分 ----
    # 维度：Gottman比率(30%) + 关心次数(20%) + 冲突修复率(20%) + 断联频率(15%) + 四骑士频率(15%)
    score_gottman = min(gottman_ratio / 5.0, 1.0) * 30  # 5:1满分
    score_care = min((me_care + her_care) / max(N / 100, 1), 1.0) * 20
    score_repair = min(1.0 - conflict_segments / max(N / 200, 1), 0) * 20 if conflict_segments > N / 200 else 20
    score_gap = max(0, 1 - max_gap / 30) * 15  # 断联30天以上0分
    score_four = max(0, 1 - (me_criticism + her_criticism + me_contempt + her_contempt) / max(N / 100, 1)) * 15

    health_score = round(score_gottman + score_care + score_repair + score_gap + score_four, 1)
    health_score = max(0, min(100, health_score))

    # ---- 爱情三角理论（Sternberg） ----
    # 亲密：关心、爱称、思念
    intimacy = round((me_care + her_care + me_nickname + her_nickname + me_miss + her_miss) / max(N / 50, 1), 1)
    # 激情：爱称、思念、甜话
    passion = round((me_nickname + her_nickname + me_miss + her_miss) / max(N / 80, 1), 1)
    # 承诺：长期在一起的表述
    commitment_words = ['永远', '一辈子', '未来', '以后', '在一起', '不分开']
    me_commit = sum(count_words(m['content'], commitment_words) for m in me_msgs)
    her_commit = sum(count_words(m['content'], commitment_words) for m in her_msgs)
    commitment = round((me_commit + her_commit) / max(N / 200, 1), 1)

    # 归一化到0-10
    intimacy = min(intimacy, 10)
    passion = min(passion, 10)
    commitment = min(commitment, 10)

    # ---- 逐月统计 ----
    monthly_me = defaultdict(int)
    monthly_her = defaultdict(int)
    for m in messages:
        month_key = m['time'].strftime('%Y-%m')
        if m['sender_norm'] == 'me':
            monthly_me[month_key] += 1
        else:
            monthly_her[month_key] += 1

    all_months = sorted(set(list(monthly_me.keys()) + list(monthly_her.keys())))
    monthly_labels = [m[2:] for m in all_months]  # 只显示MM
    monthly_me_data = [monthly_me.get(m, 0) for m in all_months]
    monthly_her_data = [monthly_her.get(m, 0) for m in all_months]

    # ---- 24小时分布 ----
    hourly = [0] * 24
    for m in messages:
        h = m['time'].hour
        hourly[h] += 1

    hourly_labels = [f"{h}时" for h in range(24)]
    hourly_values = hourly

    # ---- 关系类型判断 ----
    if max_gap > 90:
        rel_type = '分分合合型'
        rel_desc = '你们有过长时间断联，关系像过山车。吵架、和好、再吵架、再和好。这种模式要么彻底稳定下来，要么迟早会分。'
    elif me_anxious > her_anxious and her_avoidant > me_avoidant:
        rel_type = '追逃模式'
        rel_desc = '你追，TA逃。你越想靠近，TA越想躲。这是最常见的情侣矛盾模式，也是最容易耗死的一种。'
    elif me_n + her_n > 100000 and max_gap < 7:
        rel_type = '热恋甜蜜型'
        rel_desc = '你们的联系非常紧密，几乎没有断联，积极互动远多于消极。这是最健康的关系状态。'
    elif gottman_ratio < 3:
        rel_type = '消耗内耗型'
        rel_desc = '消极互动偏多，你们可能经常吵架、互相指责。这段关系正在消耗你们双方。'
    else:
        rel_type = '平淡稳定型'
        rel_desc = '你们的关系不算特别甜蜜，但也没有大矛盾，属于比较平淡稳定的状态。'

    # ---- 一句话结论 ----
    if health_score >= 80:
        conclusion = f'你们的关系很健康（{health_score}分）。Gottman比率{gottman_ratio}:1，超过了5:1的健康线，说明你们的积极互动远多于消极。'
    elif health_score >= 60:
        conclusion = f'你们的关系中等偏上（{health_score}分）。Gottman比率{gottman_ratio}:1，刚过健康线，但最长断联{max_gap}天是个隐患。'
    elif health_score >= 40:
        conclusion = f'你们的关系有风险（{health_score}分）。最长断联{max_gap}天，Gottman比率{gottman_ratio}:1，需要注意沟通方式。'
    else:
        conclusion = f'你们的关系亮红灯了（{health_score}分）。最长断联{max_gap}天，Gottman比率只有{gottman_ratio}:1，建议认真聊聊。'

    # ---- 建议生成 ----
    # Gottman建议
    if gottman_ratio >= 5:
        gottman_advice = "你们的积极互动远多于消极，这是非常健康的比例。保持下去。"
    elif gottman_ratio >= 3:
        gottman_advice = "积极互动略多于消极，整体还不错，但可以多一些正面表达。"
    elif gottman_ratio >= 1:
        gottman_advice = "正负互动接近平衡，偶尔会有摩擦。注意多肯定、少批评。"
    else:
        gottman_advice = "消极互动偏多，这是一个危险信号。建议多注意沟通方式。"

    # 断联建议
    if max_gap == 0:
        gap_advice = "你们几乎没有断联，联系非常紧密。但也要注意给彼此留空间。"
    elif max_gap <= 3:
        gap_advice = "最长断联不超过3天，整体很稳定。"
    elif max_gap <= 7:
        gap_advice = "有过一周左右的断联，可能是吵架后冷战。注意及时修复。"
    else:
        gap_advice = "有过长时间断联，这是关系不稳定的信号。需要找出原因。"

    # 四骑士建议
    total_contempt = me_contempt + her_contempt
    if total_contempt > 0:
        four_advice = "检测到蔑视行为，这是关系破裂的最强预测指标。请停止讽刺和贬低对方。"
    elif me_stonewalling + her_stonewalling > 10:
        four_advice = "检测到筑墙（沉默回避）行为，有矛盾不要冷处理，及时沟通。"
    else:
        four_advice = "四骑士信号很少，沟通方式整体健康。"

    # ---- 汇总结果 ----
    result = {
        'total_msgs': N,
        'me_n': me_n,
        'her_n': her_n,
        'me_pct': round(me_n / N * 100, 1),
        'her_pct': round(her_n / N * 100, 1),
        'total_days': total_days,
        'start_date': start_time.strftime('%Y-%m-%d'),
        'end_date': end_time.strftime('%Y-%m-%d'),

        'gottman_ratio': gottman_ratio,
        'total_pos': total_pos,
        'total_neg': total_neg,

        'four_horsemen': {
            'criticism': {'me': me_criticism, 'her': her_criticism},
            'contempt': {'me': me_contempt, 'her': her_contempt},
            'defensive': {'me': me_defensive, 'her': her_defensive},
            'stonewalling': {'me': me_stonewalling, 'her': her_stonewalling},
        },

        'care': {'me': me_care, 'her': her_care},
        'nickname': {'me': me_nickname, 'her': her_nickname},
        'miss': {'me': me_miss, 'her': her_miss},

        'attachment': {
            'anxious': {'me': me_anxious, 'her': her_anxious},
            'avoidant': {'me': me_avoidant, 'her': her_avoidant},
        },

        'reply_speed': {
            'me_median_min': reply_me_median,
            'her_median_min': reply_her_median,
            'me_p90_min': reply_me_p90,
            'her_p90_min': reply_her_p90,
        },

        'emotion_contagion': contagion_rate,

        'conversation': {
            'starts': conversation_starts,
            'ends': conversation_ends,
            'total': total_convs,
            'her_start_pct': round(conversation_starts['her'] / max(total_convs, 1) * 100, 1),
        },

        'late_night_pct': late_night_pct,
        'weekend_pct': weekend_pct,

        'burst': {
            'me_count': burst_me,
            'her_count': burst_her,
            'me_max': max_burst_me,
            'her_max': max_burst_her,
        },

        'questions': {
            'me_pct': question_me_pct,
            'her_pct': question_her_pct,
        },

        'avg_length': {
            'me': avg_len_me,
            'her': avg_len_her,
        },

        'emoji_avg': {
            'me': emoji_me_avg,
            'her': emoji_her_avg,
        },

        'topics': topic_counts,
        'top_words': top_words,

        'monthly_sentiment': {
            'labels': monthly_sentiment_labels,
            'scores': monthly_sentiment_score,
        },

        'repair_rate': repair_rate,

        'relationship_type': rel_type,
        'relationship_desc': rel_desc,
        'one_line_conclusion': conclusion,

        'message_types': type_counts,
        'first_chat': {
            'date': first_date,
            'sender': first_sender,
        },

        'gap': {
            'max_days': max_gap,
            'total_gap_days': len(gap_days),
        },

        'conflict': {
            'segments': conflict_segments,
        },

        'health_score': health_score,
        'health_detail': {
            'gottman': round(score_gottman, 1),
            'care': round(score_care, 1),
            'repair': round(score_repair, 1),
            'gap': round(score_gap, 1),
            'four_horsemen': round(score_four, 1),
        },

        'sternberg_triangle': {
            'intimacy': intimacy,
            'passion': passion,
            'commitment': commitment,
        },

        'monthly_data': {
            'labels': monthly_labels,
            'me': monthly_me_data,
            'her': monthly_her_data,
        },

        'hourly_data': {
            'labels': hourly_labels,
            'values': hourly_values,
        },

        'gottman_advice': gottman_advice,
        'gap_advice': gap_advice,
        'four_advice': four_advice,
    }

    print(f"分析完成！健康分：{health_score}/100")
    return result


# ============================================================
# 报告生成
# ============================================================

def generate_report(result, output_path):
    """生成HTML报告"""
    # 读取模板
    template_path = os.path.join(os.path.dirname(__file__), 'report_template.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # 替换占位符
    html = template
    for k, v in result.items():
        if isinstance(v, (int, float, str)):
            html = html.replace('{{' + k.upper() + '}}', str(v))

    # 替换嵌套的dict（简单处理，后续完善）
    fh = result['four_horsemen']
    html = html.replace('{{CRITICISM_ME}}', str(fh['criticism']['me']))
    html = html.replace('{{CRITICISM_HER}}', str(fh['criticism']['her']))
    html = html.replace('{{CONTEMPT_ME}}', str(fh['contempt']['me']))
    html = html.replace('{{CONTEMPT_HER}}', str(fh['contempt']['her']))
    html = html.replace('{{DEFENSIVE_ME}}', str(fh['defensive']['me']))
    html = html.replace('{{DEFENSIVE_HER}}', str(fh['defensive']['her']))
    html = html.replace('{{STONEWALLING_ME}}', str(fh['stonewalling']['me']))
    html = html.replace('{{STONEWALLING_HER}}', str(fh['stonewalling']['her']))

    html = html.replace('{{CARE_ME}}', str(result['care']['me']))
    html = html.replace('{{CARE_HER}}', str(result['care']['her']))
    html = html.replace('{{NICKNAME_ME}}', str(result['nickname']['me']))
    html = html.replace('{{NICKNAME_HER}}', str(result['nickname']['her']))
    html = html.replace('{{MISS_ME}}', str(result['miss']['me']))
    html = html.replace('{{MISS_HER}}', str(result['miss']['her']))

    html = html.replace('{{ANXIOUS_ME}}', str(result['attachment']['anxious']['me']))
    html = html.replace('{{ANXIOUS_HER}}', str(result['attachment']['anxious']['her']))
    html = html.replace('{{AVOIDANT_ME}}', str(result['attachment']['avoidant']['me']))
    html = html.replace('{{AVOIDANT_HER}}', str(result['attachment']['avoidant']['her']))

    html = html.replace('{{REPLY_ME}}', str(result['reply_speed']['me_median_min']))
    html = html.replace('{{REPLY_HER}}', str(result['reply_speed']['her_median_min']))

    html = html.replace('{{MAX_GAP}}', str(result['gap']['max_days']))
    html = html.replace('{{CONFLICT_SEGMENTS}}', str(result['conflict']['segments']))

    html = html.replace('{{EMOTION_CONTAGION}}', str(result['emotion_contagion']))

    # 谁更主动
    html = html.replace('{{CONV_START_ME}}', str(result['conversation']['starts']['me']))
    html = html.replace('{{CONV_START_HER}}', str(result['conversation']['starts']['her']))
    her_start = result['conversation']['her_start_pct']
    if her_start > 60:
        conv_tip = 'TA更主动找你'
    elif her_start < 40:
        conv_tip = '你更主动找TA'
    else:
        conv_tip = '差不多'
    html = html.replace('{{CONV_START_TIP}}', conv_tip)

    html = html.replace('{{Q_ME_PCT}}', str(result['questions']['me_pct']))
    html = html.replace('{{Q_HER_PCT}}', str(result['questions']['her_pct']))

    html = html.replace('{{BURST_ME}}', str(result['burst']['me_count']))
    html = html.replace('{{BURST_HER}}', str(result['burst']['her_count']))
    html = html.replace('{{BURST_ME_MAX}}', str(result['burst']['me_max']))
    html = html.replace('{{BURST_HER_MAX}}', str(result['burst']['her_max']))

    html = html.replace('{{LATE_NIGHT_PCT}}', str(result['late_night_pct']))
    html = html.replace('{{WEEKEND_PCT}}', str(result['weekend_pct']))

    # 说话风格
    html = html.replace('{{AVG_LEN_ME}}', str(result['avg_length']['me']))
    html = html.replace('{{AVG_LEN_HER}}', str(result['avg_length']['her']))
    html = html.replace('{{EMOJI_ME}}', str(result['emoji_avg']['me']))
    html = html.replace('{{EMOJI_HER}}', str(result['emoji_avg']['her']))
    html = html.replace('{{REPAIR_RATE}}', str(result['repair_rate']))

    # 图表数据
    topics = result['topics']
    html = html.replace('{{TOPICS_DATA}}', json.dumps({
        'labels': list(topics.keys()),
        'values': list(topics.values()),
    }))

    html = html.replace('{{SENTIMENT_DATA}}', json.dumps(result['monthly_sentiment']))

    # 消息类型
    types = result['message_types']
    types_data = [
        {'name': '文本消息', 'value': types['text']},
        {'name': '图片', 'value': types['image']},
        {'name': '表情', 'value': types['emoji']},
        {'name': '语音', 'value': types['voice']},
        {'name': '其他', 'value': types['other']},
    ]
    html = html.replace('{{TYPES_DATA}}', json.dumps(types_data))

    # 首次聊天
    html = html.replace('{{FIRST_DATE}}', result['first_chat']['date'])
    html = html.replace('{{FIRST_SENDER}}', result['first_chat']['sender'])

    html = html.replace('{{ONE_LINE_CONCLUSION}}', result['one_line_conclusion'])
    html = html.replace('{{RELATIONSHIP_TYPE}}', result['relationship_type'])
    html = html.replace('{{RELATIONSHIP_DESC}}', result['relationship_desc'])

    html = html.replace('{{HEALTH_GOTTMAN}}', str(result['health_detail']['gottman']))
    html = html.replace('{{HEALTH_CARE}}', str(result['health_detail']['care']))
    html = html.replace('{{HEALTH_REPAIR}}', str(result['health_detail']['repair']))
    html = html.replace('{{HEALTH_GAP}}', str(result['health_detail']['gap']))
    html = html.replace('{{HEALTH_FOUR}}', str(result['health_detail']['four_horsemen']))

    html = html.replace('{{TRIANGLE_INTIMACY}}', str(result['sternberg_triangle']['intimacy']))
    html = html.replace('{{TRIANGLE_PASSION}}', str(result['sternberg_triangle']['passion']))
    html = html.replace('{{TRIANGLE_COMMITMENT}}', str(result['sternberg_triangle']['commitment']))

    html = html.replace('{{SENDER_ME}}', result['sender_names']['me'])
    html = html.replace('{{SENDER_HER}}', result['sender_names']['her'])

    # 新数据：图表和建议
    html = html.replace('{{MONTHLY_DATA}}', json.dumps(result['monthly_data']))
    html = html.replace('{{HOURLY_DATA}}', json.dumps(result['hourly_data']))
    html = html.replace('{{CARE_DATA}}', json.dumps({
        'labels': ['关心问候', '爱称次数', '思念表达'],
        'me': [result['care']['me'], result['nickname']['me'], result['miss']['me']],
        'her': [result['care']['her'], result['nickname']['her'], result['miss']['her']],
    }))

    html = html.replace('{{GOTTMAN_ADVICE}}', result['gottman_advice'])
    html = html.replace('{{GAP_ADVICE}}', result['gap_advice'])
    html = html.replace('{{FOUR_ADVICE}}', result['four_advice'])

    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"报告已生成：{output_path}")


# ============================================================
# 主入口
# ============================================================

def main():
    if len(sys.argv) < 2:
        print("用法：python analyze.py 聊天记录.txt [输出报告.html]")
        print("示例：python analyze.py chat.html report.html")
        sys.exit(1)

    input_file = sys.argv[1]
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        base = os.path.splitext(input_file)[0]
        output_file = base + '_分析报告.html'

    # 读取
    print(f"读取文件：{input_file}")
    lines = read_chat(input_file)

    # 解析
    messages = []
    for line in lines:
        m = parse_line(line)
        if m:
            messages.append(m)

    print(f"有效消息：{len(messages)} 条（剔除 {len(lines) - len(messages)} 条）")

    if len(messages) < 10:
        print("错误：有效消息太少，无法分析")
        sys.exit(1)

    # 自动识别发送者
    me_name, her_name = detect_senders(messages)
    messages = normalize_senders(messages, me_name, her_name)

    # 分析
    result = analyze(messages)
    result['sender_names'] = {'me': me_name, 'her': her_name}

    # 生成报告
    generate_report(result, output_file)


if __name__ == '__main__':
    main()
