FROM python:3.8
WORKDIR /Project/demo

COPY requirements.txt ./
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

CMD ["gunicorn", "vvs_service:app", "-c", "./gunicorn.py"]