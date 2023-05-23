# 青春浙江-青年大学习自动签到脚本

青春浙江-青年大学习自动签到脚本

## 开始

### 本地运行

1. 安装相关依赖（requirements.txt）
1. 修改配置文件（config.toml）
1. 启动自动签到（main.py）
1. 获取结束截图（end文件夹中）

### 定时运行

1. 安装相关依赖（requirements.txt）
2. 修改配置文件（config.toml）
3. 启动自动签到（**main-scheduled.py**）
4. 获取结束截图（end文件夹中）



## 项目结构

```txt
|   config.toml
|   config.toml.demo
|   main-scheduled.py
|   main.py
|   profile.toml
|   README.md
|   requirements.txt
|
+---.github
|   \---workflows
|           run.yml
|
\---end
    \---2023_05_23
```



### 配置文件：config.toml

- #### 配置文件模板为config.toml.demo，需要自行重命名为config.toml

```toml
[user.xxx]
openid="oO-xxxxxxxxxxxxxxxxx"
nid=""     # optional
cardNo=""  # optional

[user.yyy]
openid="oO-xxxxxxxxxxxxxxxxx"
nid=""     # optional
cardNo=""  # optional

```

- [user.xxx]：这里可以自定义字段如user.pqc表示当前签到的用户
- openid：[必须]用户登录凭据，可以通过抓包获取
- nid：非必要，可以为空，只要你之前在微信上登录过
- cardNo：非必要，可以为空，只要你之前在微信上登录过



### main.py

- 立即执行的脚本

### main-scheduled.py

- 定时执行，时间在周一早上八点左右





### profile.toml

- 程序配置信息，包含api地址，小程序id，UA等



### end/

- 截图输出目录，里面的文件夹根据日期分类。
