FROM python:3.8.10-buster

# 한국어 설정
ENV LC_ALL=C.UTF-8

# timezone 설정
ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# pip upgrade
RUN python -m pip install --upgrade pip

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /video_collector
WORKDIR /video_collector
ADD . /video_collector

COPY run.sh run.sh
RUN chmod a+x run.sh

CMD ["./run.sh"]