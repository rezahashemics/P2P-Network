FROM python:3.9-slim

WORKDIR /app

COPY stun_server.py .

RUN pip install flask redis

ENV REDIS_HOST=redis

CMD ["python", "stun_server.py"]
