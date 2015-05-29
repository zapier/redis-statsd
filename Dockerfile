FROM ubuntu:14.04

RUN apt-get update
RUN apt-get -y install python-pip
RUN pip install redis

ADD app.py /app.py

CMD python /app.py
