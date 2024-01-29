from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

words_played = []

def katakana_to_hiragana(word):
    return "".join(chr(ord(char) - 96) if "ァ" <= char <= "ン" else char for char in word)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/play', methods=['POST'])
def play():
    word = request.json.get('word')
    word = katakana_to_hiragana(word)  # ユーザーの入力をひらがなに変換

    if not words_played:
        words_played.append(word)
        return jsonify({"status": "success", "message": "OK"})
    else:
        last_word = words_played[-1]
        last_word = katakana_to_hiragana(last_word)  # リストの最後の単語をひらがなに変換

        if last_word[-1] == word[0]:
            if word not in words_played:
                words_played.append(word)
                return jsonify({"status": "success", "message": "OK"})
            else:
                return jsonify({"status": "error", "message": "この単語は既に使われています。"})
        else:
            return jsonify({"status": "error", "message": "前の単語の最後の文字と一致しません。"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
    
