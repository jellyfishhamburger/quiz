# CoursePack v1 规范

> 目标：**任何人（或任何 AI）按这个规范生成一套文件，就能变成本站的课程页**；同学之间也能互相传课程包。
> 一个课程包 = 一个文件夹。打包后是一个 `.coursepack.zip`。

## 1. 目录结构

```
<course-id>/
├── course.json              # 必需：课程元信息（见 §2）
├── week1/                   # 讲次目录，名字随意，course.json 里指到就行
│   ├── 精讲.md              # 必需：知识点讲解（§3）
│   ├── 概念卡.md            # 推荐：速查表（§4）
│   └── bank_week1.json      # 必需：题库（§5）
├── week2/ …
├── pastpapers/              # 可选：真题拆解、老师强调点、规律总表（普通 Markdown）
│   ├── 真题考点-按知识点重组.md
│   └── 老师强调点.md
├── pages/                   # 可选：讲义原页截图（§6）
│   └── w1-1_p02.jpg
├── images.json              # 可选：9 张以内的关键图（dataURI 或已落盘的相对路径）
├── pagemap.json             # 可选：{"W1-1|2": "pages/w1-1_p02.jpg"}
└── study.json               # 自动生成：学习关卡（由 make_study.py 产出）
```

## 2. course.json

```json
{
  "id": "idat7215",
  "code": "IDAT7215",
  "name": "Computer Programming for Product Development and Applications",
  "short": "Computer Programming for Product Dev.",
  "root": "C:\\path\\to\\<course-id>",          // 构建时的素材根目录（可省略）
  "exam": { "date": "2026-10-22", "minutes": 60, "note": "闭卷 · 80% 选择判断 + 20% 简答" },
  "weeks": [
    { "key": "w1", "name": "Week 1 · 编程导论 + Python 基础",
      "desc": "一句话说明这一讲的范围",
      "notes": ["week1/精讲.md", "week1/概念卡.md"],
      "bank":  "week1/bank_week1.json" }
  ],
  "papers": ["pastpapers/真题考点-按知识点重组.md", "pastpapers/老师强调点.md"],
  "study": "study.json",
  "images_file": "images.json",
  "pagemap": "pagemap.json",
  "out": "site/quiz/courses/idat7215/index.html",
  "hub": "../../index.html"
}
```

规则：
- `weeks[].key` 决定**进度键**与题目 id 前缀（`w1` → 题目 `W1-001`，速记锚点 `#wk-w1`）。**一旦发布不要改**，否则同学进度会丢。
- 没有题库的讲次（比如只想放讲义）可以省略 `bank`，该讲就不会出现在「练」里。
- `papers` 里**第一篇**会展开显示，其余自动折叠。

## 3. 精讲.md（最重要）

- 用 `## 1. 标题（p.8）` / `### 4.1 子标题` 分知识点——**每个标题就是一张学习卡**。
- **标题里带讲义页码**（`（p.8）`、`（W1-2 p.10–12）`）。系统靠页码把「题目 ↔ 讲解」自动配对，配不上的知识点会单独成卡但不配题。
- 每个知识点建议写三层：`**在说什么**` / `**为什么/怎么理解**` / `**考试怎么考**`。
- 表格用标准 Markdown（会被渲染成真表格，手机上自动变卡片）。
- 每讲结尾加 `## 📌 本讲速记` + 5–10 条可背的短句。
- 需要跳转到别处时写 `[[go:关键词|按钮文字]]` → 渲染成"跳到速记表对应小节"的按钮。

## 4. 概念卡.md

一张表：`概念 | 一句话定义 | 关键点 | 易混/陷阱`。行数不限，但每行都要能独立看懂。

## 5. 题库 JSON（数组）

```json
[
  { "id": "W1-001", "topic": "编程导论", "type": "single",
    "q": "Which of the following is a prohibited action?",
    "options": ["A 选项", "B 选项", "C 选项", "D 选项"],
    "answer": 2,
    "explain": "中文解析：为什么对 + 其它选项为什么错",
    "source": "W1-1 p.2",
    "tag": "w1" },

  { "id": "W1-002", "type": "tf", "options": ["True", "False"], "answer": 1, … },
  { "id": "W1-003", "type": "multi", "options": ["…","…","…","…"], "answer": [0, 2], … },
  { "id": "W1-004", "type": "fill",  "q": "Call … ______ .", "answers": [["after you leave"], ["在你离开之后"]], … },
  { "id": "W1-005", "type": "short", "q": "State two differences …", "keywords": ["…","…"], "model": "English model answer." },
  { "id": "W1-006", "type": "match", "pairs": [["Latex", "single use"], ["…", "…"]] }
]
```

硬性要求：
- **`id` 必须以讲次前缀开头**（`W1-`、`W2-`…），系统据此把题挂到对应讲次的「看这一讲的精讲」。
- **`source` 必须能解析出页码**（`W1-2 p.13`、`W3-1 p.46–49`），这是"🖼 看讲义这一页"和自动配题的依据。
- 单选必须 4 个选项、`answer` 是 0-based 索引；多选 `answer` 是升序索引数组。
- `explain` 用中文，写出"为什么错"；`source` 写讲义出处。
- 同一份题库内 `id` 唯一。

## 6. pages/ 与 pagemap.json

- 每个引用了的 (讲义, 页码) 渲染成一张 JPEG（建议 dpi 96 / quality 58，约 60KB/页）。
- 命名：`w1-1_p02.jpg`（讲次小写 + 页码两位）。
- `pagemap.json`：`{"W1-1|2": "pages/w1-1_p02.jpg"}`。
- 生成脚本示例见 `make_pages.py`（PyMuPDF）。

## 7. 打包与校验

```bash
python pack_course.py <course-dir>          # 校验 + 打包成 <id>.coursepack.zip
python pack_course.py <course-dir> --check  # 只校验不打包
```

`--check` 会检查：course.json 必填字段、每个 week 的 notes/bank 是否存在、题库 id 前缀与唯一性、单选选项数、answer 越界、short 是否缺 keywords/model、source 是否带可解析页码。

## 8. 构建成网页

```bash
python app/build_course.py <course-id>      # 读取 学习中心/courses/<id>/course.json
```

产物是单文件 HTML（+ `assets/`、`pages/`），可直接放 GitHub Pages / 任何静态托管。

## 9. 版本与兼容

- 本规范版本 **v1**；`pack_course.py` 打包时会写 `manifest.json`（`{"spec":"coursepack/1", "id":…, "built":…, "files":[…]}`）。
- 新增字段必须可选、有默认值；**不要重命名已有字段**（会让旧包打不开）。
