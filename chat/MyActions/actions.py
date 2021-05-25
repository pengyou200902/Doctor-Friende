import sys
import logging
import re
from typing import Text, Dict, Any

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from py2neo import Graph
from markdownify import markdownify as md

logger = logging.getLogger(__name__)

p = 'data/medical/lookup/Diseases.txt'
disease_names = [i.strip() for i in open(p, 'r', encoding='UTF-8').readlines()]
# default neo4j account should be user="neo4j", password="neo4j"
try:
    # graph = Graph(host="127.0.0.1", http_port=7474, user="neo4j", password="myneo")
    graph = Graph("http://localhost:7474", auth=("neo4j", "myneo"))
except Exception as e:
    logger.error('Neo4j connection error: {}, check your Neo4j'.format(e))
    sys.exit(-1)
else:
    logger.debug('Neo4j Database connected successfully.')


def retrieve_disease_name(name):
    names = []
    name = '.*' + '.*'.join(list(name)) + '.*'
    pattern = re.compile(name)
    for i in disease_names:
        candidate = pattern.search(i)
        if candidate:
            names.append(candidate.group())
    return names


def make_button(title, payload):
    return {'title': title, 'payload': payload}


class ActionEcho(Action):
    def name(self) -> Text:
        return "action_echo"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        user_say = "You said: " + tracker.latest_message['text']
        dispatcher.utter_message(user_say)
        return []


class ActionFirst(Action):
    def name(self) -> Text:
        return "action_first"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        # dispatcher.utter_template("utter_first", tracker)
        # print('ActionFirst'*10)
        dispatcher.utter_message(response="utter_first")
        # dispatcher.utter_template("utter_howcanhelp", tracker)
        # print('dispatcher.utter_message')
        dispatcher.utter_message(md("您可以这样向我提问: <br/>头痛怎么办<br/>\
                              什么人容易头痛<br/>\
                              头痛吃什么药<br/>\
                              头痛能治吗<br/>\
                              头痛属于什么科<br/>\
                              头孢地尼分散片用途<br/>\
                              如何防止头痛<br/>\
                              头痛要治多久<br/>\
                              糖尿病有什么并发症<br/>\
                              糖尿病有什么症状"))
        return []


class ActionDonKnow(Action):
    def name(self) -> Text:
        return "action_donknow"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        # dispatcher.utter_template("utter_donknow", tracker)
        dispatcher.utter_message(response="utter_donknow")
        # dispatcher.utter_template("utter_howcanhelp", tracker)
        dispatcher.utter_message(md("您可以这样向我提问: <br/>头痛怎么办<br/>\
                                      什么人容易头痛<br/>\
                                      头痛吃什么药<br/>\
                                      头痛能治吗<br/>\
                                      头痛属于什么科<br/>\
                                      头孢地尼分散片用途<br/>\
                                      如何防止头痛<br/>\
                                      头痛要治多久<br/>\
                                      糖尿病有什么并发症<br/>\
                                      糖尿病有什么症状"))
        return []


class ActionSearchTreat(Action):
    def name(self) -> Text:
        return "action_search_treat"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        disease = tracker.get_slot("disease")
        pre_disease = tracker.get_slot("sure")
        print("pre_disease::::" + str(pre_disease))
        
        possible_diseases = retrieve_disease_name(disease)
        # if len(possible_diseases) == 1 or sure == "true":
        if disease == pre_disease or len(possible_diseases) == 1:
            a = graph.run("match (a:Disease{name: {disease}}) return a", disease=disease).data()[0]['a']
            if "intro" in a:
                intro = a['intro']
                template = "{0}的简介：{1}"
                retmsg = template.format(disease, intro)
            else:
                retmsg = disease + "暂无简介"
            dispatcher.utter_message(retmsg)
            if "treat" in a:
                treat = a['treat']
                template = "{0}的治疗方式有：{1}"
                retmsg = template.format(disease, "、".join(treat))
            else:
                retmsg = disease + "暂无常见治疗方式"
            dispatcher.utter_message(retmsg)
        elif len(possible_diseases) > 1:
            buttons = []
            for d in possible_diseases:
                buttons.append(make_button(d, '/search_treat{{"disease":"{0}", "sure":"{1}"}}'.format(d, d)))
            dispatcher.utter_button_message("请点击选择想查询的疾病，若没有想要的，请忽略此消息", buttons)
        else:
            dispatcher.utter_message("知识库中暂无与 {0} 疾病相关的记录".format(disease))
        return []


