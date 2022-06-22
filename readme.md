# Voice print recognition system (Speaker identification system)

> Email : zhaosheng@nuaa.edu.cn

## Requirements

1. Mysql 5.7
2. Docker 20.10.12
3. redis 5.0.7

## Install
### backend
```shell
docker load -i si_server.tar
docker run -it -p 8180:8180 si_server:v1.0 /bin/bash
```

### frontend
```shell
docker load -i si_vue.tar
docker run -it -p 8190:8190 si_vue:v1.0 /bin/bash
```

### nginx server (load balancing)
```shell
docker load -i si_nginx.tar
docker run -it -p 80:80 si_nginx:v1.0 /bin/bash
```


## Files

```shell
├── blackbase_preprocess        # 黑库预处理脚本
├── demo_flask                  # Flask后端
│   ├── auto_register
│   ├── cfg.py
│   ├── Dockerfile
│   ├── encoder
│   ├── gunicorn.py
│   ├── log
│   ├── models
│   ├── pretrained_ecapa
│   ├── pretrained_models
│   ├── register
│   ├── requirements.txt
│   ├── scripts
│   ├── snakers4_silero-vad_master
│   ├── static
│   ├── supervisor
│   ├── templates
│   ├── utils
│   ├── vvs_service.py
│   └── wavs
├── dist                        # 前端VUE页面
│   ├── assets
│   ├── favicon.ico
│   └── index.html
├── django                      # Django后端
│   └── si_server_django
├── readme.md
├── src                         # Speechbrain
│   └── speechbrain
└── test                        # 测试脚本
```