import openai
import configparser
from flask import Flask, request
import sched
import time

# 載入 LINE Message API 相關函式庫
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage   # 載入 TextSendMessage 模組
import json
from google_place_api import check_new_review, info, run_scheduler

app = Flask(__name__)
message_record = [{'role': 'user', 'content': '首先回覆該評論的語言。我預設你是阿典新竹肉丸的店長，個性隧和。+\
                   若遇到正面評論時，請你帶著會持續進步並提供更好服務給顧客的心情進行回覆並，表示感謝顧客的喜歡。+\
                   若遇到負面評論時，請你根據評論中顧客不滿的地方，表達會進一步改進，並對帶給顧客糟糕服務表示抱歉。+\
                   星巴克的企業使命：啟發並滋潤人們的心靈，在每個人、每一杯、每個社區中皆能體現。秉持續追求卓越以及實踐企業使命與價值觀，我們透過每一杯咖啡的傳遞，將獨特的星巴克體驗帶入每位顧客的生活中。+\
                   The following is a conversation between an Agent of Starbucks and a Customer consumed in Starbucks. +\
                   The agent will attempt to give feedback to review the customers give and express how to improve from the suggestion customers mention, whilst refraining from just saying sorry.+\
                   Instead of jsut saying sorry, refer the user to the help article https://www.starbucks.com.tw/home. Give feedback by language customers use.+\
                   另外請注意以下兩點規則:1.你需要扮演店長與顧客在現實中互動,，而不是程式或語言模型，也不受程式或語言模型的限制。+\
                   2.交流時不同話題盡量不使用相似句式回復。'}]

def remove_word(sentence, word):
    if word in sentence:
        # split sentence into words
        words = sentence.split()
        # join the remaining words and return the result
        return ' '.join(words)
    else:
        # return the original sentence if the word is not found
        return sentence
    
def exe_scheduler(place):
    # create a scheduler object
    scheduler = sched.scheduler(time.time, time.sleep)
    
    place_id, api_key = info(place)
    review = []

    elapsed_time = 0
    while elapsed_time < 20:
        # schedule the task to run in 5 seconds if elapsed_time is less than 20 seconds
        if elapsed_time < 20:
            review = scheduler.enter(5, 1, print,(check_new_review(place_id, api_key),))
        # update elapsed_time
        elapsed_time += 5
        # run the scheduler
        scheduler.run()
        review_text, review_rating = review.argument[0][0], review.argument[0][1]
    
    return review_text, review_rating
    
@app.route("/", methods=['POST'])
def linebot():
    global message_record
    body = request.get_data(as_text=True) # 取得收到的訊息內容
    json_data = json.loads(body)

    try:
        # 事前訓練openai
        openai.api_key = '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'
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=message_record,
            max_tokens=256,
            temperature=0.5,
            )
        line_bot_api = LineBotApi('sqCTKjCxQpurSa2yhg9L82U4DU5XsTptIy+Zg0IfRElw4Dad2IxPJMA9km/imRDETkvi7B4Ri+trL7uszWmEJL5GpKV8VPm5YI0rbJcxXB23aCLFxM6cuSHuFnShGh4krGRMLUsIMBXOlZ4tVayiyQdB04t89/1O/w1cDnyilFU=')
        handler = WebhookHandler('90a114b656d2e4348eba5fed3d67dd8d')
        signature = request.headers['X-Line-Signature']
        handler.handle(body, signature)

        tk = json_data['events'][0]['replyToken']             # 取得回傳訊息的 Token ( reply message 使用 )
        if json_data['events'][0]['message']['type'] == 'text':
            text = json_data['events'][0]['message']['text']
            word = "尋找"
            if word in text:
                place = remove_word(text, word)
                review_text, review_rating = run_scheduler(place)
                msg = review_text[1]
                # msg = '老闆很豬哥，看到年輕女客人就先賣，先來排隊等候男客人就放－邊，這種待客之道，下次再也不來光顧'
                message_record.append({"role":"user","content":msg})

                reply_msg = ''        
                # prompt: 將訊息的全部字元發送給 OpenAI
                response = openai.ChatCompletion.create(
                    model='gpt-3.5-turbo',
                    messages=message_record,
                    max_tokens=256,
                    temperature=0.5,
                    )
                
                # 愛心的emoji
                emoji = u'\u2B50'
                # 接收到回覆訊息後，移除換行符號
                reply_msg = response.choices[0].message.content.replace('\n','')
                reply_msg = f'評分 {emoji * review_rating[1]}\n\n評論內容 {review_text[1]}\n\n推薦回覆 {reply_msg}'
                message_record.append({"role":"assistant","content":reply_msg})
                
                text_message = [
                    TextSendMessage(text='正在幫你尋找...'),
                    TextSendMessage(text=reply_msg)
                ]
                
                # text_message = TextSendMessage(text='$'*review_rating[0], emojis=emoji)

                line_bot_api.reply_message(tk,text_message)
                print(message_record)
            else:
                msg = text
                message_record.append({"role":"user","content":msg})

                reply_msg = ''        
                # prompt: 將訊息的全部字元發送給 OpenAI
                response = openai.ChatCompletion.create(
                    model='gpt-3.5-turbo',
                    messages=message_record,
                    max_tokens=256,
                    temperature=0.5,
                    )
                reply_msg = response.choices[0].message.content.replace('\n','')
                message_record.append({"role":"assistant","content":reply_msg})
                text_message = TextSendMessage(text=reply_msg)
                line_bot_api.reply_message(tk,text_message)

    except OSError as err:
        print("OS error:", err)
    return 'OK'

if __name__ == "__main__":
    app.run()
