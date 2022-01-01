FROM python:3.9
ENV PYTHONUNBUFFERED True
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
# WORKDIR /app/webapp
EXPOSE 8080
ENV PORT=8080
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 3600 main:app
