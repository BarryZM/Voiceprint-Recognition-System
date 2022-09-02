# Voice print recognition system (Speaker identification system)
> Email : zhaosheng@nuaa.edu.cn
声纹识别系统后台及前端展示页面。

## Requirements
1. Mysql 5.7
2. Docker 20.10.12
3. redis 5.0.7
4. Minio

## Files
```shell
├── preprocess           # 黑库预处理脚本
├── postprocess          # 导出识别结果，准确率报告等结果
├── src                  # 主体代码
└───├
    ├── auto_register                   # 自动注册服务
    ├── cfg.py                          # 配置文件
    ├── Dockerfile                      # DOCKER
    ├── encoder                         # 编码器
    ├── gunicorn.py                     # gunicorn的配置文件
    ├── log                             # 日志目录
    ├── models                          # flask的model
    ├── pretrained_ecapa                # 训练完成的模型参数
    ├── pretrained_models               # 训练完成的模型参数
    ├── requirements.txt                # 项目依赖
    ├── scripts                         # 启动和停止的脚本
    ├── snakers4_silero-vad_master      # VAD的工具
    ├── static                          # flask的静态页面
    ├── supervisor                      # 进程管理工具
    ├── templates                       # flask的模板
    ├── utils                           # 工具函数
    ├── vvs_service.py                  # 主体
    └── wavs                            # 保存音频文件以及黑库
└── test                                # 测试脚本
```

## Install

### Database
1. 安装并启动Mysql和Redis服务
Mysql运行脚本`si.sql`，创建表单

2. 在存储服务器上运行minio对象存储服务
```shell
sudo ./minio server <where/to/save/data> --console-address ":9001"
```

3. 修改配置文件
```shell
vim ./src/cfg.py
```

### backend
```shell
sudo docker load -i si_v1_0.tar
sudo docker run --entrypoint="" --name si_server_1_0 -it -p 8180:8180 -v <path/to/VAF-System>:/VAF-System nuaazs/si:v1.0 /bin/bash
```
### docker
```shell
cd ./src
# gunicorn运行
./scripts/start.sh

# python运行
python vvs_service.py
```