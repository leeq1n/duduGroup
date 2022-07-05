# 本项目为学习mirai、mirai-api-http所建，有叙述不对的内容请批评指正
## 本项目主体由[该网址](https://cloud.tencent.com/developer/article/1966467)所述搭建
## 搭建于wsl环境下，目前只在qq使用

# 本项目主要改动在**demo.py**，即使用python控制消息的收发

# 本项目主要基于两部分组成，mirai主体及mirai-api-http
> mirai在http的[API](https://docs.mirai.mamoe.net/mirai-api-http/api/API.html#%E6%89%A7%E8%A1%8C%E5%91%BD%E4%BB%A4)提供了大量消息接口，作为一个server存在于**config/net.mamoe.mirai-api-http/setting.yml**所述的端口上
> 而mirai-api-http由python的flask框架启动，在demo.py中最后一行所述端口启动另一个server，对mirai的消息进行处理


### 后续工作：
> 实现更多的群消息指令控制功能

