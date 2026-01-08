FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip \
 && pip install -r requirements.txt \
 && pip install .

ENV PORT=8000
EXPOSE 8000

CMD ["bash", "-lc", "gunicorn index:app --bind 0.0.0.0:$PORT"]