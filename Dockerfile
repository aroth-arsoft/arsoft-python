FROM python:3-slim

ADD python3/arsoft/ /usr/local/lib/python3.11/site-packages/arsoft/

CMD /usr/local/bin/python

