# 牌索引

本文件始终加载。解读时先用它定位每张牌的元素/守护星/星座/原型,再按需读 `cards/<牌名>.md` 取详细牌意。**只读涉及到的牌的详细 ref,没涉及的不加载。**

## 当前支持的塔罗体系

- **韦特(Rider-Waite-Smith)** —— 已支持,牌意在 `cards/waite/`。
- 透特(Thoth)、马赛(Marseille)等 —— 暂未支持(目录 `cards/thoth/` 已预留)。若用户指定其他体系,告知当前仅支持韦特,仍按韦特解读或请用户确认。

## 跨体系结构(重要)

- **占星骨架(本文件的元素/守护星/星座列)** —— 跨体系通用,放索引层。韦特与透特对大部分牌的元素/守护星认定一致;差异在牌意、画面、编号、原型,这些放各体系目录。
- **牌意(画面/正逆位/原型)** —— 体系专属,按体系分目录:`cards/waite/<牌>.md`、`cards/thoth/<牌>.md`。加新体系 = 加一个目录,不动索引和其他体系。

## 文件名约定

每张牌的详细 ref 在 `cards/<体系>/` 下,文件名为小写连字符英文:

- 大阿卡纳:`the-fool.md`、`the-magician.md` ... `the-world.md`
- 小阿卡纳:`<花色>-<数字或宫廷>.md`,如 `wands-ace.md`、`cups-queen.md`、`pentacles-10.md`

花色英文:权杖 wands / 圣杯 cups / 宝剑 swords / 星币 pentacles。宫廷:侍从 page / 骑士 knight / 皇后 queen / 国王 king。数字:ace(1)/ 2-10。

下表「ref」列即文件名(不含 `.md`)。当前体系为韦特时,详细 ref 路径为 `references/cards/waite/<ref>.md`。grep 牌名时用英文驼峰或中文均可命中。

## 大阿卡纳(22 张)

| ref | 英文名 | 中文 | 元素 | 守护星 | 星座 | 原型关键词 |
|---|---|---|---|---|---|---|
| the-fool | TheFool | 愚者 | 风 | 天王星 | 水瓶座 | 纯真者、探险家、自由精神 |
| the-magician | TheMagician | 魔术师 | 风 | 水星 | — | 创造者、显化者、沟通者 |
| the-high-priestess | TheHighPriestess | 女祭司 | 水 | 月亮 | — | 智慧守护者、神秘主义者、内在导师 |
| the-empress | TheEmpress | 女皇 | 土 | 金星 | — | 母亲、滋养者、自然女神 |
| the-emperor | TheEmperor | 皇帝 | 火 | 火星 | 白羊座 | 父亲、统治者、秩序维护者 |
| the-hierophant | TheHierophant | 教皇 | 土 | 金星 | 金牛座 | 导师、传统守护者、精神领袖 |
| the-lovers | TheLovers | 恋人 | 风 | 水星 | 双子座 | 选择者、结合者、爱人 |
| the-chariot | TheChariot | 战车 | 水 | 月亮 | 巨蟹座 | 胜利者、意志力驾驭者 |
| strength | Strength | 力量 | 火 | 太阳 | 狮子座 | 驯兽师、内在力量掌握者 |
| the-hermit | TheHermit | 隐士 | 土 | 水星 | 处女座 | 智者、寻求者、内在指引者 |
| wheel-of-fortune | WheelofFortune | 命运之轮 | 火 | 木星 | — | 命运轮转者、机遇捕捉者 |
| justice | Justice | 正义 | 风 | 金星 | 天秤座 | 法官、平衡者、真理追求者 |
| the-hanged-man | TheHangedMan | 倒吊人 | 水 | 海王星 | — | 殉道者、牺牲者、新视角 |
| death | Death | 死神 | 水 | 冥王星 | 天蝎座 | 转变者、结束者、凤凰 |
| temperance | Temperance | 节制 | 火 | 木星 | 射手座 | 炼金术士、平衡者、治疗者 |
| the-devil | TheDevil | 恶魔 | 土 | 土星 | 摩羯座 | 阴影、诱惑者、囚禁者 |
| the-tower | TheTower | 高塔 | 火 | 火星 | — | 毁灭者、觉醒者、颠覆者 |
| the-star | TheStar | 星星 | 风 | 天王星 | 水瓶座 | 希望给予者、灵感者、治疗者 |
| the-moon | TheMoon | 月亮 | 水 | 海王星 | 双鱼座 | 潜意识探索者、幻象者 |
| the-sun | TheSun | 太阳 | 火 | 太阳 | — | 启蒙者、喜悦者、成功者 |
| judgement | Judgement | 审判 | 水 | 冥王星 | — | 觉醒者、重生者、自我评估 |
| the-world | TheWorld | 世界 | 土 | 土星 | — | 完成者、整合者、圆满者 |

## 小阿卡纳(56 张)

每个花色 14 张:Ace + 2-10 + 侍从 + 骑士 + 皇后 + 国王。

