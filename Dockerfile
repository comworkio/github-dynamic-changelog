FROM python:3-alpine

ENV FLASK_APP=/api.py \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=8080 \
    WERKZEUG_RUN_MAIN=true \
    MANIFEST_FILE_PATH=/manifest.json

COPY ./api/api.py ./manifest.json ./api/requirements.txt /api/list_commits.sh /

RUN pip3 install --upgrade pip && \
    pip3 install -r /requirements.txt && \
    apk add --no-cache bash jq && \
    chmod +x /list_commits.sh

EXPOSE 8080

CMD ["python3", "-m", "flask", "run"]
