#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
    SSK予想
    DANGER!!
    This is very crazy!
'''

import datetime
import random
import sqlite3
import urllib.request
from bs4 import BeautifulSoup
from decimal import Decimal, ROUND_HALF_UP

global score
global margin
global now #判定する日


def main(day="now"):
    global score
    global margin
    global now

    db_connect = sqlite3.connect("ssk_bigdata.db")
    db = db_connect.cursor()
    

    if day == "now":
        now = datetime.datetime.today()
    else:
        now = day

    week = now.weekday()

    sql = "insert into access_log (date) values ('{}');".format(datetime.datetime.today())
    db.execute(sql)

    sql = "select threshold from weekday_threshold where week_id = {};".format(week)
    result = db.execute(sql)
    for row in result:
        score = row[0]

    if week == 3:
        #Thursday
        score += 10

    seven_days_ago = now.date() - datetime.timedelta(days=7)
    sql = "select count(date) from login_days where date like '{}';".format(seven_days_ago)
    result = db.execute(sql)
    for row in result:
        count = row[0]
    if count <= 1:
        score = score + score*0.5

    sql = "select max(date(date)) from login_days;"
    result = db.execute(sql)
    for row in result:
        last_login = datetime.datetime.strptime(row[0], "%Y-%m-%d")
    margin =  (now.date() - last_login.date()).days
    if margin <= 7:
        score = score + score * (margin*0.1)
    elif margin > 7:
        score = score - score * (margin/50)

    html = urllib.request.urlopen("https://www.jma.go.jp/jp/yoho/319.html")
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="rain")
    rainy_percent_array = table.getText().split()
    if 0 <= now.hour < 6:
        rainy_percent = rainy_percent_array[1].replace("%", "")
    elif 6 <= now.hour < 12:
        rainy_percent = rainy_percent_array[3].replace("%", "")
    elif 12 <= now.hour < 18:
        rainy_percent = rainy_percent_array[5].replace("%", "")
    elif 18 <= now.hour <24:
        rainy_percent = rainy_percent_array[7].replace("%", "")

    if not rainy_percent == "--":
        rainy_percent = int(rainy_percent)
        if rainy_percent >= 60:
            score = score - score*0.4
        elif rainy_percent >= 80:
            score = score - score*0.6
    else:
        #print("no wether")
        pass

    feel = random.randrange(-10, 10)/100
    score = score + score*feel

    score = Decimal(str(score)).quantize(Decimal('0'), rounding=ROUND_HALF_UP)

    if score <= 0:
        score = 1
        pass
    elif score >= 100:
        score = 99

    db_connect.commit()
    db_connect.close()


def resultHypothesis(day="now"):
    '''
        return result
        day: Date to calculate ssk appearance probability (type is datetime)
             If omitted, today is used
        result: result dict
        score: Occurrence probability of ssk
        margin: Cumulative absence days
        now: Expected date
    '''
    main(day)
    result = {}
    result["score"] = score
    result["margin"] = margin
    result["now"] = now
    return result


if __name__ == '__main__':
    '''
        ローカル変数 day のコメントアウトを解除すると指定日での予想を行う
    '''
    #day = datetime.datetime(2018, 10, 17, 12, 0, 0)


    if 'day' in locals():
        result = resultHypothesis(day)
        print("SSK予想")
        print("{} の予想は {}%！".format(result["now"], result["score"]))
    else:
        result = resultHypothesis()
        print("SSK予想")
        print("{} の予想は {}%！\n{}日連続で来ていません！".format(result["now"], result["score"], result["margin"]))
