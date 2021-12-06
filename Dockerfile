FROM python:3.9
ENV PYTHONUNBUFFERED True

WORKDIR /app
COPY . /app
ENV FLASK_ENV=development

RUN pip install -r requirements.txt

ENV PORT=8080
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 900000000 main:app
