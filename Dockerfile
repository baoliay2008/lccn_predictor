# OS
FROM ubuntu:22.04

# Python 3.10
RUN apt update && apt upgrade &&  \
    apt install software-properties-common -y &&  \
    add-apt-repository ppa:deadsnakes/ppa -y &&  \
    apt update &&  \
    apt install python3.10 -y && \
    apt install python3-pip python3.10-venv -y

# Copy project
ADD . /lccn_predictor

# Path
WORKDIR /lccn_predictor

# Install packages
# add `-i https://pypi.tuna.tsinghua.edu.cn/simple/` if you were in China mainland.
RUN pip install --no-cache-dir -r requirements.txt

# Run project
# make main.py a background task, although it's not a good idea to run two processes in a single container
CMD python3 main.py & uvicorn api.entry:app --host 0.0.0.0 --port 55555
