
# Introduction

This is a LeetCode weekly and biweekly contest rating predictor. The APP is available online at [🔗 lccn.lbao.site](https://lccn.lbao.site/)

Hopefully, you can get the predicted result within **15-30 minutes** after the contest has finished.

## Features

* ⚡️ Fast
  * The core Elo rating algorithm is significantly enhanced by a **Just-In-Time (JIT) compiler** through [Numba](https://numba.pydata.org), reducing execution time to approximately 20 seconds on a dual-core *Intel(R) Xeon(R) Platinum 8255C CPU* (@ 2.50GHz).
  * In addition to the JIT implementation, this project incorporates a [Fast Fourier Transform (FFT) implementation](https://github.com/baoliay2008/lccn_predictor/pull/43). The Elo rating system employed by LeetCode benefits significantly from the FFT algorithm, achieving speedups ranging from **65 to 1,000 times** for individual contest predictions. The most efficient FFT implementation (`EXPAND_SIZE=1`) completes predictions in under **0.25 seconds**, maintaining an impressively low Mean Squared Error (MSE) of approximately 0.027.
  * **Caching** the user's latest rating before initiating the prediction process leads to a substantial reduction in the time required for data retrieval.
* 🎯 Accurate
  * If there were no significant rejudges (assuming everyone's global ranking remains unchanged), it is ensured that the prediction error for rating deltas for **EACH** participant is within the precision limit of 0.05. As a result, the rating difference should be negligible.
  * Please note that a normal case is that there would be some misconduct detection, so your global ranking will be slightly higher even if your submissions are not rejudged, which results in a slightly higher rating :)
* 📱 Responsive web page
  * Tested on phones and tablets.

## More Information

* [🔗 Chinese introduction on leetcode.cn](https://leetcode.cn/circle/discuss/2Ibimx/)
* [🔗 refined-leetcode](https://github.com/XYShaoKang/refined-leetcode): A Chrome extension for leetcode.**cn**, created by [@XYShaoKang](https://github.com/XYShaoKang)

# Underlying Mechanism

## Algorithm

* [🔗 English official illustration on leetcode.com](https://leetcode.com/discuss/general-discussion/468851/New-Contest-Rating-Algorithm-(Coming-Soon))
* [🔗 Chinese official illustration on leetcode.cn](https://leetcode.cn/circle/article/neTUV4/)
* 🔗 Detailed post about FFT acceleration
  - ❤️ Special thanks to [@tiger2005](https://github.com/tiger2005) for proposing this idea in [issue #8](https://github.com/baoliay2008/lccn_predictor/issues/8)

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
docker image build -t lccn_predictor:0.1.2 .

# create docker volume
docker volume create lccn_predictor

# run container
docker run -d -v lccn_predictor:/lccn_predictor -p 55555:55555 --name lp lccn_predictor:0.1.2

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
* v0.0.2(2022/11/25)
  > first version in production
* v0.1.1(2023/02/14)
  > change frontend from server-side rendering([Jinja](https://jinja.palletsprojects.com/) + [Materialize](https://materializecss.com/)) to client-side rendering([React](https://reactjs.org/)).
* v0.1.2(2023/10/04)
  > refine backend logic to enhance robustness and clean up deprecated static site rendering code

---

# Supported by

[![JetBrains Logo (Main) logo](https://resources.jetbrains.com/storage/products/company/brand/logos/jb_beam.svg)](https://jb.gg/OpenSourceSupport)
