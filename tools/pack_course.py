# -*- coding: utf-8 -*-
"""CoursePack 校验 + 打包

用法：
  python pack_course.py <course-dir>            # 校验后打包成 <id>.coursepack.zip
  python pack_course.py <course-dir> --check    # 只校验
  python pack_course.py <course-dir> --out x.zip
"""
import os, sys, json, zipfile, datetime

REQUIRED = ["id", "code", "name", "weeks"]
VALID_TYPES = {"single", "multi", "tf", "fill", "short", "match"}


def load(p):
    return json.load(open(p, encoding="utf-8"))


def check(course_dir):
    errs, warns = [], []
    cj = os.path.join(course_dir, "course.json")
    if not os.path.exists(cj):
        return ["缺 course.json"], []
    try:
        c = load(cj)
    except Exception as e:
        return ["course.json 解析失败: %s" % e], []
    for k in REQUIRED:
        if not c.get(k):
            errs.append("course.json 缺字段 %s" % k)
    if not c.get("weeks"):
        errs.append("weeks 为空")

    qids = {}
    total = 0
    for w in c.get("weeks", []):
        key = w.get("key")
        if not key:
            errs.append("某个 week 缺 key"); continue
        for rel in w.get("notes", []):
            if not os.path.exists(os.path.join(course_dir, rel)):
                errs.append("[%s] 讲义不存在: %s" % (key, rel))
        bf = w.get("bank")
        if not bf:
            warns.append("[%s] 没有题库（只能看讲义，不能练）" % key); continue
        bp = os.path.join(course_dir, bf)
        if not os.path.exists(bp):
            errs.append("[%s] 题库不存在: %s" % (key, bf)); continue
        try:
            qs = load(bp)
        except Exception as e:
            errs.append("[%s] 题库解析失败: %s" % (key, e)); continue
        if not isinstance(qs, list):
            errs.append("[%s] 题库应为数组" % key); continue
        for q in qs:
            total += 1
            qid = q.get("id") or "(无 id)"
            if not q.get("id"):
                errs.append("[%s] 有题目缺 id" % key)
            elif qid in qids:
                errs.append("重复 id: %s（%s 与 %s）" % (qid, qids[qid], bf))
            else:
                qids[qid] = bf
            if not str(qid).upper().startswith(key.upper()):
                warns.append("%s 的 id 没有以 %s 开头（讲次归属可能错）" % (qid, key.upper()))
            t = q.get("type")
            if t not in VALID_TYPES:
                errs.append("%s 的 type 非法: %s" % (qid, t)); continue
            if t == "single":
                if len(q.get("options") or []) != 4:
                    errs.append("%s 单选选项数 ≠ 4" % qid)
                a = q.get("answer")
                if not isinstance(a, int) or not (0 <= a < len(q.get("options") or [])):
                    errs.append("%s 单选 answer 越界" % qid)
            elif t == "tf":
                if q.get("options") != ["True", "False"]:
                    errs.append("%s 判断题 options 必须是 [\"True\",\"False\"]" % qid)
                if q.get("answer") not in (0, 1):
                    errs.append("%s 判断题 answer 必须是 0/1" % qid)
            elif t == "multi":
                a = q.get("answer")
                if not isinstance(a, list) or not a:
                    errs.append("%s 多选 answer 应为数组" % qid)
                elif any((not isinstance(i, int)) or i < 0 or i >= len(q.get("options") or []) for i in a):
                    errs.append("%s 多选 answer 越界" % qid)
                elif a != sorted(a):
                    warns.append("%s 多选 answer 未升序（会自动排序）" % qid)
            elif t == "fill":
                if not q.get("answers"):
                    errs.append("%s 填空缺 answers" % qid)
                elif not all(isinstance(x, list) for x in q["answers"]):
                    errs.append("%s 填空 answers 应为「每空一个数组」" % qid)
            elif t == "short":
                if not q.get("keywords") or not q.get("model"):
                    errs.append("%s 简答缺 keywords/model" % qid)
            elif t == "match":
                if not q.get("pairs"):
                    errs.append("%s 配对缺 pairs" % qid)
            if not q.get("explain"):
                warns.append("%s 缺中文解析" % qid)
            src = q.get("source") or ""
            if "p" not in src.lower():
                warns.append("%s 的 source 里没有页码（无法自动配到讲义页）" % qid)
    return errs, warns + ["共 %d 题 / %d 讲" % (total, len(c.get("weeks", [])))]


