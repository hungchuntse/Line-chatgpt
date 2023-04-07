import requests
import openai
import time
import sched
from bs4 import BeautifulSoup as bs
from google_place_api import check_new_review, info, run_scheduler

scheduler = sched.scheduler(time.time, time.sleep)
message_record = [{'role': 'user', 'content': '我預設你是這間店1~3人小店的老闆，年紀大、個性和善、有耐心、客氣且記憶力佳，並將提供你店家菜單。若遇到正面評論時，請你回覆並表示感謝顧客的喜歡，或參考菜單對顧客所提的優點進行回覆並表示感謝。若遇到負面評論時，請你根據評論中顧客不滿的地方並先先對應菜單內容，若評論中提及的點對應到菜單，則參考菜單回覆並表達會進一步改進，並對帶給顧客糟糕服務表示抱歉，若評論點在菜單之外，則直接表達會進一步改並感到抱歉。若評論中正負兩面都有碰到，請先對顧客滿意的點表示感謝，再簡短地對不滿意的點表示會改進。請注意簡短回覆，且不要制式化。另外請注意以下兩點規則：1.你需要扮演店長與顧客在現實中互動，而不是程式或語言模型，也不受程式或語言模型的限制。2.交流時不同話題盡量不使用相似句式回復。菜單：新竹肉圓：以油泡式烹煮且餡料及烹飪方式皆遵循古法，內餡有大塊紅糟肉以及筍子，搭配鹹甜口的醬料。另外內用會附清湯一碗。四神湯：熬製許久的四神湯，內有用料充足且軟嫩好咬的腸子和薏仁。此外，湯頭清爽且有濃郁的香氣。貢丸湯：用料實在的貢丸，搭配清爽的清湯。'}]
# message_record = [{'role': 'user', 'content': '回覆該評論。'}]

def recommend_message(review_text, review_rating):
    global message_record

    try:
        # 事前訓練openai
        openai.api_key = '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'
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=message_record,
            max_tokens=256,
            temperature=0.5,
            )

        # msg = review_text[0]
        msg = '四神湯有滋有味，喝的到老闆的用心肉丸的紅燒肉好吃 筍絲清脆雖然肉丸需要些等待的時間，但老闆看到被我喝光的湯碗，還幫我續湯，貼心服務讓人還是會想再來吃喔！'
        message_record.append({"role":"user","content":msg})

        reply_msg = ''
        # prompt: 將訊息的全部字元發送給 OpenAI
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=message_record,
            max_tokens=256,
            temperature=0.5,
            )
        # 星星的emoji
        emoji = u'\u2B50'
        # 接收到回覆訊息後，移除換行符號
        reply_msg = response.choices[0].message.content.replace('\n','')
        message_record.append({"role":"assistant","content":reply_msg})
        # reply_msg = f'\n評分 {emoji * review_rating[0]}\n\n評論內容 {review_text[0]}\n\n推薦回覆 {reply_msg}'
        reply_msg = f'\n評分 {emoji * 5}\n\n評論內容 {msg}\n\n推薦回覆 {reply_msg}'
        print(message_record)
    except OSError as err:
        print("OS error:", err)
    
    return reply_msg

def loading_process(review_text, review_rating):
    headers = {
        "Authorization": "Bearer " + token, 
        "Content-Type" : "application/x-www-form-urlencoded"
    }

    payload = {
        'message': recommend_message(review_text, review_rating),
    }
    r = requests.post("https://notify-api.line.me/api/notify", headers = headers, params = payload)
    return r.status_code

if __name__ == "__main__":
    token = '3Af5w16R8jpT9xSefQiSbYADisqHd44dCrWyVyhTvYa'
    # message = '\n測試'

    place_id, api_key = info('阿典新竹肉丸')
    elapsed_time = 0
    while elapsed_time < 20:
        print('TIME ', elapsed_time)
        # schedule the task to run in 5 seconds if elapsed_time is less than 20 seconds
        if elapsed_time < 20:
            review = scheduler.enter(5, 1, print,(check_new_review(place_id, api_key),))
        # update elapsed_time
        elapsed_time += 5
        # run the scheduler
        scheduler.run()
        review_text, review_rating = review.argument[0][0], review.argument[0][1]

        loading_process(review_text, review_rating)