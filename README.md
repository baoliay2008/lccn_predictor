
# Introduction

Leetcode weekly and biweekly contest rating predictor.

## Backend

* [APScheduler](https://apscheduler.readthedocs.io/en/3.x/): background tasks
* [Numpy](https://numpy.org/) and [Numba](https://numba.pydata.org/): core prediction algorithm implementation
* [FastAPI](https://fastapi.tiangolo.com/): restful API
* [Jinja](https://jinja.palletsprojects.com/): HTML templates for server-side rendering

## Frontend

* [Materialize](https://materializecss.com/): responsive front-end framework
* [Echarts](https://echarts.apache.org/en/index.html): data visualization

## Database

* [MongoDB](https://www.mongodb.com/): NoSQL database
* [Beanie](https://roman-right.github.io/beanie/): ODM for MongoDB

# Online Web APP

Running on [🔗 lccn.lbao.site](https://lccn.lbao.site/)

# Algorithm

[Leetcode.com 🔥👩🏻‍💻New Contest Rating Algorithm👨🏽‍💻🔥 - It's HERE!](https://leetcode.com/discuss/general-discussion/468851/New-Contest-Rating-Algorithm-(Coming-Soon))

[力扣官方 📣 通知：全新「周赛评分算法」最终方案](https://leetcode.cn/circle/article/neTUV4/)

# Deployment

## virtualenv

```shell
git clone git@github.com:baoliay2008/lccn_predictor.git
cd lccn_predictor

python3.10 -m virtualenv venv/
source venv/bin/activate

pip3 install -r requirements.txt

python main.py 
uvicorn api.fastapi:app --host 0.0.0.0 --port 55555
```

## Docker

```shell
git clone git@github.com:baoliay2008/lccn_predictor.git
cd lccn_predictor

# write production environment mongodb config
cp config.yaml.template config.yaml
vi config.yaml

# build docker image
docker image build -t lccn_predictor:0.0.1 .

# create docker volume
docker volume create lccn_predictor

# run container
docker run -d -v lccn_predictor:/lccn_predictor -p 55555:55555 --name lp lccn_predictor:0.0.1

docker exec -it lp bash

docker container stop lp

docker container start lp

```

# License

MIT License

# Changelog



