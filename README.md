# Теория вероятностей и математическая статистика

Учебник по теории вероятностей и математической статистике с задачами и решениями.

Авторы: Арсений Синаков, Ольга Кривохижина. Книга написана при участии Claude (Anthropic) и Gemini (Google).

**[Скачать PDF](../../releases/download/latest/tvims-book.pdf)**

Книгу мы пока только пишем: готово введение, остальные главы будут добавляться по мере готовности. PDF по ссылке выше всегда собран из самой свежей версии текста.

Книгу можно читать, копировать и распространять бесплатно с указанием авторов, но не продавать ([CC BY-NC-SA 4.0](LICENSE)).

---

<details>
<summary><b>Для тех, кто правит текст</b></summary>

Текст книги лежит в папке `главы/`: каждая глава — это отдельный файл Markdown с формулами LaTeX.

Порядок работы:

1. Перед началом сделать Pull, чтобы получить чужие правки.
2. Поправить главу.
3. Сделать Commit и Push. Через пару минут GitHub сам пересоберёт PDF.

Чтобы посмотреть PDF главы у себя, не дожидаясь GitHub:

1. Открыть в VS Code всю папку репозитория (File → Open Folder), а не отдельный файл. При первом открытии VS Code спросит, доверяете ли вы автору папки: ответить «Yes, I trust the authors», иначе сборка не запустится.
2. Открыть нужную главу из `главы/` и, находясь в ней, нажать Ctrl+Shift+B. Проверка и сборка пойдут в панели внизу, готовый PDF откроется сам.

Для этого нужно один раз установить программы:

- Windows: [Python](https://www.python.org/downloads/) (при установке отметить «Add python.exe to PATH»), [pandoc](https://pandoc.org/installing.html), [MiKTeX](https://miktex.org/download). Потом в терминале: `pip install -r requirements.txt`.
- Ubuntu: `sudo apt install python3-pip texlive-xetex texlive-latex-extra texlive-lang-cyrillic texlive-fonts-recommended texlive-science` и `pip install -r requirements.txt`. Pandoc лучше поставить свежий, со [страницы релизов](https://github.com/jgm/pandoc/releases).

Шрифты лежат в репозитории, ставить их не нужно. Сборка из терминала: `python сборка/build.py главы/00_введение.md`, вся книга: `python сборка/build.py --all`.

</details>
