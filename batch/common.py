import re

def translate_text_to_japanese(client, text):
    system_message = "あなたはデジタルデータの長期保存の専門家であり、Archivematicaのドキュメントの日本語訳を担当しています。翻訳対象の文字列を.poファイル形式の文字列として返却します。翻訳作業では、コメントやmsgidから始まる文字列をそのまま保持し、msgstrに翻訳結果を入力します。また、:ref:タグや``で囲まれたコードなどの特殊フォーマットにも注意を払います。"

    user_message = text

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]

    model = "gpt-4-1106-preview"

    completion = client.chat.completions.create(
        model=model,
        messages=messages
    )

    choice = completion.choices[0]

    content = choice.message.content

    return content

def add_space_around_special_phrase(text):
    """
    特定のパターンに一致する文字列の前後に空白を追加し、
    テキストの可読性を向上させる。
    """
    # パターンを定義: 新しい段落の先頭や末尾にない、:ref:で始まる参照リンクまたは
    # 1つまたは2つのバッククォートで囲まれたインラインコード
    # （オプショナルなアンダースコアとバッククォートを含む）
    pattern = r"(?<!\n\n)(:ref:`[^`]+`|`{1,2}\S+?`_{0,1}`{0,1})(?!\n\n)"
    
    # パターンに一致する文字列の前後に空白を追加
    msgstr = re.sub(pattern, r" \1 ", text)

    # 「テキスト」_ 形式の文字列を「`テキスト`_」に変換（_で終わる場合に限る）
    msgstr = re.sub(r'「([^」]+)」_', r'`\1`_', msgstr)

    # バッククォートで囲まれ、末尾にアンダースコアがあるテキストの開始部分にのみスペースを追加
    # 既にスペースがあるか、行の先頭にある場合は除く
    msgstr = re.sub(r'(?<!^)(?<! )(`[^`]+`_)', r' \1', msgstr)

    # バッククォートで囲まれたテキストの終了部分（アンダースコアを含む）に、
    # 半角スペースがない場合にスペースを追加
    msgstr = re.sub(r'(`[^`]+`_)(?!\s)', r'\1 ', msgstr)

    # 連続する空白を1つにまとめる
    modified_text = re.sub(r' {2,}', ' ', msgstr)
    
    return modified_text.strip()

def desired_text(txt):
    """
    与えられたテキストから特定の部分を抽出し、整形する。
    """
    # "### START ###"が含まれている場合、それ以降のテキストを対象とする
    if "### START ###" in txt:
        txt = txt.split("### START ###")[1]

    txt = txt.strip()

    txt_fixed = ""

    lines = txt.split("\n")

    for i, line in enumerate(lines):
        # コードブロックの開始行を無視
        if i == 0 and "```" in line:
            continue

        # コードブロックの終了行を無視
        if line == "```":
            continue

        # 行が空でなく、引用符で始まらず、引用符で終わらない、
        # かつコメント行でない場合に処理
        if len(line) > 0 and not line.startswith("\"") and not line.endswith("\"") and not line.startswith("#"):
            spl = line.split("\"")
            # 引用符で囲む
            line = "\"" + spl[1] + "\""
        
        # msgidまたはmsgstrの行でない場合、コメント行でない場合、
        if not line.startswith("msgstr") and not line.startswith("#") and not line.startswith("msgid") and not line.startswith("\"") and not len(line.strip()) == 0:
            continue            

        txt_fixed += line + "\n"

    return txt_fixed.strip()

def create_batches(lines, max_tokens=258):
    """トータルがmax_tokens以下になるようにテキストのリストをバッチに分割する"""
    batches = []
    current_batch = []
    current_tokens = 0

    for line in lines:
        # 仮にトークン数を単語数として計算
        line_tokens = len(line.split())
        if current_tokens + line_tokens <= max_tokens:
            current_batch.append(line)
            current_tokens += line_tokens
        else:
            batches.append(current_batch)
            current_batch = [line]
            current_tokens = line_tokens
    # 最後のバッチを追加
    if current_batch:
        batches.append(current_batch)

    return batches