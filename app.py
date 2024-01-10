from flask import Flask, render_template, request, jsonify,redirect, url_for
import openai
import os
import re
from flask_sqlalchemy import SQLAlchemy




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookimages.db'

# Set your OpenAI API key
openai.api_key = ''

# Initialize the conversation with the system role
messages = [
    {
    "role": "system",
    "content": '''You are a counselor(EmoEcho), a virtual listener who empathizes with emotions and aims to provide a safe space for users to express their feelings and concerns. Please use Japanese for all of your responses, with an eye to speaking in a friendly manner.
'''
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
        completions_generator = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            stream=True
        )
        # Handle streamed responses; combine content chunks
        for chunk in completions_generator:
            content_chunk = chunk.get('choices', [{}])[0].get('delta', {}).get('content', "")
            ai_message += content_chunk

        # Formatting the response
        ai_message = re.sub(r'([a-z]\))', r'<h3>\1</h3>', ai_message)  # Subheading formatting
        ai_message = ai_message.replace('\n', '<br/>')  # New line formatting

        messages.append({"role": "assistant", "content": ai_message})
    except Exception as e:
        ai_message = "Error: " + str(e)

    return jsonify({'message': ai_message})

@app.route('/books',methods=['GET'])
def books():
    return render_template("books.html")

@app.route('/testupload',methods=['GET'])
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

