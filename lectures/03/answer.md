# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
  - 第1回の素のLLMは一般的な知識や推測に基づいて回答し、最新情報や講義固有のコンテキストを正確に反映できなかった。一方、エージェントは自律的に `search_glossary` ツールを呼び出して用語集から正確な定義を検索・参照し、該当する講義回（第2回）まで正確に特定して回答した。
- `--trace` で見えたツール呼び出し（ツール名と引数）：
  - `search_glossary({'query': 'LoRA'})`
  - `make_quiz({'lecture_number': 2})`
- 1つの質問での LLM 呼び出し回数（`requests`）：
  - 2回（1回目でツール呼び出しを決定し、ツール実行結果を受け取った後の2回目で最終回答を生成）
- 追加したツールと、docstring に書いた説明：
  - ツール名: `make_quiz`
  - docstring:
    ```python
    """指定した回の用語集から、ランダムに1問クイズ（用語の定義から用語名を当てさせる問題）を作成して返す。

    講義の復習や確認問題を出してほしいと頼まれたときに使う。

    Args:
        lecture_number: 講義の回数（1〜5の整数）
    """
    ```

## 宿題

- 取り組んだレベル：実装
- やったこと：
  - 学習記録をMarkdownファイルとして保存するツール `save_learning_log` を `app/tools.py` に追加した。
  - ファイル保存のような副作用（取り消しにくい操作）を安全に扱うため、`app/agent.py` で `requires_approval=True` を設定してツールを登録した。
  - Pydantic AI のエージェント出力型に `DeferredToolRequests` を追加し、CLI（`main()` 関数）側で実行直前にユーザーへ承認確認（y/n）を求める Human-in-the-Loop の対話フローを実装した。
  - 承認された場合のみ `DeferredToolResults` を渡してエージェントループを再開し、保存を実行させた。
- 結果：
  - `uv run python -m app.agent --trace "LoRAについてのまとめを学習記録として保存して"` を実行。
  - `[承認確認] ツール「save_learning_log」を実行しようとしています。` のプロンプトで `y` を入力すると、無事に `learning_log/LoRAについてのまとめ.md` が作成され、保存完了の回答が得られた（`n` を入力した場合は安全に中断されることも確認）。
  - `--trace` ログ:
    ```text
    [model] gemini-3.5-flash-lite
    [承認確認] ツール「save_learning_log」を実行しようとしています。
    引数: {'content': '【LoRA（Low-Rank Adaptation）のまとめ】\n...', 'title': 'LoRAのまとめ'}
    この操作を実行しますか？ (y/n): y
    LoRAについてのまとめを学習記録として保存しました！

    --- trace ---
    [tool call]   search_glossary({'query': 'LoRA'})
    [tool return] search_glossary -> [{"term": "LoRA", "lecture": 2, ...
    [tool call]   save_learning_log({'content': '...', 'title': 'LoRAについてのまとめ'})
    [tool return] save_learning_log -> 学習記録を保存しました: LoRAについてのまとめ.md…
    [usage] RunUsage(cost=Decimal('0.0003627'), details={'text_prompt_tokens': 1034}, input_text_tokens=1034, input_tokens=1034, output_tokens=21, requests=1, tool_calls=1)
    ```
- 気づき・疑問：
  - エージェントが外部環境（ファイルやDB）に直接書き込める構成にすると、モデルのハルシネーションや誤解釈による意図しないデータ破壊のリスクが極めて高くなる。
  - `requires_approval=True` と `DeferredToolRequests` を用いることで、「何を保存するか」の思考・生成はエージェントに任せつつ、「実際に確定するか」の決定権を人間に委ねる安全設計がシンプルに構築できた。
  - 本番のWebアプリやモバイルアプリ（AIDentなど）でも、DB更新や復習スケジュールの変更をエージェントに直接実行させず、フロントエンドで承認モーダル/カードUIを挟むパターンとして必須の設計になると感じた。