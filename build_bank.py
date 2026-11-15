"""Extract the PMP practice-test PDF into a structured question bank for personal multiple-choice practice.

Run:     py -3.12 -X utf8 pmp-mock/build_bank.py
Outputs: bank.json, <section>-questions.md, <section>-answers.md, README.md
"""
import glob, json, os, re, sys, unicodedata

sys.path.insert(0, r"C:\Users\THANH\.claude\skills\pdf-to-word\deps")
import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = glob.glob(os.path.join(os.path.dirname(HERE), "PMP Mock Practice Tests*.pdf"))[0]

SECTION = re.compile(r"^(.{3,60}?)\s+-\s+(Questions|Answers|Result Sheet)$")
Q_HEAD = re.compile(r"^Question\s+(\d{1,3})$")
A_HEAD = re.compile(r"^Question\s+\((\d{1,3})\)$")
OPTION = re.compile(r"^([A-H])\.\s*(.*)$")
CORRECT = re.compile(r"^Correct Answers?\s*[=:]\s*(.*)$", re.I)
ZW = dict.fromkeys(map(ord, "\u200b\u200c\u200d\ufeff"), None)


def clean(line: str) -> str:
    return unicodedata.normalize("NFC", line).translate(ZW).replace("\u00a0", " ").strip()


def lines_of(doc):
    for page_index in range(len(doc)):
        for raw in doc[page_index].get_text().split("\n"):
            line = clean(raw)
            if line:
                yield page_index + 1, line


def slug(name: str) -> str:
    name = name.lower().replace("&", "and")
    return re.sub(r"[^a-z0-9]+", "-", name).strip("-")


def parse():
    doc = pymupdf.open(SRC)
    sections, order = {}, []
    current, kind, item, field = None, None, None, None
    for page, line in lines_of(doc):
        m = SECTION.match(line)
        if m and m.group(1).lower().replace("full exam", "full mock exam") != "":
            name = re.sub(r"^Full Exam", "Full Mock Exam", m.group(1).strip())
            if page <= 4:           # table of contents
                continue
            current, kind, item, field = name, m.group(2), None, None
            if name not in sections:
                sections[name] = {"name": name, "questions": {}, "answers": {}}
                order.append(name)
            continue
        if current is None or kind == "Result Sheet":
            continue
        if re.fullmatch(r"\d{1,3}", line):   # page numbers
            continue
        sec = sections[current]
        if kind == "Questions":
            m = Q_HEAD.match(line)
            if m:
                item = {"n": int(m.group(1)), "page": page, "stem": "", "options": {}}
                sec["questions"][item["n"]] = item
                field = "stem"
                continue
            if item is None:
                continue
            m = OPTION.match(line)
            # an option letter must continue the A, B, C… sequence, otherwise it is ordinary text
            if m and m.group(1) == "ABCDEFGH"[len(item["options"])]:
                field = m.group(1)
                item["options"][field] = m.group(2)
                continue
            if field == "stem":
                item["stem"] = (item["stem"] + " " + line).strip()
            else:
                item["options"][field] = (item["options"][field] + " " + line).strip()
        else:
            m = A_HEAD.match(line)
            if m:
                item = {"n": int(m.group(1)), "page": page, "correct": "", "explanation": ""}
                sec["answers"][item["n"]] = item
                field = None
                continue
            if item is None:
                continue
            m = CORRECT.match(line)
            if m and not item["correct"]:
                item["correct"] = m.group(1).strip()
                field = "correct" if not item["correct"] else "explanation"
                continue
            if field == "correct" and not item["correct"]:
                item["correct"] = line
                field = "explanation"
                continue
            sep = "\n" if re.match(r"^Options?\s+[A-H]", line) else " "
            item["explanation"] = (item["explanation"] + sep + line).strip()
            field = "explanation"
    return [sections[name] for name in order]


def main():
    sections = parse()
    bank, report = [], []
    for index, sec in enumerate(sections, 1):
        sid = f"{index:02d}-{slug(sec['name'])}"
        qs, ans = sec["questions"], sec["answers"]
        merged = []
        for n in sorted(qs):
            q, a = qs[n], ans.get(n, {})
            letters = re.findall(r"\b([A-H])\b", a.get("correct", "")) if re.fullmatch(r"[A-H](\s*(,|and|&)\s*[A-H])*\.?", a.get("correct", "").strip()) else []
            merged.append({
                "id": f"{sid}#{n}", "section": sec["name"], "n": n, "page": q["page"],
                "stem": q["stem"], "options": q["options"],
                "correct": a.get("correct", ""), "correct_letters": letters,
                "type": "choice" if len(q["options"]) >= 2 and letters else "other",
                "explanation": a.get("explanation", ""), "answer_page": a.get("page"),
            })
        bank += merged
        with open(os.path.join(HERE, f"{sid}-questions.md"), "w", encoding="utf-8") as f:
            f.write(f"# {sec['name']} — Questions\n\n")
            for m in merged:
                f.write(f"## Question {m['n']}\n\n{m['stem']}\n\n")
                for letter, text in m["options"].items():
                    f.write(f"- **{letter}.** {text}\n")
                f.write("\n")
        with open(os.path.join(HERE, f"{sid}-answers.md"), "w", encoding="utf-8") as f:
            f.write(f"# {sec['name']} — Answers and explanations\n\n")
            for m in merged:
                f.write(f"## Question {m['n']}\n\n**Answer: {m['correct'] or '(not extracted)'}**\n\n{m['explanation']}\n\n")
        report.append({
            "id": sid, "name": sec["name"], "questions": len(qs), "answers": len(ans),
            "choice": sum(m["type"] == "choice" for m in merged),
            "other": [m["n"] for m in merged if m["type"] == "other"],
            "no_answer": [n for n in sorted(qs) if n not in ans],
            "missing_numbers": [n for n in range(1, (max(qs) if qs else 0) + 1) if n not in qs],
            "option_counts": {k: sum(len(m["options"]) == k for m in merged) for k in sorted({len(m["options"]) for m in merged})},
        })
    with open(os.path.join(HERE, "bank.json"), "w", encoding="utf-8") as f:
        json.dump(bank, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, "README.md"), "w", encoding="utf-8") as f:
        f.write("# PMP mock — practice question bank\n\n")
        f.write("Extracted automatically from the PMP practice-test PDF in the parent folder, for personal practice only. Re-run with `py -3.12 -X utf8 pmp-mock/build_bank.py`.\n\n")
        f.write("| Section | Questions | With answer | Gradable multiple-choice | Other types (drag-and-drop, matching…) |\n|---|---|---|---|---|\n")
        for r in report:
            f.write(f"| {r['name']} | {r['questions']} | {r['answers']} | {r['choice']} | {len(r['other'])} |\n")
        f.write("\nEach section has two files: `*-questions.md` (questions only) and `*-answers.md` (answer key with explanations). `bank.json` holds everything in structured form. `quiz.py` serves questions one at a time and tracks progress in `progress.json`; `CLAUDE.md` tells a Claude session how to run a practice session.\n")
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
