# Проверка главы книги.
#
# 1. Блоки ```python выполняются подряд в общем пространстве имён (как тетрадка).
#    Если сразу за блоком идёт блок ``` без языка — это ожидаемый вывод, он сверяется.
#    Ошибка печатается как "Тип: сообщение". Блок с "# не запускать" пропускается.
# 2. Задачи: раздел, заголовок которого начинается с "Задача". В каждой должны быть
#    **Решение.** и **Ответ.**; считается, у скольких задач есть проверка кодом.
# 3. Опасное для NotebookLM: < и > вне кода (в формулах писать \lt, \gt; цитата "> " в начале
#    строки разрешена), <буква внутри кода.
# 4. Сборка PDF: $ с пробелом у края, строка --- без пустой строки после, четвёртый уровень заголовков.
# 5. Штампы и отговорки из гайда.
#
# Запуск: python сборка/check.py главы/Т09_....md (обычно через python сборка/build.py)
import contextlib, io, os, re, sys, textwrap, time

path = sys.argv[1]
src = open(path, encoding="utf-8").read()
FENCE = re.compile(r"^([ \t]*)```(\{[^}\n]*\}|[\w-]*)[ \t]*\n(.*?)^\1```[ \t]*$", re.S | re.M)
blocks = [(m.start(), m.group(2).strip(), textwrap.dedent(m.group(3))) for m in FENCE.finditer(src)]
spans = [(m.start(), m.end()) for m in FENCE.finditer(src)]
infence = lambda p: any(a <= p < b for a, b in spans)
bad = 0
warn = 0


def problem(text):
    global bad
    bad += 1
    print("--- " + text + "\n")


def note(text):
    global warn
    warn += 1
    print("--- предупреждение: " + text + "\n")


def lineno(pos):
    return src.count("\n", 0, pos) + 1


ns = {"__name__": "__main__"}
nb = 0
t0 = time.time()
for k, (pos, lang, code) in enumerate(blocks):
    if lang != "python" or "# не запускать" in code:
        continue
    nb += 1
    buf = io.StringIO()
    tb = time.time()
    with contextlib.redirect_stdout(buf):
        try:
            exec(compile(code, f"block{k}", "exec"), ns)
        except Exception as e:
            print(f"{type(e).__name__}: {e}")
    if time.time() - tb > 20:
        note(f"блок в строке {lineno(pos)} считается {time.time() - tb:.0f} с (лимит 20 с)")
    got = buf.getvalue().rstrip()
    nxt = blocks[k + 1] if k + 1 < len(blocks) else None
    if nxt and nxt[1] == "":
        want = nxt[2].rstrip()
        if got != want:
            problem(f"РАСХОЖДЕНИЕ в блоке, строка {lineno(pos)}\n{code.rstrip()}\n--- ожидалось:\n{want}\n--- получено:\n{got}")
    else:
        problem(f"у блока python в строке {lineno(pos)} нет следующего за ним блока вывода ```")

heads = [(m.start(), len(m.group(1)), m.group(2)) for m in re.finditer(r"^(#{1,6}) +(.*)$", src, re.M) if not infence(m.start())]
for pos, lv, title in heads:
    if lv >= 4:
        problem(f"заголовок четвёртого уровня в строке {lineno(pos)}: {title}")
tasks = checked = 0
for i, (pos, lv, title) in enumerate(heads):
    if not title.startswith("Задача"):
        continue
    end = next((p for p, l, _ in heads[i + 1:] if l <= lv), len(src))
    body = src[pos:end]
    tasks += 1
    if "**Решение.**" not in body and "**Решение**" not in body:
        problem(f"в задаче «{title}» нет **Решение.**")
    if "**Ответ.**" not in body and "**Ответ**" not in body:
        problem(f"в задаче «{title}» нет **Ответ.**")
    if "```python" in body:
        checked += 1

lines = src.splitlines()
offs = [0]
for l in lines:
    offs.append(offs[-1] + len(l) + 1)
ang, angcode, dollar, rule = [], [], [], []
for i, l in enumerate(lines):
    p = offs[i]
    if infence(p):
        if re.search(r"<[A-Za-z/!?_]", l):
            angcode.append(i + 1)
        continue
    t = re.sub(r"`[^`]*`", "", l)
    t = re.sub(r"^\s*(>\s*)+", "", t)
    if "<" in t or ">" in t:
        ang.append(i + 1)
    if l.strip() == "---" and i + 1 < len(lines) and lines[i + 1].strip() and not infence(offs[i + 1]):
        rule.append(i + 1)
    for m in re.finditer(r"(?<![\\$])\$(?!\$)([^$]+?)(?<!\\)\$(?!\$)", t):
        b = m.group(1)
        if b != b.strip():
            dollar.append(i + 1)
            break
cyr = []
nocode = re.sub(r"```.*?```", lambda m: "\n" * m.group(0).count("\n"), src, flags=re.S)
nocode = re.sub(r"`[^`\n]*`", "", nocode)
for m in re.finditer(r"\$\$(.+?)\$\$|\$([^$\n]+?)\$", nocode, re.S):
    body = m.group(1) or m.group(2)
    stripped = body
    for _ in range(3):
        stripped = re.sub(r"\\(text|mathrm|textrm|textit|textbf|operatorname|mbox)\{[^{}]*\}", "", stripped)
    if re.search(r"[А-Яа-яЁё]", stripped):
        cyr.append(nocode.count("\n", 0, m.start()) + 1)
if cyr:
    problem(f"кириллица в формуле вне \\text{{}} (в PDF пропадёт), строки: {cyr[:30]}")
if ang:
    problem(f"< или > вне кода (писать \\lt, \\gt, словами или ≤ ≥), строки: {ang[:30]}")
if angcode:
    problem(f"<буква в коде (ставить пробел: x < y), строки: {angcode[:30]}")
if dollar:
    problem(f"пробел у края формулы $ ... $, строки: {dollar[:30]}")
if rule:
    problem(f"после --- нет пустой строки, строки: {rule[:30]}")

STAMPS = ["очевидно", "легко видеть", "легко показать", "давайте", "стоит отметить", "стоит подчеркнуть",
          "важно понимать", "важно отметить", "мощный инструмент", "мощное средство", "элегантн", "краеугольн", "в современном мире", "не секрет",
          "погрузимся", " опустим ", "докажите самостоятельно", "оставляем читателю", "нетрудно видеть"]
low = re.sub(r"```.*?```", "", src, flags=re.S).lower()
found = [s for s in STAMPS if s in low]
if found:
    note("штампы или отговорки: " + ", ".join(f"«{s}» ×{low.count(s)}" for s in found))
if re.search(r"P\(\s*[A-Z]\s*[A-Z]\s*\)", re.sub(r"```.*?```", "", src, flags=re.S)):
    note("похоже на слитную запись пересечения P(AB): писать P(A\\cap B)")

name = os.path.basename(path)
print(f"{name}: слов {len(re.sub(r'```.*?```', '', src, flags=re.S).split())}, блоков python {nb} ({time.time() - t0:.0f} с), "
      f"задач {tasks}, из них с проверкой кодом {checked}, ошибок {bad}, предупреждений {warn}")
sys.exit(1 if bad else 0)
