FROM python:3
ADD GDrive_Download.py /
ADD requirements.txt /
ADD credentials.json /
RUN pip3 install -r requirements.txt
RUN mkdir -p /app
CMD ["python", "./GDrive_Download.py"]
