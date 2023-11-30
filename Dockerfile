FROM python:3.10-bullseye

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .
RUN apt-get update && apt-get install -y ffmpeg

CMD [ "python3", "-m", "bot4" ]
