FROM python:3.12-slim

WORKDIR /usr/src/app

COPY . .

RUN python3 -m venv .venv
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

CMD ["flask", "run"]

# docker run -p 5000:5000 weather-app
# docker build -t weather-app . 