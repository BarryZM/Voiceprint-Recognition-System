FROM python:3.8
WORKDIR /Project/demo

COPY requirements.txt ./
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN apt-get update -y && apt-get install -y --no-install-recommends build-essential gcc vim libsndfile1 fzf
COPY . .

CMD ["gunicorn", "vvs_service:app", "-c", "./gunicorn.py"]