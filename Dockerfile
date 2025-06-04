FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir requests

COPY app /app/

CMD ["python", "-u", "notify.py"]
