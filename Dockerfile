FROM python:3.12-slim
LABEL org.opencontainers.image.source https://github.com/not-from-concentrate/nfc-info-bot
RUN apt-get update
RUN apt install -y git
RUN pip install pipenv
ENV PROJECT_DIR /usr/local/src/nfc-info-bot
WORKDIR ${PROJECT_DIR}
RUN git clone https://github.com/not-from-concentrate/nfc-info-bot ${PROJECT_DIR}
RUN pipenv install --system --deploy --verbose
ENTRYPOINT ["python", "bot.py"]
