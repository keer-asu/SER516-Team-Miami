
FROM python:3.11-slim-buster

WORKDIR /app

COPY . /app

RUN pip install --trusted-host pypi.python.org -r requirements.txt

EXPOSE 5000

ENV TAIGA_URL=https://api.taiga.io/api/v1

WORKDIR /app/Backend

CMD ["flask", "--app", "flaskProject/main", "run", "--host=0.0.0.0"]
