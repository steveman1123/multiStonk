FROM python:3.8-slim-buster
COPY multistock-server/ /usr/src/app/multistock-server/
WORKDIR /usr/src/app/multistock-server/
RUN pip install -r requirements.txt

CMD ["python", "app.py"]
