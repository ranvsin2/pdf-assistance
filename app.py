import fitz  # PyMuPDF
from flask import Flask, request, jsonify, send_file, render_template
from transformers import pipeline
from gtts import gTTS
from pydub import AudioSegment
import os
from openai import OpenAI
from pygame import mixer
import time
from PyPDF2 import PdfReader




client = OpenAI()
app = Flask(__name__)
qa_pipeline = pipeline('question-answering')

def extract_text_from_pdf(pdf_path):
    document = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text += page.get_text()
    return text

pdf_path="python-ppt-pages.pdf"
pdf_text = extract_text_from_pdf('python-ppt-pages.pdf')

def generate_response(user_question,context):
    # transcribed_text="in this video I am going to answer the top three questions my students ask me about paisa what is python what you can do with it and why is it so popular in other words what does it do that other programming languages don't Python is the world's fastest growing and most popular programming language not just among software engineers but also among mathematics analysis and visualisation artificial Intelligence and machine learning automation in fact this is one of the big uses of python among people who are not suffer develop website and Windows Mac and LINUX community so whenever you get started has been around for over 20 years is a multipurpose language that's why is the number one language employers are looking for so whether you are a program 16000 in India with others also be sure to subscribe to my Channel now programming explain"
    transcribed_text=context
    response = client.chat.completions.create(
        model="gpt-4",
        messages = [
        {"role": "system", "content": "You are a helpful assistant and a teacher who teaches python. limit the context to the pdf and do not mention edureka, teach like its your content"},
        {"role": "user", "content": f"Here is some context:\n\n{transcribed_text}"},
        {"role": "user", "content": f"Now, I have a question based on the above context:\n\n{user_question}"}
         ],
        max_tokens=150,
        temperature=0.7,
    )
    return response.choices[0].message.content

def generate_summary(transcribed_text):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a tutor. explain me the given content as a tutor and do not mention about pdf. act as you are tutor who is explaining this pdf. limit the context to the pdf and do not mention edureka, teach like its your content"},
            {"role": "user", "content": f"Summarize the following content as a tutor:\n\n{transcribed_text}\n\nSummary:"}
        ],
        max_tokens=150,
        temperature=0.7,
    )
    return response.choices[0].message.content

def playmusic():
    mixer.init()
    mixer.music.load('/Users/ranvijay/dev/openai/ans1.mp3')
    mixer.music.play()
    while mixer.music.get_busy():  # wait for music to finish playing
        time.sleep(1)

def frameaudio(full_response,file_name="ans1.mp3"):
    response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input=full_response
    )
    file_name = file_name
    response.write_to_file(file_name)

@app.route('/getsummary', methods=['POST'])
def create_summary():
    # transcribed_text = (
    #     "in this video I am going to answer the top three questions my students ask me about "
    #     "paisa what is python what you can do with it and why is it so popular in other words "
    #     "what does it do that other programming languages don't Python is the world's fastest "
    #     "growing and most popular programming language not just among software engineers but "
    #     "also among mathematics analysis and visualisation artificial Intelligence and machine "
    #     "learning automation in fact this is one of the big uses of python among people who are "
    #     "not suffer develop website and Windows Mac and LINUX community so whenever you get started "
    #     "has been around for over 20 years is a multipurpose language that's why is the number one "
    #     "language employers are looking for so whether you are a program 16000 in India with others "
    #     "also be sure to subscribe to my Channel now programming explain"
    # )
    transcribed_text=extract_text_from_pdf(pdf_path)
    transcribed_response = generate_summary(transcribed_text)
    print(transcribed_response)
    frameaudio(transcribed_response,"ans1.mp3")
    sound = AudioSegment.from_mp3("ans1.mp3")
    sound.export("ans1.wav", format="wav")
    return jsonify({'answer': transcribed_response, 'audio': '/get_audio'})

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/teach')
def home2():
    return render_template('teach.html')

@app.route('/teach1')
def home3():
    return render_template('teach1.html')

@app.route('/pdf')
def serve_pdf():
    pdf_path="python-ppt-pages.pdf"
    return send_file(pdf_path, mimetype='application/pdf')

def extract_content_by_pagenum(page_num):
    reader = PdfReader('python-ppt-pages.pdf')
    print(len(reader.pages))
    # getting a specific page from the pdf file
    page = reader.pages[page_num]
    # extracting text from page
    text = page.extract_text()
    return text


@app.route('/command', methods=['POST'])
def command():
    print("****coming****")
    data = request.json
    command = data.get('command')
    page_num = data.get('page_num')
    
    if "next" in command.lower():
        page_num += 1
    elif "previous" in command.lower() or "back" in command.lower():
        page_num -= 1
    elif "explain" in command.lower():
        print("I am in explain")
        context = extract_content_by_pagenum(page_num - 1)
        print("context is" , context)
        explanation = generate_summary(context)
        print(explanation)
        # tts = gTTS(explanation)
        # tts.save("explanation.mp3")
        # sound = AudioSegment.from_mp3("explanation.mp3")
        # sound.export("explanation.wav", format="wav")
        frameaudio(explanation,"explanation.mp3")
        sound = AudioSegment.from_mp3("explanation.mp3")
        sound.export("explanation.wav", format="wav")
        return jsonify({'action': 'explain', 'page_num': page_num, 'audio': '/get_explanation','answer':explanation})
    else :
        question=command.lower()
        print("I am in else")
        print(question)
        context = extract_content_by_pagenum(page_num - 1)
        #print("context is" , context)
        explanation_response = generate_response(question,context)
        print(explanation_response)
        # tts = gTTS(explanation)
        # tts.save("explanation.mp3")
        # sound = AudioSegment.from_mp3("explanation.mp3")
        # sound.export("explanation.wav", format="wav")
        frameaudio(explanation_response,"explanation_response.mp3")
        sound = AudioSegment.from_mp3("explanation_response.mp3")
        sound.export("explanation_response.wav", format="wav")
        return jsonify({'action': 'explain', 'page_num': page_num, 'audio': '/get_explanation_response','answer':explanation_response})
    
    page_num = max(1, min(page_num, len(pdf_text)))  # Ensure page_num is within bounds
    return jsonify({'action': 'navigate', 'page_num': page_num})


@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question')
    # page_num = data.get('page_num')
    context = pdf_text  # the extracted text from the PDF
    # answer = qa_pipeline(question=question, context=context)['answer']
    answer=generate_response(question)
    # Convert the answer to speech
    # tts = gTTS(answer)
    # tts.save("answer.mp3")
    frameaudio(answer)
    sound = AudioSegment.from_mp3("ans1.mp3")
    sound.export("ans1.wav", format="wav")
    return jsonify({'answer': answer, 'audio': '/get_audio'})

@app.route('/get_audio', methods=['GET'])
def get_audio():
    return send_file('ans1.wav', mimetype='audio/wav')

@app.route('/get_explanation', methods=['GET'])
def get_explanation():
    return send_file('explanation.wav', mimetype='audio/wav')

@app.route('/get_explanation_response', methods=['GET'])
def get_explanation_response():
    return send_file('explanation_response.wav', mimetype='audio/wav')

if __name__ == '__main__':
    app.run(debug=True)
