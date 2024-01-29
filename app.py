from flask import Flask, request, jsonify, render_template
import openai
import os
import traceback

app = Flask(__name__)

words_played = []

openai.organization = os.environ.get("OPENAI_ORGANIZATION")
openai.api_key = os.getenv("OPENAI_API_KEY")

def katakana_to_hiragana(word):
    return "".join(chr(ord(char) - 96) if "ァ" <= char <= "ン" else char for char in word)

def adjust_last_character(word):
  # 子音と母音の変換ルール
    consonant_to_vowel = {
        'か': 'あ', 'き': 'い', 'く': 'う', 'け': 'え', 'こ': 'お',
        'さ': 'あ', 'し': 'い', 'す': 'う', 'せ': 'え', 'そ': 'お',
        'た': 'あ', 'ち': 'い', 'つ': 'う', 'て': 'え', 'と': 'お',
        'な': 'あ', 'に': 'い', 'ぬ': 'う', 'ね': 'え', 'の': 'お',
        'は': 'あ', 'ひ': 'い', 'ふ': 'う', 'へ': 'え', 'ほ': 'お',
        'ま': 'あ', 'み': 'い', 'む': 'う', 'め': 'え', 'も': 'お',
        'や': 'あ', 'ゆ': 'う', 'よ': 'お',
        'ら': 'あ', 'り': 'い', 'る': 'う', 'れ': 'え', 'ろ': 'お',
        'わ': 'あ', 'を': 'お',
        'が': 'あ', 'ぎ': 'い', 'ぐ': 'う', 'げ': 'え', 'ご': 'お',
        'ざ': 'あ', 'じ': 'い', 'ず': 'う', 'ぜ': 'え', 'ぞ': 'お',
        'だ': 'あ', 'ぢ': 'い', 'づ': 'う', 'で': 'え', 'ど': 'お',
        'ば': 'あ', 'び': 'い', 'ぶ': 'う', 'べ': 'え', 'ぼ': 'お',
        'ぱ': 'あ', 'ぴ': 'い', 'ぷ': 'う', 'ぺ': 'え', 'ぽ': 'お',
    }

    hiragana_small = "ぁぃぅぇぉっゃゅょ"
    hiragana_large = "あいうえおつやゆよ"
    katakana_small = "ァィゥェォッャュョ"
    katakana_large = "アイウエオツヤユヨ"

  # 「ー」で終わる場合
    if word[-1] == 'ー':
        last_char = word[-2]
        hiragana_char = katakana_to_hiragana(last_char)

        if hiragana_char in consonant_to_vowel:
            return consonant_to_vowel[hiragana_char]
        else:
            return hiragana_char

    # 拗音で終わる場合（例：'しゃ', 'ちゃ', 'にゃ', 'ひゃ', 'みゃ', 'りゃ' など）
    elif word[-1] in hiragana_small[5:]:  # 拗音部分のみをチェック
        return hiragana_large[hiragana_small.index(word[-1])]

    # 通常の処理
    else:
        last_char = word[-1]
        if last_char in hiragana_small:
            return hiragana_large[hiragana_small.index(last_char)]
        else:
            return last_char
            
def generate_shiritori_response(prompt):
    try:
        response = openai.Completion.create(
          model="gpt-3.5-turbo",  # 使用するモデルを指定
          prompt=prompt,
          max_tokens=50
        )
        if response is None or not response.choices:
            error_message = "Error: 応答が空です"
            print(error_message)
            return jsonify({"status": "error", "message": error_message}), 500

        response_text = response.choices[0].text.strip()
        if not response_text:
            error_message = "Error: 応答テキストが空です"
            print(error_message)
            return jsonify({"status": "error", "message": error_message}), 500

        return response_text
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/play', methods=['POST'])
def play():
    word = request.json.get('word')
    word = katakana_to_hiragana(word)

    if not words_played:
        words_played.append(word)
        return jsonify({"status": "success", "message": "OK"})
    else:
        last_word = words_played[-1]
        last_char = adjust_last_character(katakana_to_hiragana(last_word))

        if last_char == word[0]:
            if word not in words_played:
                words_played.append(word)
                return jsonify({"status": "success", "message": "OK"})
            else:
                return jsonify({"status": "error", "message": "この単語は既に使われています。"})
        else:
            return jsonify({"status": "error", "message": "前の単語の最後の文字と一致しません。"})

@app.route('/ai_play', methods=['POST'])
def ai_play():
    user_word = request.json.get('word')
    prompt = f"しりとり: {user_word}、"
    
    ai_response = generate_shiritori_response(prompt)
    
    if ai_response:
        return jsonify({"status": "success", "message": ai_response})
    else:
        return jsonify({"status": "error", "message": "AIからの応答がありませんでした。"})

@app.route('/reset', methods=['POST'])
def reset():
    global words_played
    words_played = []
    return jsonify({"message": "しりとりの履歴がリセットされました。"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
