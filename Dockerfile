FROM python:3.7.8-slim

RUN apt-get update
# RUN apt-get install ffmpeg libsm6 libxext6  -y

COPY . /app/
WORKDIR /app

# COPY requirements.txt /app/
RUN pip install -r requirements.txt

# CMD gunicorn -b :$PORT main:app
CMD streamlit run notifier.py --server.address=0.0.0.0 --server.port=$PORT
# --browser.serverAddress=https://vaccinesearchindia.ue.r.appspot.com --browser.serverPort=$PORT
