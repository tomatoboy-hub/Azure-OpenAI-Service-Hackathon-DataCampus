from flask import Flask, render_template, request, jsonify
import requests
import os
import re
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookimages.db'

azure_endpoint = "https://sunhackathon51.openai.azure.com/"
api_key = "e6b46d28ad9445ebaa1a9e6a80fa7d76"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Initialize the conversation with the system role
messages = [
    {
        "role": "system",
        "content": '''You are a counselor(EmoEcho), a virtual listener who empathizes with emotions and aims to provide a safe space for users to express their feelings and concerns. Please use Japanese for all of your responses, with an eye to speaking in a friendly manner.'''
    }
]

db = SQLAlchemy(app)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    data = db.Column(db.LargeBinary)

# push context manually to app
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/message', methods=['POST'])
def message():
    global messages
    data = request.get_json()
    user_message = data.get('message')
    messages.append({"role": "user", "content": user_message})

    ai_message = ""
    try:
        response = requests.post(
            f"{azure_endpoint}gpt3.5-turbo/completions",
            headers=headers,
            json={
                "model": "GPT35TURBO",  # モデルを選択（GPT35TURBO, GPT35TURBO16K, ADA）
                "messages": messages
            }
        )
        response_json = response.json()
        ai_message = response_json.get('choices', [{}])[0].get('message', '')

        # Formatting the response
        ai_message = re.sub(r'([a-z]\))', r'<h3>\1</h3>', ai_message)
        ai_message = ai_message.replace('\n', '<br/>')

        messages.append({"role": "assistant", "content": ai_message})
    except Exception as e:
        ai_message = "Error: " + str(e)

    return jsonify({'message': ai_message})

@app.route('/books', methods=['GET'])
def books():
    return render_template("books.html")

@app.route('/testupload', methods=['GET'])
def testupload():
    return render_template("testupload.html")

@app.route('/upload', methods=['POST'])
def upload_image():
    file = request.files['image']
    if file:
        image = Image(name=file.filename, data=file.read())
        db.session.add(image)
        db.session.commit()
        return 'Image has been uploaded'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