def pack(course_dir, out=None):
    c = load(os.path.join(course_dir, "course.json"))
    cid = c["id"]
    out = out or os.path.join(course_dir, cid + ".coursepack.zip")
    files = []
    for root, dirs, fs in os.walk(course_dir):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
        for f in fs:
            if f.endswith(".coursepack.zip"):
                continue
            p = os.path.join(root, f)
            files.append(os.path.relpath(p, course_dir).replace("\\", "/"))
    man = {"spec": "coursepack/1", "id": cid, "code": c.get("code"), "name": c.get("name"),
           "built": datetime.datetime.now().isoformat(timespec="seconds"),
           "weeks": [w.get("key") for w in c.get("weeks", [])], "files": files}
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(man, ensure_ascii=False, indent=1))
        for rel in files:
            z.write(os.path.join(course_dir, rel), rel)
    size = os.path.getsize(out) / 1024 / 1024
    print("打包完成：%s（%d 个文件，%.2f MB）" % (out, len(files) + 1, size))
    return out


def pack_json(course_dir, out=None):
    """把课程打成一个 .pack.json（数据包）：浏览器端可直接导入，无需 Python。"""
    import sys as _s, re as _re
    _s.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "app"))
    import build_course as bc
    c = bc.load_course(course_dir)
    banks = bc.build_banks(c)
    notes = bc.notes_html_for(c)
    papers = bc.papers_html_for(c)
    # 讲义图内联进数据包（导入后没有 assets 目录）
    if c.get("images_file"):
        imgp = os.path.join(c["root"], c["images_file"])
        if os.path.exists(imgp):
            imgs = json.load(open(imgp, encoding="utf-8"))
            for k, v in imgs.items():
                notes = notes.replace('assets/%s.jpg' % k, v[0])
    # 页面截图不随数据包走
    for b in banks:
        for q in b.get("questions", []):
            q.pop("pageimg", None)
    study = []
    sp = os.path.join(c["root"], c.get("study") or "study.json")
    if os.path.exists(sp):
        study = json.load(open(sp, encoding="utf-8"))
        for card in study:
            for q in card.get("qs", []):
                q.pop("pageimg", None)
    callout = ""
    cf = os.path.join(c["root"], "callout.html")
    if os.path.exists(cf):
        callout = open(cf, encoding="utf-8").read()
    packobj = {"spec": "coursepack/1", "id": c["id"],
               "meta": {k: c.get(k) for k in ("id", "code", "name", "short", "exam", "hub")},
               "banks": banks, "notes_html": notes, "papers_html": papers,
               "study": study, "callout": callout,
               "built": datetime.datetime.now().isoformat(timespec="seconds")}
    out = out or os.path.join(course_dir, c["id"] + ".pack.json")
    json.dump(packobj, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    print("数据包：%s（%.2f MB，%d 题库 / %d 关）" % (out, os.path.getsize(out) / 1024 / 1024, len(banks), len(study)))
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    d = sys.argv[1]
    errs, warns = check(d)
    for w in warns[:40]:
        print("  ⚠", w)
    if errs:
        print("\n❌ %d 个错误：" % len(errs))
        for e in errs[:60]:
            print("  -", e)
        sys.exit(2)
    print("\n✅ 校验通过")
    if "--pack-json" in sys.argv:
        out = None
        if "--out" in sys.argv:
            out = sys.argv[sys.argv.index("--out") + 1]
        pack_json(d, out)
        sys.exit(0)
    if "--check" not in sys.argv:
        out = None
        if "--out" in sys.argv:
            out = sys.argv[sys.argv.index("--out") + 1]
        pack(d, out)
