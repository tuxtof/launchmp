FROM python:3.7-alpine3.12

LABEL maintainer="François Egger <francois.egger@swatchgroup.com>"

# copy over our requirements.txt file
COPY requirements.txt /tmp/

# upgrade pip and install required python packages
RUN pip install  -U pip

RUN pip install  -r /tmp/requirements.txt


# copy over our app code
COPY ./  /app/

WORKDIR /app

CMD ["python", "run.py"]
#CMD ["tail", "-f", "/dev/null"]