### 权杖(Wands)— 火 | 白羊/狮子/射手 | 火星 — 行动力、热情、事业

| ref | 牌名 | 中文 |
|---|---|---|
| wands-ace | Wands-Ace | 权杖王牌 |
| wands-2 | Wands-2 | 权杖二 |
| wands-3 | Wands-3 | 权杖三 |
| wands-4 | Wands-4 | 权杖四 |
| wands-5 | Wands-5 | 权杖五 |
| wands-6 | Wands-6 | 权杖六 |
| wands-7 | Wands-7 | 权杖七 |
| wands-8 | Wands-8 | 权杖八 |
| wands-9 | Wands-9 | 权杖九 |
| wands-10 | Wands-10 | 权杖十 |
| wands-page | Wands-Page | 权杖侍从 |
| wands-knight | Wands-Knight | 权杖骑士 |
| wands-queen | Wands-Queen | 权杖皇后 |
| wands-king | Wands-King | 权杖国王 |

### 圣杯(Cups)— 水 | 双鱼/巨蟹/天蝎 | 月亮 — 情感、关系、内在

| ref | 牌名 | 中文 |
|---|---|---|
| cups-ace | Cups-Ace | 圣杯王牌 |
| cups-2 | Cups-2 | 圣杯二 |
| cups-3 | Cups-3 | 圣杯三 |
| cups-4 | Cups-4 | 圣杯四 |
| cups-5 | Cups-5 | 圣杯五 |
| cups-6 | Cups-6 | 圣杯六 |
| cups-7 | Cups-7 | 圣杯七 |
| cups-8 | Cups-8 | 圣杯八 |
| cups-9 | Cups-9 | 圣杯九 |
| cups-10 | Cups-10 | 圣杯十 |
| cups-page | Cups-Page | 圣杯侍从 |
| cups-knight | Cups-Knight | 圣杯骑士 |
| cups-queen | Cups-Queen | 圣杯皇后 |
| cups-king | Cups-King | 圣杯国王 |

### 宝剑(Swords)— 风 | 双子/天秤/水瓶 | 水星 — 思维、沟通、冲突

| ref | 牌名 | 中文 |
|---|---|---|
| swords-ace | Swords-Ace | 宝剑王牌 |
| swords-2 | Swords-2 | 宝剑二 |
| swords-3 | Swords-3 | 宝剑三 |
| swords-4 | Swords-4 | 宝剑四 |
| swords-5 | Swords-5 | 宝剑五 |
| swords-6 | Swords-6 | 宝剑六 |
| swords-7 | Swords-7 | 宝剑七 |
| swords-8 | Swords-8 | 宝剑八 |
| swords-9 | Swords-9 | 宝剑九 |
| swords-10 | Swords-10 | 宝剑十 |
| swords-page | Swords-Page | 宝剑侍从 |
| swords-knight | Swords-Knight | 宝剑骑士 |
| swords-queen | Swords-Queen | 宝剑皇后 |
| swords-king | Swords-King | 宝剑国王 |

### 星币(Pentacles)— 土 | 金牛/处女/摩羯 | 金星 — 物质、稳定、现实

| ref | 牌名 | 中文 |
|---|---|---|
| pentacles-ace | Pentacles-Ace | 星币王牌 |
| pentacles-2 | Pentacles-2 | 星币二 |
| pentacles-3 | Pentacles-3 | 星币三 |
| pentacles-4 | Pentacles-4 | 星币四 |
| pentacles-5 | Pentacles-5 | 星币五 |
| pentacles-6 | Pentacles-6 | 星币六 |
| pentacles-7 | Pentacles-7 | 星币七 |
| pentacles-8 | Pentacles-8 | 星币八 |
| pentacles-9 | Pentacles-9 | 星币九 |
| pentacles-10 | Pentacles-10 | 星币十 |
| pentacles-page | Pentacles-Page | 星币侍从 |
| pentacles-knight | Pentacles-Knight | 星币骑士 |
| pentacles-queen | Pentacles-Queen | 星币皇后 |
| pentacles-king | Pentacles-King | 星币国王 |

## 数字牌与宫廷牌的发展逻辑

- **数字牌 1-10**:事物从开始到结束的完整发展过程。1 = 起点/种子,10 = 圆满或过度后的循环终点。
- **宫廷牌 侍从→骑士→皇后→国王**:某项能力或人生阶段的发展,从稚嫩探索到成熟掌控。

## 如何读取单牌详细 ref

定位到牌后,按当前体系读对应文件:

```
references/cards/<体系>/<ref>.md
```

当前体系默认韦特。例:抽到正位女皇 → 读 `references/cards/waite/the-empress.md`。抽到逆位宝剑七 → 读 `references/cards/waite/swords-7.md`(逆位解读在该文件内)。

若该牌的 ref 文件尚未创建(不存在),回退到模型自身的塔罗知识,并参考 `elements.md`/`planets.md` 补全元素与占星维度。
