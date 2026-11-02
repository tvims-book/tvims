"""Сборка книги в PDF. Работает одинаково на Windows, Linux и macOS.

    python сборка/build.py главы/00_введение.md   PDF одной главы (и открыть его)
    python сборка/build.py --check главы/00_введение.md   только проверка главы
    python сборка/build.py --all                            вся книга
    python сборка/build.py --ci                             все главы и книга, без открытия (для GitHub)

PDF складываются в папку pdf/ в корне репозитория.
Нужны: pandoc 3.x, XeLaTeX (TeX Live или MiKTeX), Python 3 с numpy, scipy, sympy, matplotlib.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "сборка"
CHAPTERS = ROOT / "главы"
OUT = ROOT / "pdf"
TITLE = "Теория вероятностей и математическая статистика"
AUTHOR = r"Арсений Синаков, Ольга Кривохижина\\ {\small при участии Claude (Anthropic) и Gemini (Google)}"
BOOK_PDF = "tvims-book.pdf"
TRANSLIT = {"П": "P", "Т": "T", "С": "S"}


def code(path):
    return path.name.split("_")[0]


def ascii_name(path):
    c = code(path)
    return "".join(TRANSLIT.get(ch, ch) for ch in c) + ".pdf"


def is_stat(path):
    return code(path).startswith("С")


def book_order():
    codes = [l.strip() for l in (BUILD / "порядок.txt").read_text(encoding="utf-8").splitlines()]
    codes = [c for c in codes if c and not c.startswith("#")]
    files = []
    for c in codes:
        files += sorted(CHAPTERS.glob(f"{c}_*.md"))
    return files


def pandoc_highlight_args():
    out = subprocess.run(["pandoc", "--version"], capture_output=True, text=True).stdout
    m = re.search(r"pandoc\S* (\d+)\.(\d+)", out)
    new = m and (int(m.group(1)), int(m.group(2))) >= (3, 8)
    return ["--syntax-highlighting=tango"] if new else ["--highlight-style=tango"]


def header_files(tmp, stat_from_start):
    fonts = (BUILD / "шрифты").as_posix() + "/"
    head = tmp / "fonts.tex"
    head.write_text(
        "\\newcommand{\\fontdir}{" + fonts + "}\n"
        "\\setmainfont{cmunrm.otf}[Path=\\fontdir,BoldFont=cmunbx.otf,ItalicFont=cmunti.otf,BoldItalicFont=cmunbi.otf]\n"
        "\\setsansfont{cmunss.otf}[Path=\\fontdir,BoldFont=cmunsx.otf]\n"
        "\\setmonofont{DejaVuSansMono.ttf}[Path=\\fontdir,Scale=0.84]\n",
        encoding="utf-8",
    )
    args = ["-H", str(head), "-H", str(BUILD / "style.tex")]
    if stat_from_start:
        q = tmp / "qed_stat.tex"
        q.write_text("\\AtBeginDocument{\\qedstat}\n", encoding="utf-8")
        args += ["-H", str(q)]
    return args


def run_pandoc(src_args, out_pdf, tmp, stat_from_start, extra=()):
    cmd = (
        ["pandoc", "-f", "markdown+lists_without_preceding_blankline-yaml_metadata_block"]
        + src_args
        + ["-V", "documentclass=article", "--pdf-engine=xelatex", "-V", "lang=ru",
           "-V", "colorlinks", "-V", "linkcolor=codeframe"]
        + header_files(tmp, stat_from_start)
        + ["--lua-filter", str(BUILD / "boxes.lua"), "--toc", "--toc-depth=2",
           "-V", "toc-title=Содержание", "-V", "geometry:margin=2.3cm", "-V", "fontsize=11pt",
           f"--resource-path={CHAPTERS}"]
        + pandoc_highlight_args()
        + list(extra)
        + ["-o", str(out_pdf)]
    )
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    log = (r.stdout or "") + (r.stderr or "")
    missing = sorted(set(re.findall(r"Missing character: There is no (\S+)", log)))
    if r.returncode != 0 or not out_pdf.exists():
        print(log[-3000:])
        print(f"ОШИБКА сборки: {out_pdf.name}")
        return False
    if missing:
        print("Нет символов в шрифте:", " ".join(missing))
    print(f"Готово: {out_pdf}")
    return True


def check(path):
    r = subprocess.run([sys.executable, str(BUILD / "check.py"), str(path)], cwd=ROOT)
    return r.returncode == 0


def build_chapter(path, out_pdf):
    with tempfile.TemporaryDirectory() as t:
        return run_pandoc([str(path)], out_pdf, Path(t), is_stat(path))


def build_book(out_pdf):
    files = book_order()
    parts = []
    stat_started = False
    for f in files:
        text = f.read_text(encoding="utf-8")
        if is_stat(f) and not stat_started:
            text = "```{=latex}\n\\qedstat\n```\n\n" + text
            stat_started = True
        parts.append(text)
    body = "\n\n\\newpage\n\n".join(parts)
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        src = tmp / "book.md"
        src.write_text(body, encoding="utf-8")
        return run_pandoc([str(src), "-s"], out_pdf, tmp, False,
                          ["-M", f"title={TITLE}", "-V", f"author={AUTHOR}"])


def open_pdf(pdf):
    try:
        if sys.platform.startswith("win"):
            os.startfile(pdf)  # noqa
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(pdf)])
        else:
            subprocess.Popen(["xdg-open", str(pdf)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print("Не удалось открыть PDF:", e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("chapter", nargs="?")
    ap.add_argument("--check", action="store_true", help="только проверить главу")
    ap.add_argument("--all", action="store_true", help="собрать всю книгу")
    ap.add_argument("--ci", action="store_true", help="все главы и книга, без открытия")
    ap.add_argument("--no-open", action="store_true")
    a = ap.parse_args()
    for tool in ("pandoc", "xelatex"):
        if not a.check and shutil.which(tool) is None:
            sys.exit(f"Не найден {tool}. Как установить — в README.md.")
    OUT.mkdir(exist_ok=True)
    if a.ci:
        ok = all([check(f) for f in book_order()])
        ok = all([build_chapter(f, OUT / ascii_name(f)) for f in book_order()]) and ok
        ok = build_book(OUT / BOOK_PDF) and ok
        sys.exit(0 if ok else 1)
    if a.all:
        ok = build_book(OUT / BOOK_PDF)
        if ok and not a.no_open:
            open_pdf(OUT / BOOK_PDF)
        sys.exit(0 if ok else 1)
    if not a.chapter:
        ap.error("укажите файл главы или --all")
    path = Path(a.chapter).resolve()
    if path.suffix != ".md":
        sys.exit("Откройте файл главы (.md) и запустите сборку снова.")
    ok = check(path)
    if a.check:
        sys.exit(0 if ok else 1)
    if not ok:
        print("Проверка нашла ошибки (см. выше). PDF всё равно собираю.")
    pdf = OUT / (path.stem + ".pdf")
    if build_chapter(path, pdf) and not a.no_open:
        open_pdf(pdf)


if __name__ == "__main__":
    main()
