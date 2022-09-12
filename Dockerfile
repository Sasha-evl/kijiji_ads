FROM python:3

WORKDIR /kijiji_ads

COPY keys.json .
COPY requirements.txt .
COPY main.py .

RUN pip install -r requirements.txt

CMD [ "python", "./main.py" ]