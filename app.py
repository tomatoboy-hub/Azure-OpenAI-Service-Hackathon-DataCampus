from flask import Flask, render_template, request, jsonify,send_file
import io
import requests
import os
import re
from flask_sqlalchemy import SQLAlchemy
import base64
import requests
import logging
import openai

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookimages.db'
openai.api_type = "azure"
openai.api_version = "2023-05-15" 
openai.api_base = "https://sunhackathon51.openai.azure.com/"  # Your Azure OpenAI resource's endpoint value.
openai.api_key = "e6b46d28ad9445ebaa1a9e6a80fa7d76"


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Initialize the conversation with the system role
messages = [
    {
        "role": "system",
        "content": '''Please use English for all of your responses, with an eye to speaking in a friendly manner. If you get Japanese messages, you should translate it to English at first'''
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

@app.route('/',methods = ['GET'])
def index():
    return render_template('index.html')

@app.route('/chat')
def chat():
    return render_template("chat.html")

@app.route('/message', methods=['POST'])
def message():
    global messages
    data = request.get_json()
    user_message = data.get('message')
    messages.append({"role": "user", "content": f"please translate {user_message} into English"})
    print(messages)

    ai_message = ""
    try:
        response = openai.ChatCompletion.create(
            engine="GPT35TURBO", # The deployment name you chose when you deployed the GPT-3.5-Turbo or GPT-4 model.
            messages=messages
            )
        ai_message = response['choices'][0]['message']['content']

        # Formatting the response

        messages.append({"role": "assistant", "content": ai_message })
        logger.info("ai_message is created")
        logger.info(ai_message)
    except Exception as e:
        ai_message = "Error: " + str(e)
        logger.info(ai_message)


    return jsonify({'message': ai_message})

@app.route('/books', methods=['GET'])
def books():
    return render_template("books.html")

@app.route('/testupload', methods=['GET'])
def testupload():
    return render_template("testupload.html")

@app.route('/create_image',methods=['POST'])
def create_image():

    try:

        data = request.get_json()
        ai_response_text = data.get('text')

        # Update the text_prompts with the AI response
        logger.info("ai_response_text")
        logger.info(ai_response_text )
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"

        body = {
        "steps": 40,
        "width": 1024,
        "height": 1024,
        "seed": 0,
        "cfg_scale": 5,
        "samples": 1,
        "text_prompts": [
        {
        "text": ai_response_text,
        "weight": 1
        },
        {
	    "text": "blurry, bad",
	    "weight": -1
	  }
        ],
        }

        headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "sk-WSGCH3VWaCUlfTFVVjSijUJUJg4fVqWhuf8zUD34ylRQSwoQ",
        }

        response = requests.post(
        url,
        headers=headers,
        json=body,
        )
        logger.info("response")
        logger.info(response)


        if response.status_code != 200:
            raise Exception("Non-200 response: " + str(response.text))

        data = response.json()

        # make sure the out directory exists
        if not os.path.exists("./out"):
            os.makedirs("./out")

        for i, image in enumerate(data["artifacts"]):
            image_data = base64.b64decode(image["base64"])
            file_name = f'txt2img_{image["seed"]}.png'
            # ファイルをサーバーに一時的に保存
            with open(f'./out/{file_name}', "wb") as f:
                f.write(image_data)

            # 画像データをデータベースに保存
            new_image = Image(name=file_name, data=image_data)
            db.session.add(new_image)
            db.session.commit()

            

        return jsonify({'message': 'Image created successfully'})
    except Exception as e:
        # エラーレスポンスを返す
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_image():
    file = request.files['image']
    if file:
        image = Image(name=file.filename, data=file.read())
        db.session.add(image)
        db.session.commit()
        return 'Image has been uploaded'

@app.route('/images')
def images():
    images = Image.query.all()
    return render_template('images.html', images=images)

@app.route('/show_image/<int:image_id>')
def show_image(image_id):
    image = Image.query.get(image_id)
    if image:
        return send_file(io.BytesIO(image.data), mimetype='image/png')
    return 'Image not found', 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
