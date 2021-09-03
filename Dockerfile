FROM python:3-alpine

ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    FLASK_APP=/api.py \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=8080 \
    WERKZEUG_RUN_MAIN=true \
    MANIFEST_FILE_PATH=/manifest.json \
    LOG_LEVEL=info \
    PAGE_SIZE=27 \
    GITHUB_MAX_PER_PAGE=100

COPY ./api/api.py ./manifest.json ./api/requirements.txt /

RUN pip3 install --upgrade pip && \
    pip3 install -r /requirements.txt

EXPOSE 8080

CMD ["python3", "-m", "flask", "run"]
