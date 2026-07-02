# Minimal one-shot runner: replays DVWA's setup.php form submission over
# HTTP so the database is initialized automatically on `docker compose up`.
FROM alpine:3.20

RUN apk add --no-cache curl grep sed

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
