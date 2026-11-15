# PMP mock practice — session instructions

This folder is a personal PMP practice setup. The user practises multiple-choice questions with you, usually from their phone.

## How to run a practice session

The helper is plain Python with no dependencies. On Windows run it as `py -3.12 -X utf8 quiz.py ...`; on Linux/macOS or a cloud session use `python3 quiz.py ...` (same arguments). Run it from this folder.

- **Everything in English**: questions, feedback and explanations.
- **One question at a time.** Show one question, wait for the user's answer, give feedback, then show the next one. Never show several questions in one message.
- Get the next question with:
  `py -3.12 -X utf8 quiz.py next 1`
  Show the question and its options exactly as printed (it is the user's own study material), without the answer.
- When the user answers (a letter such as `B`, or several letters for multi-answer questions), check it with:
  `py -3.12 -X utf8 quiz.py check "B"`
- If the answer is **correct**: confirm in one short line and move on to the next question.
- If the answer is **wrong**, the user wants a DETAILED explanation with sources (they said the short version was hard to understand). The command prints the correct answer and the book's explanation; then:
  1. search the web (WebSearch) for the concept and cite 2–3 sources as markdown links, preferring PMI/PMBOK/Agile Practice Guide, Scrum Guide, then reputable PMP prep sites; say when a source is secondary;
  2. explain the concept in plain language with a concrete everyday example or analogy;
  3. go through the options: why the correct one fits the keywords in the question, why the user's choice is wrong, and briefly why the others are wrong;
  4. give a reusable "spot it on the exam" rule (keywords → answer);
  5. end with a "Sources:" list.
  Then move on to the next question.
- Do not reveal the correct answer before the user has answered. Do not read `bank.json` or the `*-answers.md` files to look ahead.
- Keep messages short: the user reads on a phone.

## Useful commands

| Command | Purpose |
|---|---|
| `py -3.12 -X utf8 quiz.py next 1` | next unanswered question in the current section |
| `py -3.12 -X utf8 quiz.py next 1 --section 03` | switch section (01 Agile & Hybrid, 02 Predictive, 03–05 Full Mock Exams 1–3) |
| `py -3.12 -X utf8 quiz.py check "A"` | grade the pending question and record it |
| `py -3.12 -X utf8 quiz.py review 1` | re-ask a question previously answered wrong |
| `py -3.12 -X utf8 quiz.py stats` | progress per section |

Progress is stored in `progress.json`, so a new session continues where the last one stopped. If the user asks for a summary, run `stats` and report score and weak areas.

## Files

- `bank.json` — all 719 questions (698 gradable multiple-choice) extracted from the user's PDF.
- `NN-*-questions.md` / `NN-*-answers.md` — questions and answer keys per section.
- `build_bank.py` — re-extracts the bank from the PDF in the parent folder.
