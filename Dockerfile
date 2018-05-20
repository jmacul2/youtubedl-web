FROM python:3.6
MAINTAINER Fran Hermoso <franhp@gmail.com>

RUN apt-get update && apt-get install -y supervisor redis-server

ADD requirements.txt /app/
RUN pip install -r /app/requirements.txt

ADD static /app/static
ADD templates /app/templates
ADD app.py /app/

# Supervisor
ADD supervisord/conf.d/* /etc/supervisor/conf.d/
ADD supervisord/supervisord.conf /etc/supervisor/supervisord.conf
RUN mkdir -p /var/log/server /var/log/redis /var/log/celery

RUN mkdir /downloads
RUN chmod -R a+rwx /downloads

EXPOSE 5000

CMD ["/usr/bin/supervisord"]
