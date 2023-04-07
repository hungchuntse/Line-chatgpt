import sched
import time
import requests
import googlemaps

scheduler = sched.scheduler(time.time, time.sleep)

def info(place):
    api_key = 'AIzaSyAh9gXsAU2oiQzWeVOjqkfHWEiHqtSw2oc'
    #將API憑證用以下指令包起來
    gmaps=googlemaps.Client(key=api_key)

    #簡單的調用資料示範
    geocode_result = gmaps.geocode(place)
    place_id = geocode_result[0]['place_id']
    return place_id, api_key


def check_new_review(place_id, api_key):
    global last_review_text
    last_review_text = ' '
    review_text, review_rating = [], []

    # API 請求 URL
    url = 'https://maps.googleapis.com/maps/api/place/details/json?place_id={}&fields=review&key={}&reviews_no_translations=true&reviews_sort=newest'.format(place_id, api_key)
    response = requests.get(url)

    # get review
    if 'reviews' in response.json()['result']:
        reviews = response.json()['result']['reviews']
        for review in reviews:
            if review['text'] == '':
                pass
            elif review['text'] != last_review_text:
                review_text.append(review['text'].replace('\n',' '))
                review_rating.append(review['rating'])
            else:
                last_review_text = reviews[0]['text']
                break            
    else:
        pass

    return review_text, review_rating

def run_scheduler(place):
    place_id, api_key = info(place)
    review_text, review_rating = [], []
    scheduler.enter(300, 1, run_scheduler, ())
    review_text, review_rating = check_new_review(place_id, api_key)
    return review_text, review_rating

# # 安排定時任務，每5分鐘檢查有無新評論
def run_scheduler_time(place):
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