class ActionSearchFood(Action):
    def name(self) -> Text:
        return "action_search_food"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        disease = tracker.get_slot("disease")
        pre_disease = tracker.get_slot("sure")
        print("pre_disease::::" + str(pre_disease))
        
        possible_diseases = retrieve_disease_name(disease)
        """ search_food db action here """
        food = dict()
        if disease == pre_disease or len(possible_diseases) == 1:
            m = [x['m.name'] for x in graph.run("match (a:Disease{name: {disease}})-[:can_eat]->(m:Food) return m.name",
                          disease=disease).data()]
            food['can_eat'] = "、".join(m) if m else "暂无记录"

            m = [x['m.name'] for x in graph.run("match (a:Disease{name: {disease}})-[:not_eat]->(m:Food) return m.name",
                          disease=disease).data()]

            food['not_eat'] = "、".join(m) if m else "暂无记录"

            retmsg = "在患 {0} 期间，可以食用：{1}，\n但不推荐食用：{2}".\
                            format(disease, food['can_eat'], food['not_eat'])

            dispatcher.utter_message(retmsg)
        elif len(possible_diseases) > 1:
            buttons = []
            for d in possible_diseases:
                buttons.append(make_button(d, '/search_food{{"disease":"{0}", "sure":"{1}"}}'.format(d, d)))
            dispatcher.utter_button_message("请点击选择想查询的疾病，若没有想要的，请忽略此消息", buttons)
        else:
            dispatcher.utter_message("知识库中暂无与 {0} 相关的饮食记录".format(disease))
        return []


class ActionSearchSymptom(Action):
    def name(self) -> Text:
        return "action_search_symptom"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        disease = tracker.get_slot("disease")
        pre_disease = tracker.get_slot("sure")
        print("pre_disease::::" + str(pre_disease))
        
        possible_diseases = retrieve_disease_name(disease)
        if disease == pre_disease or len(possible_diseases) == 1:
            a = [x['s.name'] for x in graph.run("MATCH (p:Disease{name: {disease}})-[r:has_symptom]->\
                                                (s:Symptom) RETURN s.name", disease=disease).data()]
            template = "{0}的症状可能有：{1}"
            retmsg = template.format(disease, "、".join(a))
            dispatcher.utter_message(retmsg)
        elif len(possible_diseases) > 1:
            buttons = []
            for d in possible_diseases:
                buttons.append(make_button(d, '/search_symptom{{"disease":"{0}", "sure":"{1}"}}'.format(d, d)))
            dispatcher.utter_button_message("请点击选择想查询的疾病，若没有想要的，请忽略此消息", buttons)
        else:
            dispatcher.utter_message("知识库中暂无与 {0} 相关的症状记录".format(disease))

        return []


class ActionSearchCause(Action):
    def name(self) -> Text:
        return "action_search_cause"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        disease = tracker.get_slot("disease")
        pre_disease = tracker.get_slot("sure")
        print("pre_disease::::" + str(pre_disease))
        
        possible_diseases = retrieve_disease_name(disease)
        if disease == pre_disease or len(possible_diseases) == 1:
            a = graph.run("match (a:Disease{name: {disease}}) return a.cause", disease=disease).data()[0]['a.cause']
            if "treat" in a:
                treat = a['treat']
                template = "{0}的治疗方式有：{1}"
                retmsg = template.format(disease, "、".join(treat))
            else:
                retmsg = disease + "暂无该疾病的病因的记录"
            dispatcher.utter_message(retmsg)
        elif len(possible_diseases) > 1:
            buttons = []
            for d in possible_diseases:
                buttons.append(make_button(d, '/search_cause{{"disease":"{0}", "sure":"{1}"}}'.format(d, d)))
            dispatcher.utter_button_message("请点击选择想查询的疾病，若没有想要的，请忽略此消息", buttons)
        else:
            dispatcher.utter_message("知识库中暂无与 {0} 相关的原因记录".format(disease))
        return []


