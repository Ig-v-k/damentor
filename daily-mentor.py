import os
import json
import random
import subprocess
import difflib
from pathlib import Path
import requests
from dotenv import load_dotenv

# --- НАСТРОЙКИ ---
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")  # Резерв, когда кончится Copilot
IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
ALLOWED_EXT = {".py", ".js", ".ts", ".tsx", ".go", ".rs", ".java", ".php", ".rb", ".md"}


def run_cmd(cmd: list[str], input_text: str | None = None) -> tuple[int, str]:
    res = subprocess.run(cmd, input=input_text, text=True, capture_output=True)
    return res.returncode, (res.stdout + "\n" + res.stderr).strip()


def ask_ai(prompt: str) -> str:
    """Сначала пробует GitHub Copilot CLI, при ошибке/лимите уходит на DeepSeek."""
    try:
        code, out = run_cmd(["copilot", "-p", prompt])
        if code == 0 and out and "quota" not in out.lower() and "limit" not in out.lower():
            return out
    except FileNotFoundError:
        pass

    if not DEEPSEEK_API_KEY:
        raise RuntimeError("Copilot недоступен/кончились кредиты, а DEEPSEEK_API_KEY не задан.")

    resp = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
        json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def pick_small_context() -> tuple[str, str]:
    """Берёт README + один небольшой файл проекта (малая порция)."""
    readme = ""
    for name in ("README.md", "readme.md"):
        if Path(name).exists():
            readme = Path(name).read_text(encoding="utf-8", errors="ignore")[:2500]
            break

    files = [
        p for p in Path(".").rglob("*")
        if p.is_file()
        and p.suffix in ALLOWED_EXT
        and not any(part in IGNORE_DIRS for part in p.parts)
        and p.stat().st_size < 15_000
    ]
    if not files:
        raise RuntimeError("Не нашёл подходящих файлов в репозитории.")

    target = random.choice(files)
    content = target.read_text(encoding="utf-8", errors="ignore")[:4000]
    return str(target), f"README (суть проекта):\n{readme}\n\nФайл {target}:\n{content}"


def extract_json(raw: str) -> dict:
    start, end = raw.find("{"), raw.rfind("}") + 1
    if start == -1 or end <= start:
        raise ValueError("ИИ не вернул ответ в формате JSON.")
    result = json.loads(raw[start:end])
    if not isinstance(result, dict):
        raise ValueError("Ожидался JSON-объект от ИИ.")
    return result


def main():
    filepath, context = pick_small_context()

    # Шаг 1: Находим 1 улучшение под архитектуру / бизнес-цели
    idea_prompt = f"""
Ты продуктовый и архитектурный наставник проекта.
Изучи контекст и найди ОДНО небольшое, но ценное улучшение (не мелочь вроде пробелов, а пользу для пользователя, бизнес-цели или чистоты архитектуры).
Пиши максимально коротко, простым человеческим языком, почти без технических терминов и без кусков кода.

Верни строго JSON:
{{
  "issue_title": "Короткий заголовок задачи (до 60 символов)",
  "issue_body": "2-3 простых предложения: что сейчас не так и какую пользу даст улучшение.",
  "human_pitch": "Очень короткое предложение для владельца (3-4 строки максимум): в чём идея, зачем это бизнесу/пользователю и что изменится."
}}

Контекст:
{context}
"""
    idea = extract_json(ask_ai(idea_prompt))
    for field in ("issue_title", "issue_body", "human_pitch"):
        if not isinstance(idea.get(field), str) or not idea[field].strip():
            raise ValueError(f"ИИ вернул некорректное поле: {field}")

    # Шаг 2: Создаём Issue на GitHub
    code, issue_out = run_cmd([
        "gh", "issue", "create",
        "--title", idea["issue_title"],
        "--body", idea["issue_body"],
    ])
    if code != 0:
        print(f"Не удалось создать Issue: {issue_out}")
        return

    issue_url = issue_out.splitlines()[-1].strip()
    issue_num = issue_url.rstrip("/").split("/")[-1]

    # Шаг 3: Показываем человеку короткую выжимку
    print("\n" + "=" * 50)
    print(f"📌 Создан Issue #{issue_num}: {idea['issue_title']}")
    print(f"🔗 {issue_url}\n")
    print(idea["human_pitch"])
    print("=" * 50)

    ans = input("\nВнедрить это изменение сейчас? [y — да / n — оставить Issue на потом]: ").strip().lower()
    if ans != "y":
        print("Ок, Issue сохранён в репозитории. Вернёшься к нему позже.")
        return

    # Шаг 4: Решаем задачу на основе созданного Issue
    fix_prompt = f"""
Реши задачу из GitHub Issue #{issue_num} в файле {filepath}.
Название: {idea['issue_title']}
Описание: {idea['issue_body']}

Правила:
1. Сделай минимальное, аккуратное изменение в {filepath}.
2. Верни строго JSON:
{{
  "updated_content": "ПОЛНЫЙ обновлённый текст файла {filepath}",
  "summary": "1-2 простых предложения на человеческом языке, что сделано."
}}

Текущий файл {filepath}:
{Path(filepath).read_text(encoding="utf-8", errors="ignore")}
"""
    fix = extract_json(ask_ai(fix_prompt))
    updated_content = fix.get("updated_content")
    summary = fix.get("summary")
    if not isinstance(updated_content, str) or not isinstance(summary, str) or not summary.strip():
        raise ValueError("ИИ вернул некорректный результат изменения файла.")

    current_content = Path(filepath).read_text(encoding="utf-8", errors="ignore")
    diff = difflib.unified_diff(
        current_content.splitlines(),
        updated_content.splitlines(),
        fromfile=f"{filepath} (текущая версия)",
        tofile=f"{filepath} (предложение ИИ)",
        lineterm="",
    )
    print("\n".join(diff))
    apply = input("\nПрименить показанные изменения? [y — применить / n — отменить]: ").strip().lower()
    if apply != "y":
        print(f"Файл не изменён. Issue #{issue_num} оставлен открытым.")
        return

    Path(filepath).write_text(updated_content, encoding="utf-8")
    print(f"\nИзменения записаны в {filepath}: {summary}")
    print(f"Проверь diff перед коммитом. Issue #{issue_num} оставлен открытым.")


if __name__ == "__main__":
    main()