# 会话主题：寻找剧本杀互动与羁绊设计 Skill

创建日期：2026-10-05
记录起点：用户提出寻找适合剧本杀每幕互动、拉羁绊的社区 Skill，并比较话剧编剧 Skill。
会话标识：skill-research（当前环境未提供可读取的线程 ID）

## 第 1 轮

### 用户原文

你能帮我在github或者什么社区找一下适合剧本杀每一幕互动或者拉羁绊的skill吗，你觉得话剧的编剧skill如何呢，或者你是否能找到更好更适合的skill

### 助手进度说明

我会先按仓库约定检查当前工作区里和写作、互动设计相关的材料，再去 GitHub 和其他社区查找可用的 skills。我会重点比较它们是否支持分幕信息释放、角色关系推进和可直接落到剧本杀互动环节，而不只看“编剧”这个标签。

仓库里已经有两版“剧本互动设计” skill 和对应的互动方法资料，这能作为实际基准来判断外部方案是否更适合。接下来我会查看这两版的定位与工作流程，同时检索社区里偏剧本杀、桌面角色扮演、互动戏剧和戏剧编剧的公开 skills。

初步结论已经比较清楚：话剧/电影编剧类 skill 对人物弧光、场景目标、对白和节奏有用，但通常不管玩家实际怎么参与、NPC 如何接住玩家的不同回应，以及演员和现场资源怎么执行。相较之下，沉浸式互动戏剧和剧本杀主持类素材更贴近“每幕互动”，不过社区里不少项目偏即兴分支或主持技巧，不能直接取代你仓库里已有的 v2。

### 助手最终回复

我检索了 GitHub 和社区目录，也对照了仓库现有的两版互动 Skill。结论是：**话剧编剧 Skill 有帮助，但不适合作为“每幕互动／拉羁绊”的主 Skill；你现有的 `scripted-interaction-design-v2` 已经更贴近这个任务。**

| 方向 | 适合借鉴的部分 | 与剧本杀互动设计的缺口 |
|---|---|---|
| 话剧/影视编剧，例如 [screenwriting-skills](https://github.com/jtydhr88/screenwriting-skills) | 场景目标、戏剧压力、人物弧光、对白和节奏 | 聚焦作者写好的戏，通常不细化玩家如何进入、NPC 如何适配现场回答、流程如何在真实场地执行。这个项目本身也说明舞台剧部分仍在扩展。 |
| 互动戏剧，例如 [interactive-theatre-designer](https://github.com/majiayu000/claude-skill-registry/tree/main/skills/other/interactive-theatre-designer) | 观众参与模式、选择结构、群体决策、互动失败时的预案 | 偏沉浸式空间和分支选择，有些假设需要多区域、技术系统或观众决定剧情；不一定适合固定真相、有限演员和单房间剧本杀。 |
| 剧本杀主持，例如 [script-killing-dm](https://github.com/theneoai/awesome-skills/tree/main/skills/persona/entertainment/script-killing-dm) | 分幕控场、玩家参与、冷场/强势玩家应对、复盘流程 | 更像综合 DM 人设与主持知识，范围很宽；“情感工程”“保证高质量”等说法缺少可核验依据，也没像你的 v2 那样把互动拆成因果链和现场资源约束。 |
| 游戏叙事，例如 [game-narrative](https://github.com/myshenoy/skills-open-source/tree/main/game-narrative) | NPC 能动性、玩家驱动的信息发现、互动对白和推理结构 | 面向电子游戏的搜索式叙事和系统设计，对线下演员调度、同桌玩家之间的关系互动覆盖不足。 |

**我的建议是保留你现有 v2 作为主框架，再把戏剧编剧与游戏叙事作为两个窄辅助模块：**

1. 用戏剧编剧方法检查“这一场要发生什么变化”、阻力是否成立、人物是否有行动理由。
2. 用互动设计 v2 把目标转成玩家入口、可执行动作、NPC 接话、关系或认知变化、沉默/拒绝/提前完成时的接法，以及房间和演员调度。
3. 用游戏叙事方法补查信息差、揭晓顺序、玩家发现过程和旧互动的后续回收。

这样比另找一个“话剧编剧 Skill”整体替换更合适。你的 v2 已覆盖了很多通用互动戏剧建议，并且针对单房间、幕布、音乐灯光和玩家回应做了具体约束。外部资源最值得补的是**场景戏剧目标诊断**和**人物弧光/场景压力的工具**，不是再造一套互动流程。

我没有安装或改动任何文件；这轮是检索和比较。注意外部 Skill 的仓库内容可能会变化，社区目录里的星数和简介也不能证明它实际写作质量。推荐进一步试用前，先挑一幕做小样，检查它能否同时守住原手册事实、角色知情范围、玩家真实参与和现场可执行性。

### 参考链接

- [screenwriting-skills（GitHub）](https://github.com/jtydhr88/screenwriting-skills)
- [interactive-theatre-designer（GitHub）](https://github.com/majiayu000/claude-skill-registry/tree/main/skills/other/interactive-theatre-designer)
- [script-killing-dm（GitHub）](https://github.com/theneoai/awesome-skills/tree/main/skills/persona/entertainment/script-killing-dm)
- [game-narrative（GitHub）](https://github.com/myshenoy/skills-open-source/tree/main/game-narrative)
- [IBSEN：导演-演员协作的互动戏剧脚本研究](https://arxiv.org/abs/2407.01093)
