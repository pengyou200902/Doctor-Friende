## Rasa==1.2.9(for other versions please check the branches)
## [English ReadMe](./en-README.md)
## [Demo-Video-Here](https://www.bilibili.com/video/av61715811/)
- 视频中的demo演示网址用的上海服务器，低配，加载速度慢，各位轻虐~~ >.<

## DEMO-GIF
- 2020/05/20 新版聊天窗的颜色略有不同

![image](img/demo-1.gif)

![image](img/demo-2.gif)

## 说明
- 本程序实现的是基于中文的医疗知识图谱的问答机器人MedicalKBQA，
是基于[Rasa-1.2.9](https://rasa.com/)版本及其支持的外部组件实现的，
并使用了图数据库[Neo4j](https://neo4j.com/)构建知识图谱。

- 会话管理使用的是rasa-core，rasa的pipeline配置如下：
        
      pipeline:
      - name: "MitieNLP"
      model: "data/total_word_feature_extractor_zh.dat"
      - name: "JiebaTokenizer"
      dictionary_path: "jieba_userdict"
      - name: "MitieEntityExtractor"
      - name: "EntitySynonymMapper"
      - name: "RegexFeaturizer"
      - name: "MitieFeaturizer"
      - name: "SklearnIntentClassifier"

- *注意*： rasa-nlu和rasa-core已经合并成rasa

- Rasa训练数据集的构造： 使用到了[Chatito工具](https://rodrigopivi.github.io/Chatito/)

## 配置环境（python ≈ 3.6.8）
1. 下载zip包或者git clone 

2. 进入Doctor-Friende目录，conda记得activate环境

2. 然后在命令行使用命令安装依赖

       pip install -r requirements.txt

3. *提示*：

    - 国内推荐使用镜像加速（此命令是临时使用镜像，并非全局都用），比如：
    
          pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
    
    - 如果你有代理，可以在pip install命令后加上 --proxy=地址:端口

## 数据导入neo4j
- 前提是已经有了可以连接的neo4j graph

- 解压MedicalSpider/data/data.tar.gz，直接解压到MedicalSpider/data下，不要新建文件夹，则medical.json是所有数据的汇总，
将会被导入到你的知识图谱中

- 修改MedicalSpider.process_data下的create_graph.py，把neo4j数据库的链接信息改成你自己的，然后运行该文件
（为了防止路径问题，建议使用pycharm打开本项目后运行）

- *关于爬虫*：爬虫实现是使用了[scrapy](https://scrapy.org/)库，若想运行，可以在Doctor-Friende目录下运行SpiderMain.py

- 整体规模：
    - 13,635 nodes (5 labels)
    - 114,163 relationships (6 types)

![image](img/graphdb.png)

- 数据结构

| 实体类型 | 含义 | 数量 | 举例 |  
| :--- | :---: | :---: | :--- |  
| Disease | 疾病 | 6,143 |  百日咳\n头痛|  
| Department | 科室 | 54 |  儿科\n小儿内科|  
| Drug | 药品 | 1,124 |  硫辛酸片\n曲克芦丁片|  
| Food | 食物 | 378 |  蟹肉\n鱿鱼(干)|  
| Symptom | 疾病症状 | 5,936 |  角弓反张\n视网膜Roth斑|  
| Total | 总计 | 13,635 | 约1.3万实体量级|  

## 运行bot
1. 修改endpoints.yml中的tracker_store字段，将数据库连接信息换成你自己的（现成的db或新建db皆可，
我新建了一个db，Rasa会生成一个名为events的表），dialect字段是用了
[SQLAlchemy](https://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls)
里的，这个链接是Rasa官方文档在[Tracker Store](https://rasa.com/docs/rasa/api/tracker-stores/)
给出的，详情参考官方文档

1. 若要自己定制消息记录方式，请修改MyChannel/MyUtils.py中数据库连接信息，并确保你的MySQL数据库中
有message_received表，当然你可以取别的名字，记得在myio.py的handle_message函数里把对应代码改掉

1. 下载用于mitie的模型文件放到chat/data文件夹下，[百度网盘](https://pan.baidu.com/s/1kNENvlHLYWZIddmtWJ7Pdg)，密码：p4vx，
或者[Mega云盘](https://mega.nz/#!EWgTHSxR!NbTXDAuVHwwdP2-Ia8qG7No-JUsSbH5mNQSRDsjztSA)

1. chat/MyActions下的actions.py中同样需要先把neo4j数据库的链接信息改成你自己的

1. 打开2个终端，都cd到chat目录下，conda记得activate环境  

1. 一个终端（启动Action Server）

       rasa run actions --actions MyActions.actions --cors "*" -vv  

1. 另一个终端（启动NLU & Core Server）

       rasa run --enable-api -m models/medical-final-m3/20190728-212653.tar.gz --port 5000 --endpoints config/endpoints.yml --credentials config/credentials.yml -vv

1. 前端页面位于：[ChatHTML](https://github.com/pengyou200902/ChatHTML)
   如果用了我写的自定义socketio接口，请把前端中的socketPath做对应修改，默认就改成"/mysocket.io/"

1. *提示*：

    - 更推荐使用nohup等类似的方式在后台运行 ，并将控制台输出指向指定的文件。 

## 参考
- 刘焕勇老师的[QABasedOnMedicalKnowledgeGraph](https://github.com/liuhuanyong/QASystemOnMedicalKG)  

- 国内作者写的[Rasa_NLU_Chi](https://github.com/crownpku/Rasa_NLU_Chi)，已经被rasa收入官方文档了，新版rasa已经有支持中文的方式了。
 
- 前端设计参考[WeatherBot](https://github.com/howl-anderson/WeatherBot)，此项目采用的是nlu和core合并前的rasa。

- 所以前端使用了webchat.js，[rasa-webchat](https://github.com/mrbot-ai/rasa-webchat)

- [Scrapy](https://scrapy.org)

- [Neo4j](https://neo4j.org)

- [py2neo](https://py2neo.org)

- [rasa-doc](https://rasa.com/docs)或者旧版[legacy-rasa-doc](https://legacy-docs.rasa.com/docs/)建议先看第一个
  
- [rasa-forum](https://forum.rasa.com/)论坛上也会有很多问题的讨论，可以搜索  

## TODO
- 优化readme
- ~~上传前端项目~~
- ~~写report~~

## Change Log
- #### 2020/05/20 Update Rasa to 1.2.9
    - 在endpoints.yml中使用了Rasa的新特性[Tracker Store](https://rasa.com/docs/rasa/api/tracker-stores/)，
    这个配置将会自动把Tracker存入MySQL中叫rasa的数据库（见endpoints.yml），
    虽然有官方的这个存储Tracker的方式，但是我也加入了一个自定义存储消息记录的功能，见下方
    
    - 在chat/MyChannel里更新了myio.py和MyUtils.py，myio.py中自定义了一个socket接口以便定制存储消息记录于MySQL，
    存储的字段在myio.py中可以看到，在handle_message函数中，这个自定义的socket接口是
    以rasa.core.channels.socketio.SocketIOInput这个class为模版修改的
    
    - MyUtils.py中主要提供了数据库连接的信息，用到的mysqlclient依赖库可能安装会有困难，大家注意
    
    - 修改了credentials.yml，加入了使用上述自定义socketio的配置
    
    - 演示服务器在4月1日出了点问题，已修复，顺便更新了聊天窗依赖的js，聊天窗颜色略有不同

## 如有问题可以issue