from flask import Flask, request, jsonify, render_template
import openai
import os

app = Flask(__name__)

words_played = []

openai.organization = os.environ.get("OPENAI_ORGANIZATION")
openai.api_key = os.getenv("OPENAI_API_KEY")

def katakana_to_hiragana(word):
    return "".join(chr(ord(char) - 96) if "ァ" <= char <= "ン" else char for char in word)

def adjust_last_character(word):
    if word[-1] == 'ー':
        last_char = word[-2]
    else:
        last_char = word[-1]

    hiragana_small = "ぁぃぅぇぉっゃゅょ"
    hiragana_large = "あいうえおつやゆよ"
    katakana_small = "ァィゥェォッャュョ"
    katakana_large = "アイウエオツヤユヨ"

    if last_char in hiragana_small:
        return hiragana_large[hiragana_small.index(last_char)]
    elif last_char in katakana_small:
        return katakana_large[katakana_small.index(last_char)]
    else:
        return last_char

def generate_shiritori_response(prompt):
    try:
        response = openai.Completion.create(
          engine="text-davinci-002",  # 使用するエンジンを指定
          prompt=prompt,
          max_tokens=50
        )
        return response.choices[0].text.strip()
    except Exception as e:
        print(f"Error: {e}")
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
