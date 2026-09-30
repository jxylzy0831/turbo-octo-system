from __future__ import annotations

import re
from pathlib import Path

import build_school_arrival_interaction as renderer


ROOT = Path(__file__).resolve().parent.parent
BASE = '末日学校-抵达后互动-五人出场版-20260930-v2'


def main() -> None:
    renderer.BASE = BASE
    renderer.main()
    page_path = ROOT / 'drafts' / (BASE + '.html')
    page = page_path.read_text(encoding='utf-8')
    page = page.replace('第一顿饭，先别急着走。', '五种方式走进教室。')
    page = page.replace('第一顿饭', '五人出场与破冰')
    page = page.replace('四对来客循广播抵达学校。G 和 N1—N4 带着大家进门、分食、约上课，再录下第一天。台词分色，动作、玩家入口与接法显示为灰色。',
                        '四位玩家开场已坐在各自位置。G 与四位 N 各自出场，用名字、来物和认领短问答认识彼此，再约下一顿饭。台词分色，动作与玩家接法为灰色。')
    page = page.replace('6 个环节', '7 个环节').replace('36 分钟', '28 分钟')
    page = page.replace('末日学校-抵达后互动设计说明-20260930-v1.md',
                        '末日学校-五人出场与破冰设计说明-20260930-v2.md')
    director = '''<details class="director"><summary>排练前说明 · 五人出场、玩家坐席与破冰</summary>
<p>四位 P 开场坐好，五位演员依次出现。G 以现场广播探头入场；N1 取欢迎袋闯入；N2 举招领牌入场；N3 以箱子和叩门入场，等 P3 的安排；N4 趁开箱沿墙入场，先对 P4 说话。无需其他演员、录音旁白或自动灯光。</p>
<p>七段约 2、3、3、3、3、7、7 分钟，共约 28 分钟，待排练验证。每个出场的单向展示控制在 30 秒内，随即给玩家回应。未轮到对位 N 的玩家由 G 的点名、见证、取物与追问接住，不要求起身重演抵达。</p>
<p>G 错记小偷、走丢妹妹等称呼，由 N 和玩家纠正，完成自我介绍。物品认领只问刚才发生的事和双方看法；邀请到讲台前说，也可坐着接话。没有固定正确答案，不拿默契好坏惩罚玩家。</p>
<p>N4 的细布和椅背是有限旧轮回记忆的本轮提案。若 P4 猜中就承认异常，不强迫她回头或禁止回头。全本轮回机制另行落实。</p>
<p>五名演员全程自己敲门、操作手机、交接道具。四位 P 的称呼与物品本按真实回应填写，录像也只记录真实发生的交流。</p></details>'''
    page = re.sub(r'<details class="director">.*?</details>', director, page, flags=re.S)
    page_path.write_text(page, encoding='utf-8')
    md_path = ROOT / 'drafts' / (BASE + '.md')
    markdown = md_path.read_text(encoding='utf-8').replace('第一顿饭', '五人出场与破冰')
    markdown = markdown.replace('预计 36 分钟', '预计 28 分钟')
    markdown = markdown.replace('原创排练稿，', '四位 P 开场已坐好，五位演员分别出场。原创排练稿，')
    md_path.write_text(markdown, encoding='utf-8')


if __name__ == '__main__':
    main()
