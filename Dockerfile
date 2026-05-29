# pull official base image
FROM python:3.12.11-alpine

# set work directory
RUN mkdir bot
WORKDIR /bot

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN apk add --no-cache netcat-openbsd
RUN pip3 install --upgrade pip
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY entrypoint.sh /bot/entrypoint.sh
COPY . /bot/
RUN chmod +x /bot/entrypoint.sh && \
    sed -i 's/\r$//g' /bot/entrypoint.sh
ENTRYPOINT ["/bot/entrypoint.sh"]