class ActionSearchNeopathy(Action):
    def name(self) -> Text:
        return "action_search_neopathy"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        disease = tracker.get_slot("disease")
        pre_disease = tracker.get_slot("sure")
        print("pre_disease::::" + str(pre_disease))
        
        possible_diseases = retrieve_disease_name(disease)
        if disease == pre_disease or len(possible_diseases) == 1:
            a = [x['s.name'] for x in graph.run("MATCH (p:Disease{name: {disease}})-[r:has_neopathy]->\
                                                (s:Disease) RETURN s.name", disease=disease).data()]
            template = "{0}的并发症可能有：{1}"
            retmsg = template.format(disease, "、".join(a))
            dispatcher.utter_message(retmsg)
        elif len(possible_diseases) > 1:
            buttons = []
            for d in possible_diseases:
                buttons.append(make_button(d, '/search_neopathy{{"disease":"{0}", "sure":"{1}"}}'.format(d, d)))
            dispatcher.utter_button_message("请点击选择想查询的疾病，若没有想要的，请忽略此消息", buttons)
        else:
            dispatcher.utter_message("知识库中暂无与 {0} 相关的并发症记录".format(disease))
        return []


class ActionSearchDrug(Action):
    def name(self) -> Text:
        return "action_search_drug"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        disease = tracker.get_slot("disease")
        pre_disease = tracker.get_slot("sure")
        print("pre_disease::::" + str(pre_disease))
        
        possible_diseases = retrieve_disease_name(disease)
        if disease == pre_disease or len(possible_diseases) == 1:
            a = [x['s.name'] for x in graph.run("MATCH (p:Disease{name: {disease}})-[r:can_use_drug]->\
                                                (s:Drug) RETURN s.name", disease=disease).data()]
            if a:
                template = "在患 {0} 时，可能会用药：{1}"
                retmsg = template.format(disease, "、".join(a))
            else:
                retmsg = "无 %s 的可能用药记录" % disease
            dispatcher.utter_message(retmsg)
        elif len(possible_diseases) > 1:
            buttons = []
            for d in possible_diseases:
                buttons.append(make_button(d, '/search_drug{{"disease":"{0}", "sure":"{1}"}}'.format(d, d)))
            dispatcher.utter_button_message("请点击选择想查询的疾病，若没有想要的，请忽略此消息", buttons)
        else:
            dispatcher.utter_message("知识库中暂无与 {0} 相关的用药记录".format(disease))
        return []


class ActionSearchPrevention(Action):
    def name(self) -> Text:
        return "action_search_prevention"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        disease = tracker.get_slot("disease")
        pre_disease = tracker.get_slot("sure")
        print("pre_disease::::" + str(pre_disease))
        
        possible_diseases = retrieve_disease_name(disease)
        if disease == pre_disease or len(possible_diseases) == 1:
            a = graph.run("match (a:Disease{name: {disease}}) return a.prevent", disease=disease).data()[0]
            if 'a.prevent' in a:
                prevent = a['a.prevent']
                template = "以下是有关预防 {0} 的知识：{1}"
                retmsg = template.format(disease, md(prevent.replace('\n', '<br/>')))
            else:
                retmsg = disease + "暂无常见预防方法"
            dispatcher.utter_message(retmsg)
        elif len(possible_diseases) > 1:
            buttons = []
            for d in possible_diseases:
                buttons.append(make_button(d, '/search_prevention{{"disease":"{0}", "sure":"{1}"}}'.format(d, d)))
            dispatcher.utter_button_message("请点击选择想查询的疾病，若没有想要的，请忽略此消息", buttons)
        else:
            dispatcher.utter_message("知识库中暂无与 {0} 相关的预防记录".format(disease))
        return []


