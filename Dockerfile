FROM python:3.11-alpine
WORKDIR /app
COPY requirements.txt /app/

RUN pip install -r /app/requirements.txt

COPY features /app/features
COPY utils /app/utils
COPY database.py /app
COPY main.py /app/
COPY config.conf /app/
COPY LATEST.md /app/
COPY LATEST_3.2.md /app/
COPY LATEST_3.1.md /app/

CMD ["python", "/app/main.py"]
