# pull official base image
FROM python:3.12.11-alpine

# set work directory
RUN mkdir bot
WORKDIR /bot

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip3 install --upgrade pip
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . /bot

RUN sed -i 's/\r$//g' /bot/entrypoint.sh
RUN chmod +x /bot/entrypoint.sh

# copy project


# run entrypoint.sh
ENTRYPOINT ["/bot/entrypoint.sh"]
