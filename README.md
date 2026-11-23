# Damentor

[![CI](https://github.com/Ig-v-k/damentor/actions/workflows/ci.yml/badge.svg)](https://github.com/Ig-v-k/damentor/actions/workflows/ci.yml)
[![GitHub release](https://img.shields.io/github/v/release/Ig-v-k/damentor)](https://github.com/Ig-v-k/damentor/releases)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-Apache--2.0-blue)](./LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/Ig-v-k/damentor?style=social)](https://github.com/Ig-v-k/damentor/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Ig-v-k/damentor)](https://github.com/Ig-v-k/damentor/network/members)
[![GitHub issues](https://img.shields.io/github/issues/Ig-v-k/damentor)](https://github.com/Ig-v-k/damentor/issues)
[![Last commit](https://img.shields.io/github/last-commit/Ig-v-k/damentor)](https://github.com/Ig-v-k/damentor/commits/main)
[![Repository size](https://img.shields.io/github/repo-size/Ig-v-k/damentor)](https://github.com/Ig-v-k/damentor)

Небольшой Python-скрипт, который анализирует один файл проекта, предлагает улучшение, создаёт для него GitHub Issue и при подтверждении предлагает изменение файла.

## Статус проекта

Проект находится в активной разработке. Основной сценарий стабилен по назначению, но API и структура файлов могут ещё меняться.

## License

Проект распространяется по лицензии [Apache License 2.0](./LICENSE). Вы можете скачивать, использовать и изменять код без предварительного разрешения, в том числе распространять изменённые версии, при соблюдении условий лицензии. При распространении нужно сохранить исходные уведомления об авторских правах и указать, какие файлы были изменены.

Авторство исходного кода остаётся за его правообладателем; авторы изменений сохраняют авторство своих вкладов. Лицензия не требует запрашивать разрешение на каждое изменение.

## Требования

- Python 3.10 или новее
- GitHub CLI (`gh`), авторизованный для нужного репозитория
- Git-репозиторий с настроенным `origin`, если нужно создавать Issues
- Copilot CLI (необязательно); DeepSeek API используется как резервный вариант

## Установка в Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Откройте `.env` и задайте `DEEPSEEK_API_KEY`, если планируете использовать DeepSeek. Ключ хранится только локально в `.env`, который исключён из Git. Не вставляйте настоящий ключ в Python-файл, README, Issue или коммит. Если ключ уже попал в GitHub, отзовите его у провайдера и создайте новый.

Установите и авторизуйте `gh` и при необходимости Copilot CLI отдельно. Скрипту требуется запуск из корня GitHub-репозитория, где доступно создание Issues.

## Запуск

```powershell
python .\daily-mentor.py
```

Скрипт отправляет README и содержимое выбранного файла внешнему ИИ-сервису (Copilot CLI или DeepSeek). Не запускайте его в проекте с конфиденциальным кодом или данными, которые нельзя передавать этим сервисам. После создания Issue скрипт покажет предложенный diff; файл изменится только после отдельного подтверждения. Коммит и закрытие Issue выполняются вручную после проверки изменений.

## Ежедневный репорт

`daily-report.py` — отдельный сценарий: каждый обычный запуск создаёт новый короткий feature/bug Issue в указанном GitHub-репозитории и не изменяет файлы. Скрипт автоматически задаёт тип `Feature`/`Bug`, label `enhancement`/`bug` и назначает Issue текущему пользователю (`@me`). Дополнительные labels, проект и milestone можно задать параметрами `--label`, `--project` и `--milestone`; `--label` можно указывать несколько раз. В заголовке используются ASCII-маркеры `[D]` (daily), `[F]` (feature) или `[B]` (bug) и дата. Для ручного запуска с пропуском, если репорт за сегодня уже есть, укажите `--skip-existing`.

Однократный запуск:

```powershell
python .\daily-report.py --project-dir "C:\path\to\your\project"
```

Пример с дополнительными полями Issue:

```powershell
python .\daily-report.py --project-dir "C:\path\to\your\project" --label "daily-report" --project "Roadmap" --milestone "Q1"
```

Для ежедневного запуска от имени текущего пользователя зарегистрируйте отдельную задачу Windows Task Scheduler для этого проекта:

```powershell
python .\daily-report.py --project-dir "C:\path\to\your\project" --install-schedule --time 09:00 --provider auto
```

По умолчанию задача запускается ежедневно в 09:00 по местному времени и также при следующем входе в Windows, если компьютер пропустил расписание. Имя задачи содержит имя папки проекта и короткий идентификатор; повторный запуск команды установки обновляет расписание и удаляет старую задачу с прежним форматом имени. Параметры assignee, labels, project и milestone сохраняются в расписании. Для добавления в project также требуется scope `project` (`gh auth refresh -s project`). Запланированный запуск пропускает создание, если репорт за сегодня уже существует; если компьютер выключен весь день, отдельный репорт за пропущенную дату не создаётся. В `auto` сначала используется Copilot CLI, запущенный в целевом проекте, затем DeepSeek с `DEEPSEEK_API_KEY` из переменной окружения или `.env` этого проекта. Нужны авторизованный `gh` и права создавать Issues. Расписание для этого проекта можно удалить командой `python .\daily-report.py --project-dir "C:\path\to\your\project" --uninstall-schedule`.

Если при регистрации задачи появляется код `0x80070005` (отказано в доступе), повторите команду установки из PowerShell, запущенного от имени администратора. Если отказ повторяется, проверьте разрешения Task Scheduler или обратитесь к администратору компьютера.

## Ежедневный pull request

`daily-pr.py` берёт открытый ежедневный репорт (Issue с заголовком `[D][F] …` или `[D][B] …`), у которого ещё нет pull request, и предлагает для него изменение одного файла. По умолчанию выбирается самый старый такой Issue, созданный текущим пользователем (`--author @me`), конкретный Issue можно указать через `--issue`. ИИ сначала выбирает файл из списка небольших файлов проекта, затем возвращает его обновлённое содержимое. Скрипт создаёт ветку `damentor/issue-<номер>` от базовой ветки (по умолчанию ветка репозитория по умолчанию, иначе `--base`), коммитит изменение, пушит его в `origin` и открывает PR с `Closes #<номер>`, назначенный на `@me`.

Работа идёт во временном `git worktree` от свежей `origin/<base>`, поэтому текущая ветка и незакоммиченные изменения в проекте не затрагиваются. Временный worktree и локальная ветка удаляются после запуска. PR не сливается автоматически: проверьте изменение перед merge. Issues других авторов по умолчанию не обрабатываются, потому что их текст отправляется ИИ и может содержать вредные инструкции.

Сначала посмотреть предлагаемый diff без пуша и без создания PR:

```powershell
python .\daily-pr.py --project-dir "C:\path\to\your\project" --dry-run
```

Создать PR для конкретного Issue как черновик:

```powershell
python .\daily-pr.py --project-dir "C:\path\to\your\project" --issue 12 --draft --label "daily-pr"
```

Ежедневный запуск (по умолчанию в 10:00, после `daily-report.py`; при пропуске срабатывает после следующего входа в Windows, а если PR за сегодня уже есть, запуск пропускается):

```powershell
python .\daily-pr.py --project-dir "C:\path\to\your\project" --install-schedule --time 10:00 --provider auto
python .\daily-pr.py --project-dir "C:\path\to\your\project" --uninstall-schedule
```

Нужны авторизованный `gh` с правом создавать PR, право push в `origin` и настроенные `git user.name`/`user.email`. Как и в других сценариях, текст Issue, README и выбранный файл отправляются Copilot CLI или DeepSeek.
