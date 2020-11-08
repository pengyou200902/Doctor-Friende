### Please wait for update
<!--
# Contents
  * [Rasa Version](#rasa-version)
  * [Chinese ReadMe](#chinese-readme)
  * [Demo Video](#demo-video)
  * [DEMO-GIF](#demo-gif)
  * [Description](#description)
  * [Environment](#environment)
  * [Import data into Neo4j](#import-data-into-neo4j)
  * [Train a Rasa model](#train-a-rasa-model)
  * [Test the model with Rasa Shell](#test-the-model-with-rasa-shell)
  * [Run this bot as a service](#run-this-bot-as-a-service)
  * [Reference](#reference)
  * [Change Log](#change-log)
  
  
## Rasa Version
- Rasa==2.0.x(for other versions please check the branches)

## Chinese ReadMe
[Chinese ReadMe](./README.md)
    
## Demo Video
- [Demo-Video-Here](https://www.bilibili.com/video/av61715811/)
- The demo server maybe slow due to low configuration


## DEMO-GIF
- 2020/05/20 The new version of the chatbox has a different color.  

![image](img/demo-1.gif)

![image](img/demo-2.gif)


## Description
- This program is a QABot based on medical knowledge graph and [Rasa-2.0.x](https://rasa.com/).
[Neo4j](https://neo4j.com/) is used for the storage of medical knowledge graph. 

- The conversation management engine is rasa-core. 
The configuration of rasa pipeline is as follows: 
    ```yaml
    pipeline:
      - name: HFTransformersNLP
        # Name of the language model to use
        model_name: "bert"
      
        # Pre-Trained weights to be loaded
        model_weights: "bert-base-chinese"
      
        # An optional path to a specific directory to download and 
        # cache the pre-trained model weights.
        # The `default` cache_dir can be "C:\Users\username\.cache\torch\transformers" 
        # OR ~/.cache/torch/transformers
        # See https://huggingface.co/transformers/installation.html#caching-models
        cache_dir: null
      
      - name: "LanguageModelTokenizer"
        # Flag to check whether to split intents
        intent_tokenization_flag: False
        # Symbol on which intent should be split
        intent_split_symbol: "_"
        # LanguageModelFeaturizer type: Dense featurizer
      - name: "LanguageModelFeaturizer"
      - name: "MitieNLP"
        model: "data/total_word_feature_extractor_zh.dat"
      - name: "MitieEntityExtractor"
      - name: "EntitySynonymMapper"
      - name: "RegexFeaturizer"
        # SklearnIntentClassifier requires dense_features for user messages
      - name: "SklearnIntentClassifier"
    ```

- ***Notice***: Rasa NLU and Rasa Core have been merged into Rasa.


## Environment
1. Python ≈ 3.8.5

1. Download the ZIP file or use "git clone" to get this project.

1. cd Doctor-Friende, and don't forget to "conda activate" your environment. 

1. Simple instructions to install mitie, see [**Install Mitie**](https://blog.csdn.net/pengyou200902/article/details/109183361)

1. Use this command to install the required libraries and tools. 
    ```shell
   pip install -r requirements.txt
    ```
   
3. *Tips*: 

    - If you are in China and suffer from slow network, you can use pip mirrors to accelerate.
    This command is for temporary use: 
        ```shell
        pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
        ```
   
    - If you have a proxy, you can add --proxy=ip:port at the end of the command above.


## Import data into Neo4j
- Prerequisite: You already have a Neo4j graph to connect to.

- Unzip ```MedicalSpider/data/data.tar.gz``` to ```MedicalSpider/data```(Do not make a new folder). 
Then ```medical.json``` contains all the data you need to import into Neo4j.

- Edit ```MedicalSpider/process_data/create_graph.py```, change the database information into yours.
In order to avoid path errors, running ```create_graph.py``` through pycharm is recommended.

- *About Spider*: The web spider is based on [scrapy](https://scrapy.org/).
If you want to run the spider, just run ```SpiderMain.py```. 
(In order to avoid path errors, running it through pycharm is recommended.)

- The Knowledge Graph contains: 
    - 13,635 nodes (5 labels)
    - 114,163 relationships (6 types)

![image](img/graphdb.png)

- Data Structure:

| Entity Type | Quantity | Example |  
| :--- | :---: | :--- |  
| Disease | 6,143 |  百日咳\n头痛|  
| Department | 54 |  儿科\n小儿内科|  
| Drug | 1,124 |  硫辛酸片\n曲克芦丁片|  
| Food | 378 |  蟹肉\n鱿鱼(干)|  
| Symptom | 5,936 |  角弓反张\n视网膜Roth斑|  
| Total | 13,635 | / |  


## Train a Rasa model
1. Create your own Rasa Train Dataset with [Chatito](https://rodrigopivi.github.io/Chatito/)

1. Download mitie model into chat/data, [BaiDu Disk](https://pan.baidu.com/s/1kNENvlHLYWZIddmtWJ7Pdg), pwd: p4vx, 
OR [Mega](https://mega.nz/#!EWgTHSxR!NbTXDAuVHwwdP2-Ia8qG7No-JUsSbH5mNQSRDsjztSA)

1. The first time running the training command with this ```Pipeline```, the terminal will download the bert model.
You can find default cache directory at [**Cache Models**](https://huggingface.co/transformers/installation.html#caching-models).

1. **Important: ** If errors happen when loading the bert model, try:
    - rename ```bert-base-chinese-config.json``` to ```config.json```
    - rename ```bert-base-chinese-vocab.txt``` to ```vocab.txt``` 
    - rename ```bert-base-chinese-tf_model.h5``` to ```tf_model.h5```

1. To the training, open up a terminal and ```cd chat```, then
    ```shell
    rasa train -c config/config_pretrained_embeddings_mitie_zh.yml --data data/medical/M3-training_dataset_1564317234.json data/medical/stories.md --out models/medicalRasa2 --domain config/domains.yml --num-threads 5 --augmentation 100 -vv
    ```


## Test the model with Rasa Shell
1. Edit the ```tracker_store``` field in endpoints.yml, change the database information into yours.
(Either a new DB or an existing one, Rasa will create a table named ```events```). Check
[SQLAlchemy](https://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls)
for the ```dialect``` field.
This link is provided here [Tracker Store](https://rasa.com/docs/rasa/api/tracker-stores/).
For more information please check Rasa official doc.

1. If you want to use the customized socketio, edit the DB info in ```MyChannel/MyUtils.py``` and 
make sure you have ```message_recieved``` table.(Of course you change this table name. If you do so,
you have to change this in ```handle_message``` function in ```myio.py```.)

1. Edit ```chat/MyActions/actions.py```, change the Neo4j information into yours.

1. Open two terminals or two cmds, both cd into the ```chat``` directory in project root.
(Don't forget to ```conda activate``` your environment.) 

1. Run rasa action server in one terminal: 
    ```shell
   rasa run actions --actions MyActions.actions --cors "*" -vv  
    ```

1. run rasa shell in another terminal/cmd: 
    ```shell
    rasa shell -m models/medicalRasa2/20201026-112436.tar.gz --endpoints config/endpoints.yml -vv
    ```


## Run this bot as a service
1. Do first five steps as mentioned above.

1. run rasa server in another terminal/cmd: 
    ```shell
   rasa run --enable-api -m models/medicalRasa2/20201026-112436.tar.gz --port 5000 --endpoints config/endpoints.yml --credentials config/credentials.yml -vv
    ```
   
1. Frontend Webpage: [ChatHTML](https://github.com/pengyou200902/ChatHTML)
   If you use the customized socketio, change socketPath in the html to ```/mysocket.io/```.

1. *Tips*: 

    - On a server, you can try ```nohup``` command for background running. 


## Reference
- [QABasedOnMedicalKnowledgeGraph](https://github.com/liuhuanyong/QASystemOnMedicalKG)  

- [Rasa_NLU_Chi](https://github.com/crownpku/Rasa_NLU_Chi)
 
- [WeatherBot](https://github.com/howl-anderson/WeatherBot)

- [rasa-webchat](https://github.com/mrbot-ai/rasa-webchat), webchat.js

- [Scrapy](https://scrapy.org)

- [Neo4j](https://neo4j.org)

- [py2neo](https://py2neo.org)

- [rasa-doc](https://rasa.com/docs) OR [legacy-rasa-doc](https://legacy-docs.rasa.com/docs/)
  
- [rasa-forum](https://forum.rasa.com/)


## Change Log
- #### 2020/10/26
    - Update Rasa to 2.0.x, Python version 3.8.5
    
    - ```Pipeline``` changes a lot. Add a new component ```HFTransformersNLP```.
    
    - You should use the new model in ```models/medicalRasa2```.
    
    - Edit ```domains.yml```, change the ```type``` of ```sure``` and ```pre_disease``` into ```any```.

- #### 2020/10/24
    - Update Rasa to 1.7.4, Python version 3.7.9.
    
    - Use newly trained model only.
    
    - Add ```session_config``` in domains.yml to meet Rasa's requirement.
    
    - Edit line 91 in ```chat/data/medical/stories.md``` to ```action_first```.
    It was ```utter_greet``` originally, which would run ```utter_greet``` according
    to line 91 in chat/data/medical/stories.md, instead of ```action_first```. 
    This happens in ```Rasa>=1.3.0```. 


- #### 2020/05/20
    - Update Rasa to 1.2.9, Python version 3.6.8

    - Introduce [Tracker Store](https://rasa.com/docs/rasa/api/tracker-stores/) into endpoints.yml, 
    this enables auto storage of Tracker into your MySQL DB.
    Though Tracker Store is an official way to store messages, I also add a customized way to
    store user message. See below.
    
    - I updated ```myio.py``` and ```MyUtils.py``` in ```chat/MyChannel/```. There's a customized socketio in 
    ```myio.py``` which enables you to store user messages into MySQL DB. It's based on 
    ```rasa.core.channels.socketio.SocketIOInput```. You can store the fields you need in function ```handle_message```.
    
    - The information for connecting your MySQL DB should be provided in ```MyUtils.py```.
    
    - Add some configurations to ```credentials.yml``` to enable the customized socketio. 
    
    - Fix the demo server. It crashed on April 1st.
-->