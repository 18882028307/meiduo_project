#!/bin/bash

# 启动tracker
docker container start tracker

# 启动storage
docker container start storage

# 启动elasticsearch
docker container start elasticsearch

# 执行静态服务器
cd /home/alvin/python/workspace/meiduo_project/front_end
live-server &

# 执行异步任务
cd /home/alvin/python/workspace/meiduo_project/meiduo_mall
celery -A celery_tasks.main worker -l info