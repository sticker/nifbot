FROM python:3.7-slim
MAINTAINER kakincamp-team <isp-kakin-camp@list.nifty.co.jp>

# 日本時間対応
ENV TZ=Asia/Tokyo

# pipenvをインストール
RUN pip install pipenv

# ソースを配置
USER root
RUN mkdir -p /service/nifbot
COPY . /service/nifbot
WORKDIR /service/nifbot

# Python依存ライブラリをインストール
RUN pipenv install

## botを起動する
ENTRYPOINT ["pipenv", "run"]

# CMDでデフォルト引数を指定
CMD ["start"]
