"""Practice helper: serves the next question, grades answers and stores progress in progress.json.

  py -3.12 -X utf8 pmp-mock/quiz.py next [N] [--section 01]   print the next N questions (no answers)
  py -3.12 -X utf8 pmp-mock/quiz.py check "A C B"             grade the pending questions; prints the answer and explanation for wrong ones
  py -3.12 -X utf8 pmp-mock/quiz.py stats                     progress per section
  py -3.12 -X utf8 pmp-mock/quiz.py review                    re-ask questions previously answered wrong
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BANK = json.load(open(os.path.join(HERE, "bank.json"), encoding="utf-8"))
PROGRESS = os.path.join(HERE, "progress.json")
CHOICE = [q for q in BANK if q["type"] == "choice"]


def load():
    if os.path.isfile(PROGRESS):
        return json.load(open(PROGRESS, encoding="utf-8"))
    return {"done": {}, "pending": [], "section": None}


def save(state):
    json.dump(state, open(PROGRESS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def show(q, index):
    multi = len(q["correct_letters"]) > 1
    print(f"### Question {index} — {q['section']} #{q['n']}" + (f" (select {len(q['correct_letters'])})" if multi else ""))
    print(q["stem"])
    for letter, text in q["options"].items():
        print(f"{letter}. {text}")
    print()


def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "next"
    state = load()
    if cmd in ("next", "review"):
        n = next((int(a) for a in args[1:] if a.isdigit() and len(a) < 3), 1)
        if "--section" in args:
            state["section"] = args[args.index("--section") + 1]
        pool = [q for q in CHOICE if not state["section"] or q["id"].startswith(state["section"])]
        if cmd == "review":
            picked = [q for q in pool if state["done"].get(q["id"], {}).get("ok") is False][:n]
        else:
            picked = [q for q in pool if q["id"] not in state["done"] and q["id"] not in state.get("skipped", [])][:n]
        if not picked:
            print("No more questions in this scope.")
            return
        state["pending"] = [q["id"] for q in picked]
        save(state)
        for i, q in enumerate(picked, 1):
            show(q, i)
    elif cmd == "check":
        given = re.findall(r"[A-Ha-h]+", " ".join(args[1:]))
        by_id = {q["id"]: q for q in BANK}
        pending = [by_id[i] for i in state["pending"]]
        if len(given) != len(pending):
            print(f"Expected {len(pending)} answer(s), got {len(given)}.")
            return
        right = 0
        for i, (q, g) in enumerate(zip(pending, given), 1):
            chosen = sorted(set(g.upper()))
            ok = chosen == sorted(q["correct_letters"])
            right += ok
            state["done"][q["id"]] = {"ok": ok, "chosen": "".join(chosen)}
            print(f"Question {i} ({q['section']} #{q['n']}): chose {''.join(chosen)} -> {'CORRECT' if ok else 'WRONG'}; answer {''.join(q['correct_letters'])}")
            if not ok:
                print("  QUESTION:", q["stem"])
                for letter, text in q["options"].items():
                    print(f"  {letter}. {text}")
                print("  SOURCE EXPLANATION:", q["explanation"])
        state["pending"] = []
        save(state)
        done = state["done"]
        print(f"This round {right}/{len(pending)}. Total: {sum(v['ok'] for v in done.values())}/{len(done)} correct, {len(CHOICE) - len(done)} questions left.")
    elif cmd == "stats":
        done = state["done"]
        print(f"Answered {len(done)}/{len(CHOICE)}; correct {sum(v['ok'] for v in done.values())}.")
        sections = {}
        for q in CHOICE:
            s = sections.setdefault(q["section"], [0, 0, 0])
            s[0] += 1
            if q["id"] in done:
                s[1] += 1
                s[2] += done[q["id"]]["ok"]
        for name, (total, did, ok) in sections.items():
            print(f"  {name}: answered {did}/{total}, correct {ok}")


if __name__ == "__main__":
    main()
