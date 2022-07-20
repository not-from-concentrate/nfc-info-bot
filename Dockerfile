LABEL org.opencontainers.image.source https://github.com/not-from-concentrate/nfc-info-bot
FROM python:3.9-slim
RUN apt-get update
RUN apt install -y git
RUN pip install pipenv
ENV PROJECT_DIR /usr/local/src/nfc-info-bot
WORKDIR ${PROJECT_DIR}
RUN git clone https://github.com/not-from-concentrate/nfc-info-bot ${PROJECT_DIR}
RUN pipenv install --system --deploy
ENTRYPOINT ["python", "bot.py"]