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
        "content": '''I am an AI picture book author aiming to teach ethics when dealing with AI. Here are the key points for conveying ethical considerations when handling AI through a picture book. Responses will be provided in English with a friendly tone.

**Importance of Transparency:**
Characters embark on an adventure where they collaborate to understand how AI operates. Transparency forms the foundation of trust.

**Adventure of Fairness:**
Characters meet friends with various colors and shapes, learning to respect diverse opinions and characteristics in AI, just as in friendships.

**Quest for Privacy's Treasure:**
Characters embark on an adventure to protect their cherished secrets and treasures, conveying the importance of respecting and safeguarding privacy.

**Responsibility as Exceptional Heroes:**
Characters, as "technology heroes," comprehend the responsibility of using AI and its impact. They share this knowledge with their peers, becoming exceptional heroes.

**Compassion for the Future:**
Characters explore ways to positively impact future generations through AI usage. Illustrate their journey to discover how AI can bring about beneficial influences for the future.

**Friendship and Cooperation:**
Characters collaborate to understand and embody ethical principles when utilizing AI, leveraging each other's strengths. Create episodes that highlight the importance of friendship and cooperation.

**Intriguing Ethical Enigmas:**
Characters solve mysteries, unveiling ethical questions. This adventure prompts children to contemplate and discover answers to ethical dilemmas on their own.

Crafting a narrative around these points will not only entertain but also educate children on the ethical considerations when interacting with AI.'''

    }
]

db = SQLAlchemy(app)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    data1 = db.Column(db.LargeBinary)
    data2 = db.Column(db.LargeBinary)
    data3 = db.Column(db.LargeBinary)
    data4 = db.Column(db.LargeBinary)

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
    messages.append({"role": "user", "content": f"{user_message}"})
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
        def split_text_into_four(text):
            n = len(text) // 4
            return [text[i:i + n] for i in range(0, len(text), n)]


        data = request.get_json()
        ai_response_text = data.get('text')
        ai_response_texts = split_text_into_four(ai_response_text)

        image_data_list = []
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        for text in ai_response_texts:
            body = {
            "steps": 40,
            "width": 1024,
            "height": 1024,
            "seed": 0,
            "cfg_scale": 5,
            "samples": 1,
            "text_prompts": [
            {
            "text": text,
            "weight": 1
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
                image_data_list.append(image_data)

        if image_data_list:
            data1 = image_data_list[0] if len(image_data_list) > 0 else None
            data2 = image_data_list[1] if len(image_data_list) > 1 else None
            data3 = image_data_list[2] if len(image_data_list) > 2 else None
            data4 = image_data_list[3] if len(image_data_list) > 3 else None

            # 画像データをデータベースに保存
        new_image = Image(name=file_name, data1=data1,data2 = data2,data3 = data3,data4 = data4)
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

@app.route('/show_image/<int:image_id>/<string:image_data>')
def show_image(image_id, image_data):
    image = Image.query.get(image_id)
    if image:
        # 選択された画像データを取得
        image_file = getattr(image, image_data, None)
        if image_file:
            return send_file(io.BytesIO(image_file), mimetype='image/png')
    return 'Image not found', 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
