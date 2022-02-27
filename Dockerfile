FROM python:3.9.7
COPY ./requirements.txt /requirements.txt
WORKDIR /app
ADD . /app
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
CMD ["python","src/app.py"]

