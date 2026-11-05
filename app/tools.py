"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""

import json
import random
from functools import cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LOG_DIR = Path(__file__).resolve().parent.parent / "learning_log"
MAX_RESULTS = 3


@cache
def load_glossary() -> list[dict]:
    with open(DATA_DIR / "glossary.json", encoding="utf-8") as f:
        return json.load(f)["terms"]


def _normalize(text: str) -> str:
    return text.casefold().replace(" ", "").replace(" ", "")


def _names(entry: dict) -> list[str]:
    return [_normalize(entry["term"]), _normalize(entry["id"])] + [
        _normalize(a) for a in entry["aliases"]
    ]


def search_glossary(query: str) -> str:
    """講座の用語集から用語を検索し、定義と、どの回で扱うかを返す。

    AIエンジニアリングの用語や、この講座（AIE2026）に固有の言葉について
    答える前に使うこと。query には調べたい用語を1つだけ入れる（例: "LoRA"）。
    """
    q = _normalize(query)
    if not q:
        return "検索語が空です。調べたい用語を1つ指定してください。"
    glossary = load_glossary()

    exact = [e for e in glossary if q in _names(e)]
    # 「r」のような短い別名が何にでも当たらないよう、名前側が短いものは除く
    partial = [
        e for e in glossary
        if e not in exact and any(q in n or (len(n) >= 3 and n in q) for n in _names(e))
    ]
    in_definition = [
        e for e in glossary
        if e not in exact and e not in partial and q in _normalize(e["definition"])
    ]
    hits = (exact + partial + in_definition)[:MAX_RESULTS]

    if not hits:
        return f"用語集に「{query}」は見つかりませんでした。"
    return json.dumps(
        [
            {
                "term": e["term"],
                "lecture": e["lecture"],
                "definition": e["definition"],
                "related": e["related"],
            }
            for e in hits
        ],
        ensure_ascii=False,
    )


def get_lecture_summary(lecture: int) -> str:
    """指定した回（1始まりの整数）の講義の要点を返す。

    「第3回では何を学ぶ？」のように、回の内容や関係を聞かれたときに使う。
    """
    path = DATA_DIR / "lectures" / f"{lecture:02d}.md"
    if not path.exists():
        available = sorted(p.stem for p in (DATA_DIR / "lectures").glob("*.md"))
        return f"第{lecture}回の要点はまだありません。用意されている回: {', '.join(available)}"
    return path.read_text(encoding="utf-8")


def make_quiz(lecture_number: int) -> str:
    """指定した回の用語集から、ランダムに1問クイズ（用語の定義から用語名を当てさせる問題）を作成して返す。

    講義の復習や確認問題を出してほしいと頼まれたときに使う。

    Args:
        lecture_number: 講義の回数（1〜5の整数）
    """
    terms = [
        entry for entry in load_glossary()
        if entry.get("lecture") == lecture_number
    ]
    if not terms:
        return f"第{lecture_number}回の用語は見つかりませんでした。"

    target = random.choice(terms)
    return (
        f"【第{lecture_number}回 クイズ】\n"
        f"問題: 次の定義に当てはまる用語は何でしょうか？\n"
        f"「{target['definition']}」\n\n"
        f"（正解: {target['term']}）"
    )


def save_learning_log(title: str, content: str) -> str:
    """学習した内容やまとめを記録ファイルとして保存する。

    ユーザーから学習記録の保存を依頼されたときや、まとめを保存したいときに使う。

    Args:
        title: 保存する記録のタイトル（ファイル名の一部になります）
        content: 保存する学習内容やまとめの本文
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    # ファイル名として安全な文字列に簡易変換
    safe_title = "".join(c for c in title if c.isalnum() or c in ("-", "_")).strip() or "log"
    file_path = LOG_DIR / f"{safe_title}.md"
    file_path.write_text(content, encoding="utf-8")
    return f"学習記録を保存しました: {file_path.name}"