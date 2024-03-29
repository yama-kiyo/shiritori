from openai import OpenAI
import traceback
import os
from flask import Flask, request, jsonify, render_template

client = OpenAI(
    # This is the default and can be omitted
api_key=os.environ.get("OPENAI_API_KEY"),
)
    ## openai.api_key = os.getenv("OPENAI_API_KEY") ##
app = Flask(__name__)

words_played = []

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
            
def generate_shiritori_response(user_input):
    # ユーザーの入力単語の最後の文字を取得
    last_char = adjust_last_character(katakana_to_hiragana(user_input))[-1]

    # しりとりのプロンプトを作成
    prompt = f"次のしりとりの単語を「{last_char}」から始めてください。ひらがなとカタカナで名詞のみ使用してください。答えは一つだけにしてください。最後に「ん」がつく単語は禁止です。もし最後に「ん」がつく単語しかなかったらあなたの負けなので「うわー、まけた！」と宣言してください。"

    try:
        # OpenAI APIリクエスト
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        # 応答からテキストを取得
        response_text = response.choices[0].message.content.strip()
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

    if word[-1] == 'ん':
        return jsonify({"status": "gameover", "message": "GAME OVER"})
        
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
                return jsonify({"status": "error", "message": "もうでたよ！"})
        else:
            return jsonify({"status": "error", "message": "最後の文字とちがうよ！"})

@app.route('/ai_play', methods=['POST'])
def ai_play():
    user_word = request.json.get('word')
    ai_response = generate_shiritori_response(user_word)
    
    if ai_response:
        return jsonify({"status": "success", "message": ai_response})
    else:
        return jsonify({"status": "error", "message": "AIはもう寝てるってさ。"})


@app.route('/reset', methods=['POST'])
def reset():
    global words_played
    words_played = []
    return jsonify({"message": "しりとりの履歴がリセットされました。"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
    