class ActionSearchDrugFunc(Action):
    def name(self) -> Text:
        return "action_search_drug_func"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        drug = tracker.get_slot("drug")
        if drug:
            a = [x['n.name'] for x in graph.run("match (n:Disease)-[:can_use_drug]->(a:Drug{name: {drug}})"
                                                "return n.name", drug=drug).data()]
            template = "{0} 可用于治疗疾病：{1}"
            retmsg = template.format(drug, "、".join(a))
        else:
            retmsg = drug + " 在疾病库中暂无可治疗的疾病"
        dispatcher.utter_message(retmsg)
        return []


class ActionSearchDiseaseTreatTime(Action):
    def name(self) -> Text:
        return "action_search_disease_treat_time" # treat_period

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        disease = tracker.get_slot("disease")
        pre_disease = tracker.get_slot("sure")
        print("pre_disease::::" + str(pre_disease))
        
        possible_diseases = retrieve_disease_name(disease)
        if disease == pre_disease or len(possible_diseases) == 1:
            a = graph.run("match (a:Disease{name: {disease}}) return a", disease=disease).data()[0]['a']
            if "treat_period" in a:
                treat_period = a['treat_period']
                template = "{0}需要的治疗时间：{1}"
                retmsg = template.format(disease, treat_period)
            else:
                retmsg = disease + "暂无治疗时间的记录"
            dispatcher.utter_message(retmsg)
        elif len(possible_diseases) > 1:
            buttons = []
            for d in possible_diseases:
                buttons.append(make_button(d, '/search_disease_treat_time{{"disease":"{0}", "sure":"{1}"}}'.format(d, d)))
            dispatcher.utter_button_message("请点击选择想查询的疾病，若没有想要的，请忽略此消息", buttons)
        else:
            dispatcher.utter_message("知识库中暂无与 {0} 相关的治疗时间记录".format(disease))
        return []


class ActionSearchEasyGet(Action):
    def name(self) -> Text:
        return "action_search_easy_get"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        disease = tracker.get_slot("disease")
        pre_disease = tracker.get_slot("sure")
        print("pre_disease::::" + str(pre_disease))
        
        possible_diseases = retrieve_disease_name(disease)
        if disease == pre_disease or len(possible_diseases) == 1:
            a = graph.run("match (a:Disease{name: {disease}}) return a", disease=disease).data()[0]['a']
            easy_get = a['easy_get']
            template = "{0}的易感人群是：{1}"
            retmsg = template.format(disease, easy_get)
            dispatcher.utter_message(retmsg)
        elif len(possible_diseases) > 1:
            buttons = []
            for d in possible_diseases:
                buttons.append(make_button(d, '/search_easy_get{{"disease":"{0}", "sure":"{1}"}}'.format(d, d)))
            dispatcher.utter_button_message("请点击选择想查询的疾病，若没有想要的，请忽略此消息", buttons)
        else:
            dispatcher.utter_message("知识库中暂无与 {0} 相关的易感人群记录".format(disease))
        return []


class ActionSearchDiseaseDept(Action):
    def name(self) -> Text:
        return "action_search_disease_dept"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        disease = tracker.get_slot("disease")
        pre_disease = tracker.get_slot("sure")
        print("pre_disease::::" + str(pre_disease))
        
        possible_diseases = retrieve_disease_name(disease)
        if disease == pre_disease or len(possible_diseases) == 1:
            a = graph.run("match (a:Disease{name: {disease}})-[:belongs_to]->(s:Department) return s.name",
                          disease=disease).data()[0]['s.name']
            template = "{0} 属于 {1}"
            retmsg = template.format(disease, a)
            dispatcher.utter_message(retmsg)
        elif len(possible_diseases) > 1:
            buttons = []
            for d in possible_diseases:
                buttons.append(make_button(d, '/search_disease_dept{{"disease":"{0}", "sure":"{1}"}}'.format(d, d)))
            dispatcher.utter_button_message("请点击选择想查询的疾病，若没有想要的，请忽略此消息", buttons)
        else:
            dispatcher.utter_message("知识库中暂无与 {0} 疾病相关的科室记录".format(disease))
        return []
