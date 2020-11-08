import logging
import MySQLdb


logger = logging.getLogger(__name__)


def get_record_db_cursor():
    try:
        db = MySQLdb.connect(
            host="localhost",
            port=3306,
            user="doctor-friende",
            passwd="doctor-friende",
            db="doctor_friende",
            charset="utf8"
        )
    except Exception as e:
        logger.error(e)
    else:
        return db.cursor()





# import requests
# from json import dumps


# api_addr = 'http://127.0.0.1:8000/api/'


# def save_message(data: dict):
#     # data = {'message': '你好', 'customData': {'user_id': 7}, 'session_id': 'b9c6bb643e194746b278f0438215daba'}
#     tail = "testSaveChat/"
#     record = {
#         "content": data["message"],
#         "from_user_id": data["customData"]["from_user_id"],
#         "session_id": data["session_id"],
#         "when": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
#     }
#     response = requests.post(url=api_addr+tail, data=dumps(data))
#     print(response.text)

