
# Introduction

This is a `Leetcode` weekly and biweekly contest rating predictor. The APP is available online at [🔗 lccn.lbao.site](https://lccn.lbao.site/)

Hopefully, you can get the predicted result within 20-30 minutes after the contest has finished.

## Features
* ⚡️ Fast
  > 1. The core prediction algorithm is accelerated by a JIT compiler([Numba](https://numba.pydata.org/)) which costs around 20 seconds on a two-cores *Intel(R) Xeon(R) Platinum 8255C CPU* (@ 2.50GHz).
  > 2. User's latest rating was **cached** serval times before predicting which can save a lot of time fetching data.
* 🎯 Accurate
  > 1. If there were no massive rejudges(say, everyone's global ranking stays unchanged), the rating difference should be negligible.
  > 2. Please note that a normal case is that there would be some misconduct detection, so your global ranking will be slightly higher even if your submissions are not rejudged, which results in a slightly higher rating :)
* 📱 Responsive web page
  > Tested on phones and tablets.

## More Information
* [🔗 Chinese introduction on leetcode.cn](https://leetcode.cn/circle/discuss/2Ibimx/)
* [🔗 refined-leetcode](https://github.com/XYShaoKang/refined-leetcode): A Chrome extension for leetcode.**cn**, created by [@XYShaoKang](https://github.com/XYShaoKang)

# Underlying Mechanism

## Algorithm

* [🔗 English official illustration on leetcode.com](https://leetcode.com/discuss/general-discussion/468851/New-Contest-Rating-Algorithm-(Coming-Soon))
* [🔗 Chinese official illustration on leetcode.cn](https://leetcode.cn/circle/article/neTUV4/)

## Database

* [MongoDB](https://www.mongodb.com/): NoSQL database
* [Beanie](https://roman-right.github.io/beanie/): ODM for MongoDB

## Backend

* [APScheduler](https://apscheduler.readthedocs.io/en/3.x/): background tasks
* [Numpy](https://numpy.org/) and [Numba](https://numba.pydata.org/): core prediction algorithm implementation and acceleration
* [FastAPI](https://fastapi.tiangolo.com/): restful API
* 🚮 ~~[Jinja](https://jinja.palletsprojects.com/): HTML templates for server-side rendering~~

## Frontend

* [React](https://reactjs.org/): most popular front-end library
* [TailwindCSS](https://tailwindcss.com/) and [DaisyUI](https://daisyui.com/): modern CSS framework and its component library
* 🚮 ~~[Materialize](https://materializecss.com/): responsive front-end framework~~
* [Echarts](https://echarts.apache.org/en/index.html): data visualization

# Development

## Backend Deployment

### virtualenv

```shell
git clone git@github.com:baoliay2008/lccn_predictor.git
cd lccn_predictor

# write your mongodb environment config
cp config.yaml.template config.yaml
vi config.yaml

python3.10 -m virtualenv venv/
source venv/bin/activate

pip3 install -r requirements.txt

python main.py
uvicorn api.entry:app --host 0.0.0.0 --port 55555
```

### Docker

```shell
git clone git@github.com:baoliay2008/lccn_predictor.git
cd lccn_predictor

# write production environment mongodb config
cp config.yaml.template config.yaml
vi config.yaml

# build docker image
docker image build -t lccn_predictor:0.1.1 .

# create docker volume
docker volume create lccn_predictor

# run container
docker run -d -v lccn_predictor:/lccn_predictor -p 55555:55555 --name lp lccn_predictor:0.1.1

docker exec -it lp bash

docker container stop lp

docker container start lp

```

## Frontend Deployment

```shell
cd client

# install dependencies
npm install

# change `baseUrl` to your local backend process
vi src/data/constants.js
# if you followed instruction above
# it should be "http://localhost:55555/api/v1"

# local test
npm start

# publish
npm run build

```


# License

[MIT License](LICENSE)

# Changelog

* v0.0.1(2022/11/14)
  > make this repo public, first release.
* v0.1.1(2023/02/14)
  > change frontend from server-side rendering([Jinja](https://jinja.palletsprojects.com/) + [Materialize](https://materializecss.com/)) to client-side rendering([React](https://reactjs.org/)).

---

# Supported by

[![JetBrains Logo (Main) logo](https://resources.jetbrains.com/storage/products/company/brand/logos/jb_beam.svg)](https://jb.gg/OpenSourceSupport)
