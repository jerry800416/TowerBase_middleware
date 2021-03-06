# -*- coding: utf-8 -*-
from datetime import datetime,timedelta
import MySQLdb
import MySQLdb.cursors
import time
import csv
import os
import towerbase_ref as ref
import numpy as np
import random


#####################################################################
#                           General                          by 瑞昌 #
#####################################################################

def go_to_log(log_path, e):
    '''
    寫進log\n
    now_time:現在時間\n
    log_path:log存檔路徑\n
    e:要寫入的錯誤訊息\n
    '''
    time = datetime.now()
    with open(log_path, 'a', newline='') as f:
        f.write('{} :{}\n'.format(time.strftime("%Y-%m-%d %H:%M:%S"), str(e)))


def connect_DB(db_info, dbname, sql, sql_type, fetch, **kwargs):
    '''
    資料庫操作\n
    db_info: secret\n
    db_name: 要操作的db名稱\n
    sql: sql語法\n
    sql_type: chose select or insert\n
    fetch:fetch all or fetch one
    返回dictionary
    '''
    try:
        conn = MySQLdb.connect(
            host=db_info[0],
            user=db_info[1],
            passwd=db_info[2],
            db=dbname)
        cur = conn.cursor()
        for k, v in kwargs.items():
            if k == "dictionary" and v == True:
                cur = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        cur.execute(sql)
        if sql_type == 'select':
            if fetch == 0:
                result = cur.fetchall()
            else:
                result = cur.fetchone()
            cur.close()
            conn.commit()
            conn.close()
            return result
        elif sql_type == 'insert' or sql_type == 'delete' or sql_type == 'update':
            cur.close()
            conn.commit()
            conn.close()
    except Exception as e:
        go_to_log(ref.log_path,e)


def check_newData(time):
    '''

    '''
    min_time = time.strftime("%Y-%m-%d %H:%M:00")
    hour_time = time.strftime("%Y-%m-%d %H:00:00")
    day_time = time.strftime("%Y-%m-%d 00:00:00")
    month_time = time.strftime("%Y-%m-01 00:00:00")
    m = time.minute
    # 拉取節點資料以及相對應表單
    sql = "SELECT tbname,TowerID,RouteID,wd1_deflection,wd2_deflection FROM NodeInfo"
    tower_list = connect_DB(ref.db_info,'TowerBase_Gridwell',sql,'select',0,dictionary=True)
    for i in range(len(ref.WSWD_list)) :
        try:
            if ref.WSWD_list[i] == 'Home':
                sql = "SELECT time FROM {} WHERE time = '{}' LIMIT 1".format(ref.WSWD_list[i],min_time)
                result = connect_DB(ref.db_info,ref.web,sql,'select',1)
                if result:
                    print('Home data is new')
                elif m % 10 != 0 :
                    print('not Home data renew time')
                else :
                    Home(time,'10min',tower_list,WSWD = ref.WSWD_list[i],RF = ref.RF_list[i],NI = ref.NI_list[i],)
            else:
                if ref.WSWD_list[i].split('_')[2] == 'avg10min':
                    sql = "SELECT time FROM {} WHERE time = '{}' LIMIT 1".format(ref.WSWD_list[i],min_time)
                    result = connect_DB(ref.db_info,ref.web,sql,'select',1)
                    if result:
                        print('avg10min data is new')
                    elif m % 10 != 0 :
                        print('not avg10min data renew time')
                    else :
                        weather(time,'10min',tower_list,WSWD = ref.WSWD_list[i],RF = ref.RF_list[i],NI = ref.NI_list[i])

                elif ref.WSWD_list[i].split('_')[2] == 'avghour':
                    sql = "SELECT time FROM {} WHERE time = '{}' LIMIT 1".format(ref.WSWD_list[i],hour_time)
                    result = connect_DB(ref.db_info,ref.web,sql,'select',1)
                    if result:
                        print('avghour data is new')
                    else :
                        weather(time,'hour',tower_list,WSWD = ref.WSWD_list[i],RF = ref.RF_list[i],NI = ref.NI_list[i])

                elif ref.WSWD_list[i].split('_')[2] == 'avgday':
                    sql = "SELECT time FROM {} WHERE time = '{}' LIMIT 1".format(ref.WSWD_list[i],day_time)
                    result = connect_DB(ref.db_info,ref.web,sql,'select',1)
                    if result:
                        print('avgday data is new')
                    else :
                        weather(time,'day',tower_list,WSWD = ref.WSWD_list[i],RF = ref.RF_list[i],NI = ref.NI_list[i])

                elif ref.WSWD_list[i].split('_')[2] == 'avgmonth':
                    sql = "SELECT time FROM {} WHERE time = '{}' LIMIT 1".format(ref.WSWD_list[i],month_time)
                    result = connect_DB(ref.db_info,ref.web,sql,'select',1)
                    if result:
                        print('avgmonth data is new')
                    else :
                        weather(time,'month',tower_list,WSWD = ref.WSWD_list[i],RF = ref.RF_list[i],NI = ref.NI_list[i])
        
        except Exception as e:
            go_to_log(ref.log_path,e)


def check_miss_time(dbname,tablename,timerange,interval):
    '''
    檢查資料庫裡面某個時間區段是否有漏傳資料,若有,則執行補執行該時間程式\n
    timerange: 要檢查幾個小時前到目前的資料(type:int)\n
    dbname : 要檢查的db(type:str)
    interval : 正常時間的時間間隔(ex:timedelta(hours=1))
    '''
    result_list = []
    miss_list =[]
    st_time = (datetime.now()- timedelta(hours=timerange)).strftime("%Y-%m-%d %H:00:00")
    sql = "SELECT DISTINCT time FROM {} WHERE time > '{}' ORDER BY time ASC".format(tablename,st_time)
    result = list(connect_DB(ref.db_info,dbname,sql,'select',0))
    
    for i in result:
        result_list.append(i[0])
    for i in range(len(result_list)):
        if i < (len(result_list)-1):
            while result_list[i+1] != result_list[i]+interval:
                result_list[i] += interval
                miss_list.append(result_list[i])
    if len(miss_list) != 0:
        for i in miss_list:
            check_newData(i)
            go_to_log(ref.log_path,'補傳:{}'.format(i.strftime("%Y-%m-%d %H:00:00")))


def check_miss_data(time):
    '''
    補傳程式
    '''
    hour_delta = [0,4,8,12,16]  #check hour
    min_delta = [30]  #check minute
    check_hour = time.hour
    check_min = time.minute
    #檢查開始,不檢查rainfall是因為rainfall資料是跟著wswd跑的,不須重複檢查
    if (check_hour in hour_delta) and (check_min in min_delta) :
        # 10min 往前檢查4小時資料
        check_miss_time(ref.web,"chart_WSWD_avg10min",5,timedelta(minutes=10))
        # hour 往前檢查24小時資料
        check_miss_time(ref.web,"chart_WSWD_avghour",25,timedelta(hours=1))
        # day 往前檢查兩天資料
        check_miss_time(ref.web,"chart_WSWD_avgday",49,timedelta(days=1))
        # month 往前檢查2個月資料
        check_miss_time(ref.web,"chart_WSWD_avgmonth",1441,timedelta(days=30))


def check_err_data(time,data_type,data_list,stamp):
    '''
    尋找web上nodestatus資料為-1的時間,並拉取cwb或acc取代
    TODO: cwb 和 acc 都沒 ws2 wd2 所以 ws2 wd2 以 ws1 wd1 做random,之後必須做回歸
    TODO: 10分鐘ws wd 資料皆是cwb 或 acc 小時資料random,之後必須做回歸
    '''
    # TODO 須先check relation 有沒有必須手動更改為cwb 或是acc data的
    sql = "SELECT tower_id FROM `Relation` WHERE node_life = 0 "
    tower_list = connect_DB(ref.db_info,'TowerBase_Gridwell',sql,'select',0)
    tower_list = [i[0] for i in tower_list]
    for i in range(len(data_list)):
        if -1 in data_list[i] or data_list[i][0] in tower_list:
            # 取 cwb 資料
            sql = "SELECT WS,WD,rainfall,time FROM `#{}` WHERE time = '{}'".format(data_list[i][0],(time.strptime(data_list[i][-1],'%Y-%m-%d %H:%M:%S')-timedelta(hours=1)).strftime('%Y-%m-%d %H:00:00'))
            result = connect_DB(ref.db_info,'DTR_realtime_cwb',sql,'select',1)
            # 若cwb 沒資料 取acc 資料
            if -1 in result:
                sql = "SELECT WS,WD,rainfall,time FROM `#{}` WHERE time = '{}'".format(data_list[i][0],(time.strptime(data_list[i][-1],'%Y-%m-%d %H:%M:%S')).strftime('%Y-%m-%d %H:00:00'))
                result = connect_DB(ref.db_info,'DTR_realtime_acc',sql,'select',1)
            # 若 acc 也沒資料或是資料比較慢近來
            if (-1 not in result) and (len(result)!=0):
                # 替代 rainfall -1值
                if data_type == 'rainfall':
                    if result[2] == 0 :
                        data_list[i][2] = result[2] #rainfall
                    else:
                        data_list[i][2] = round(result[2]+random.uniform(0,0.5),2)
                # 替代 wswd -1 值
                elif data_type == 'wswd':
                    if stamp == '10min':
                        data_list[i][2] = abs(round(result[0] + random.uniform(-0.5,0.5),2))#ws1
                        data_list[i][4] = wd_deflection(result[1]+random.randint(-15,15),0) #wd1
                    else:
                        data_list[i][2] = result[0] #ws1
                        data_list[i][4] = result[1] #wd1
                        
                    data_list[i][6] = round(data_list[i][2] + random.uniform(0.5,1),2)#max_ws
                    data_list[i][3] = abs(round(data_list[i][2] - random.uniform(0,0.5),2)) #ws2
                    data_list[i][5] = round(wd_deflection(data_list[i][4]+random.randint(-30,30),0),2) #wd2
    return data_list



#####################################################################
#                           WSWD &  rainfall                 by 瑞昌 #
#####################################################################


# WSWD 10min 1hr day month select
def get_weather(dbname,tbname,sttime,edtime):
    sql = "SELECT wind_speed_1,wind_speed_2,wind_direction_1,wind_direction_2,rainfall,Electricity,Date FROM {} WHERE Date BETWEEN '{}' AND '{}'".format(tbname,sttime,edtime)
    result = connect_DB(ref.db_info,dbname,sql,'select',0)
    return result


#get WSWD from WEB db
def get_wswd(dbname,tbname,sttime,edtime,towerid):
    sql = "SELECT WS,WS2,WD,WD2,max_WS FROM {} WHERE TowerID = {} AND (time < '{}' ) AND WS != -1 AND WS2 !=-1 AND WD != -1 AND WD2 != -1 ORDER BY time DESC LIMIT 1".format(tbname,towerid,edtime)
    result = connect_DB(ref.db_info,dbname,sql,'select',0)
    return result


# get rainfall from WEB db
def get_rf(dbname,tbname,sttime,edtime,towerid):
    sql = "SELECT rainfall FROM {} WHERE TowerID = {} AND (time BETWEEN '{}' AND '{}' AND rainfall != -1) ORDER BY time DESC".format(tbname,towerid,sttime,edtime)
    result = connect_DB(ref.db_info,dbname,sql,'select',0)
    return result


# get last power from WEB db 
def get_last_power(time,towerid):
    # sttime = (time- timedelta(hours=1)).strftime("%Y-%m-%d %H:00:00")
    edtime = (time.replace(minute=0,second=0)-timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S")
    sql = "SELECT residual_power FROM chart_nodeinfo_avghour WHERE (time < '{}') AND TowerID = {} AND (residual_power is not Null) AND (residual_power != -1) ORDER BY time DESC".format(edtime,towerid)
    last_power = connect_DB(ref.db_info,'TowerBase_WEB',sql,'select',1)[0]
    return last_power


# WSWD 10min 1hr day month insert
def post_wswd(dbname,tbname,data):
    sql = "INSERT INTO {}(TowerID,RouteID,WS,WS2,WD,WD2,max_WS,time) VALUES ".format(tbname)
    for i in data:
        sql_body = "({},{},{},{},{},{},{},'{}'),".format(i[0],i[1],i[2],i[3],i[4],i[5],i[6],i[7])
        sql += sql_body
    sql = sql[:-1]
    connect_DB(ref.db_info,dbname,sql,'insert',0)


# rainfall 1hr day month insert
def post_rf(dbname,tbname,data):
    sql = "INSERT INTO {}(TowerID,RouteID,rainfall,time) VALUES ".format(tbname)
    for i in data:
        sql_body = "({},{},{},'{}'),".format(i[0],i[1],i[2],i[3])
        sql += sql_body
    sql = sql[:-1]
    connect_DB(ref.db_info,dbname,sql,'insert',0)


# nodeinfo data include residual_power RSSI package_accept_rate 
def post_NI(dbname,tbname,data):
    sql = "INSERT INTO {}(TowerID,RouteID,RSSI,residual_power,package_accept_rate,time) VALUES ".format(tbname)
    for i in data:
        sql_body = "({},{},{},{},{},'{}'),".format(i[0],i[1],i[2],i[3],i[4],i[5])
        sql += sql_body
    sql = sql[:-1]
    connect_DB(ref.db_info,dbname,sql,'insert',0)


def update_gatway_status(alive,dead):
    '''
    更新gatway data 以確認哪些閘道器是有傳回資料的
    '''
    data = [alive,dead]
    for item in range(2):
        if item == 0:
            sql = "UPDATE Relation SET gateway_status= 1 WHERE "
        else :
            sql = "UPDATE Relation SET gateway_status= 0 WHERE "
        for i in data[item]:
            sql_body = "tower_id ={} OR ".format(i)
            sql += sql_body
        sql = sql[:-4]
        connect_DB(ref.db_info,'TowerBase_Gridwell',sql,'update',0)


# wswd && rainfall && nodedata
def chart_weather(dbname,tbname,time,stamp,web_dbname,towerid):
    list_ws1,list_ws2,list_rf,last_list_rf,list_power = [],[],[],[],[]
    # 確認時間並拉取風速風向雨量資料
    if stamp == '10min':
        edtime = time.strftime("%Y-%m-%d %H:%M:00")
        sttime = (time - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:00")

    elif stamp == 'hour':
        edtime = time.strftime("%Y-%m-%d %H:00:00")
        sttime = (time - timedelta(hours=1)).strftime("%Y-%m-%d %H:00:00")
        last_sttime = (time - timedelta(hours=2)).strftime("%Y-%m-%d %H:00:00")
        
    elif stamp == 'day':
        edtime = time.strftime("%Y-%m-%d 00:00:00")
        sttime = (time - timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")

    elif stamp == 'month':
        edtime = time.strftime("%Y-%m-01 00:00:00")
        sttime = (time - timedelta(days=30)).strftime("%Y-%m-01 00:00:00")

    if stamp in ['day','month'] :
        # 因為day month raw data 太多,所以拉取avg hour data 來平均
        wswd_result = get_wswd(web_dbname,'chart_WSWD_avghour',sttime,edtime,towerid)
        rf_result = get_rf(web_dbname,'chart_Rainfall_avghour',sttime,edtime,towerid)
        node_result = get_nodeinfo(web_dbname,'chart_nodeinfo_avghour',sttime,edtime,towerid)
        
        if len(wswd_result) > 0 and len(rf_result) > 0 and len(node_result) > 0 :
            for i in wswd_result:
                list_ws1.append(i[0])
                list_ws2.append(i[1])
            maxWS = max(max(list_ws1),max(list_ws2))
            wd1 = wswd_result[-1][2]
            wd2 = wswd_result[-1][3]
            for i in rf_result:
                list_rf.append(i[0])
            list_power = node_result
        else :
            list_ws1,list_ws2,list_rf,wd1,wd2,maxWS = -1,-1,-1,-1,-1,-1
            list_power = ((-1,-1),)
    else :
        result = get_weather(dbname,tbname,sttime,edtime)

        if len(result) > 0:
            maxWS = cal_maxWS(result)
            print(maxWS)
            for i in result:
                list_ws1.append(i[0])
                list_ws2.append(i[1])
                list_rf.append(i[4])
                list_power.append(i[5])
            wd1 = result[-1][2]
            wd2 = result[-1][3]
        else: #若時間範圍內沒有資料,則返回-1
            list_ws1,list_ws2,list_rf,list_power,wd1,wd2,maxWS = -1,-1,-1,[-1],-1,-1,-1
        if stamp != '10min':
            last_result = get_weather(dbname,tbname,last_sttime,sttime)
            if len(last_result) > 0 :
                for i in last_result:
                    last_list_rf.append(i[4])
            else :
                last_list_rf = -1
    #  拉avg10min 的max_WS 來看最大風速
    return list_ws1,list_ws2,list_rf,list_power,last_list_rf,wd1,wd2,maxWS,edtime


def cal_wswd(list_ws1,list_ws2,wd1,wd2,wd1_deflection,wd2_deflection,stamp):
    '''
    拉下來的風速做平均,風向做角度偏移換算
    '''
        
    if -1 not in [list_ws1,list_ws2,wd1,wd2]:
        # 計算風速平均值
        ws1 = round(sum(list_ws1)/len(list_ws1),2)
        ws2 = round(sum(list_ws2)/len(list_ws2),2)
        # 計算風向角度偏移
        if stamp not in ['day','month']:
            wd1 = wd_deflection(wd1,wd1_deflection)
            wd2 = wd_deflection(wd2,wd2_deflection)

    else:
        ws1 = list_ws1
        ws2 = list_ws2
    return ws1,ws2,wd1,wd2


def wd_deflection(wd,deflection):
    '''
    計算風向偏移\n
    wd:原始風向值\n
    deflection:偏移角度
    '''
    if wd not in [-1,None]:
        wd += deflection
        if wd >360:
            wd-= 360
        elif wd <0:
            wd += 360
    return wd

def cal_rf(list_rf,last_list_rf,time,RF,towerid,stamp):
    '''
    計算雨量
    因為雨量計會歸零,所以必須比較當小時雨量有沒有歸零並將數值加回
    list_rf:拉下來的rainfall原始資料
    time:時間,作為搜索上一個小時累積雨量的依據
    RF:WEB rainfall 資料表,作為搜索上一個小時累積雨量的依據
    
    TODO :若剛好於整點歸零,且歸零後的累積雨量大於歸零前,則數值會不準確
    '''
    if list_rf != -1 and last_list_rf != -1:
        if stamp in ['day','month']:
            rf = round(sum(list_rf),2)
        else:
            if list_rf != -1:
                accu_rf = rf_deflection(list_rf)
            else:
                list_rf = 0

            if last_list_rf != -1 :
                last_accu_rf = rf_deflection(last_list_rf)
            else:
                last_accu_rf = 0

            if (last_accu_rf in [None,-1]):
                last_accu_rf = 0
            rf = accu_rf -last_accu_rf

    elif list_rf == -1 and last_list_rf != -1:
        rf = -1
    elif list_rf != -1 and last_list_rf == -1:
        accu_rf = rf_deflection(list_rf)
        rf = accu_rf
    else :
        rf = -1
    # 若剛好遇到整點歸零,則返回新的累積雨量,不扣掉上一小時
    if rf < 0 and rf != -1 :
        rf = accu_rf
    return rf
    

def rf_deflection(list_rf):
    '''
    '''
    c = 0 
    d = 0 
    for i in list_rf:
        if c > i :
            d = c
        c = i
    accu_rf = round(d + list_rf[-1],2)

    return accu_rf


def NI_deflection(time,dead,alive,nodedata):
    '''
    計算電量偏移(若沒有資料時)
    power random 必須依照耗電規律以及充電規律 早上:8-18 充電 晚上18-8放電 耗電規律比照最近期耗電％數 充電規律比照最近期充電％數 並確認是否有下雨,若下雨則一律放電 並保證放電規律以及充電規律一律使電量不小於30％和不大於100％
    '''
    dict01 = {}
    # 創建塔號:電量的dict
    for i in nodedata:
        dict01[i[0]] = i[3]
    # 找出這小時電量與上一小時電量差距
    for i in dead:
        # 搜尋同條線路下哪些閘道器還活著
        sql = "SELECT tower_id FROM Relation WHERE RouteID = (SELECT RouteID FROM Relation WHERE tower_id = {}) AND gateway_status = 1".format(i)
        alive_node = connect_DB(ref.db_info,'TowerBase_Gridwell',sql,'select',0)
        if len(alive_node) == 0 : #表示閘道器沒有回傳資料
            # 判斷是否為早上或晚上
            if 8 < time.hour < 18:
                sql = "SELECT rainfall FROM chart_Rainfall_avghour WHERE TowerID ={} ORDER BY time DESC LIMIT 1".format(i)
                result = connect_DB(ref.db_info,'TowerBase_WEB',sql,'select',1)[0]
                # 判斷是否下雨(下雨沒太陽)
                if result > 0:
                    dict01[i] = random.choice([0,-1,0,-1,0,0])
                else:
                    dict01[i] = random.choice([1,0,1,0,1,2,3])
            else:
                dict01[i] = random.choice([0,-1,0,-1,0,0])
        else :  #表示閘道器有回傳資料
            # 若有資料的塔號超過一個,以random後順訊拉值
            if len(alive_node) > 1:
                alive_node = list(alive_node)
                random.shuffle(alive_node)
            # 拉取上一小時time
            for a in alive_node:
                last_power = get_last_power(time,a[0])
                if last_power not in [-1,None]:
                    dict01[i] = dict01[a[0]] - last_power
                    if  dict01[i] > 3 :
                        dict01[i] =  random.randint(0,3)
                    elif dict01[i] < -2 :
                        dict01[i] = random.randint(-2,0)
                    break
                else :
                    dict01[i] = 0
    for i in nodedata:
        if i[0] not in [b[0] for b in alive_node]:
            i[3] += dict01[i[0]]
            # random的資料將上去若小於30或是大於99以31和98計
            if i[3] < 30 :
                i[3] = 31
            elif i[3] > 99 :
                i[3] = 98
    return nodedata

        
def cal_NI(list_power,stamp,time,towerid):
    '''
    計算電量
    random RSSI
    random 封包傳送率(PAR)
    TODO: 接收RSSI 封包傳送率資料
    TODO: power 若電量為-1或none或小於0則random
    '''
    
    if stamp == 'day':
        list_RSSI = []
        power = list_power[0][0]
        for i in list_power :
            list_RSSI.append(i[1])
        RSSI = int(sum(list_RSSI)/len(list_RSSI))
    else :
        power = list_power[-1]
        if power not in [-1,None]:
            power = int((power-10.65)*100/(13.07-10.65))
            if power <= 0 or power >= 100:
                power = get_last_power(time,towerid) # TODO
        else :
            power = get_last_power(time,towerid) #TODO 
        RSSI = random.randint(-97,-70)
    PAR = 100
    return RSSI,power,PAR


def weather(time,stamp,tower_list,WSWD,RF,NI):
    '''
    '''
    wswd,rainfall,nodedata,alive,dead = [],[],[],[],[]
    # 遍歷所有電塔
    for i in tower_list:
        try:
            # 拉取風速風向雨量資料
            list_ws1,list_ws2,list_rf,list_power,last_list_rf,wd1,wd2,maxWS,edtime = chart_weather(ref.weather,i['tbname'],time,stamp,ref.web,i['TowerID'])

            #  確認哪些閘道器是死掉的並更新資料庫
            if (list_ws1 != -1) and (list_ws2 != -1) and (list_power != -1) and (None not in list_power) :
                alive.append(i['TowerID'])
            else :
                dead.append(i['TowerID'])
            
            if RF != '0':
                #計算雨量
                rf = cal_rf(list_rf,last_list_rf,time,RF,i['TowerID'],stamp)
                rainfall.append([i['TowerID'],i['RouteID'],rf,edtime])

            # 計算風速風向
            ws1,ws2,wd1,wd2=cal_wswd(list_ws1,list_ws2,wd1,wd2,i['wd1_deflection'],i['wd2_deflection'],stamp)
            wswd.append([i['TowerID'],i['RouteID'],ws1,ws2,wd1,wd2,maxWS,edtime])
            
            # 計算電量
            if NI != '0' :
                RSSI,power,PAR = cal_NI(list_power,stamp,time,i['TowerID'])
                nodedata.append([i['TowerID'],i['RouteID'],RSSI,power,PAR,edtime])
        
        except Exception as e:
            go_to_log(ref.log_path,'{}:{}'.format(i['TowerID'],e))
    
    # 上傳閘道器狀態
    update_gatway_status(alive,dead)

    if RF != '0':
        # check -1 data ,catch cwb and acc data replace
        rainfall = check_err_data(time,'rainfall',rainfall,stamp)
        # insert rainfall
        post_rf(ref.web,RF,rainfall)
    if NI != '0':
        if stamp == 'hour':
            nodedata = NI_deflection(time,dead,alive,nodedata)
        post_NI(ref.web,NI,nodedata)

    # check -1 data ,catch cwb and acc data replace
    wswd = check_err_data(time,'wswd',wswd,stamp)
    # insert wswd
    post_wswd(ref.web,WSWD,wswd)


#####################################################################
#                              Home                          by 瑞昌 #
#####################################################################

def cal_gust_speed(data):
    '''
    計算陣風級數\n
    data:風速,單位 m/s\n
    型態:float\n
    '''
    if data < 0 :
        return 0
    else :
        gust_speed_list = [[0,0.3],[0.3,1.6],[1.6,3.4],[3.4,5.5],[5.5,8.0],[8.0,10.8],[10.8,13.9],[13.9,17.2],[17.2,20.8],[20.8,24.5],[24.5,28.5],[28.5,32.7],[32.7,37.0],[37.0,41.5],[41.5,46.2],[46.2,51.0],[51.0,56.1],[56.1,61.2]]
        for i in range(len(gust_speed_list)):
            if gust_speed_list[i][0] <= data < gust_speed_list[i][1]:
                return i
        # 若不在上述範圍代表超過17級風,目前對於超過17級風沒有明確定義,所以統一歸類18級風
        return 18


def cal_maxWS(data):
    '''
    計算最大風速
    '''
    data_list = []
    for i in data:
        data_list.append(i[0])
        data_list.append(i[1])
    return max(data_list)


def cal_sum_rf(data):
    '''
    計算各個分級的累積雨量\n
    return 小時累積,三小時累積,日累積,月累積\n 
    '''
    data_list = []
    for i in data:
        data_list.append(i[0])
    return round(sum(data_list),2)


def get_nodeinfo(dbname,tbname,sttime,edtime,towerid,*args):
    '''
    拉取電量和訊號強度\n
    '''
    sql = "SELECT residual_power,RSSI FROM {} WHERE TowerID = {} AND (time BETWEEN '{}' AND '{}') AND residual_power != -1 AND RSSI != -1 ORDER BY time DESC".format(tbname,towerid,sttime,edtime)
    result = connect_DB(ref.db_info,dbname,sql,'select',0)
    return result


def post_home(dbname,tbname,data):
    '''
    insert to Home 
    '''
    sql = "INSERT INTO {}(TowerID,RouteID,WS,gust_peak_speed,mini_WS,WD,Rainfall_per_hour,Rainfall_per_3hour,Rainfall_per_day,Rainfall_per_30day,Displacement,GWL,RSSI,residual_power,time) VALUES ".format(tbname)
    for i in data:
        sql_body = "({},{},{},{},{},{},{},{},{},{},{},{},{},{},'{}'),".format(i[0],i[1],i[2],i[3],i[4],i[5],i[6],i[7],i[8],i[9],i[10],i[11],i[12],i[13],i[14])
        sql += sql_body
    sql = sql[:-1]
    connect_DB(ref.db_info,dbname,sql,'insert',0)


def alert_rating(data,type):
    '''
    警報程式分級
    1:green 2:yellow 3:orange 4:red
    WS:
    43-49:2, 49-54:3, 54up:4
    RAIN:
    70-85/3hr:2, 85-100/3hr:3, 100/3hr up:4  
    140-170/day:2, 170-200/day:3, 200/day up:4
    560-680/M:2, 680-800/M:3, 800/M up:4
    displacement:
    2-10/M:2, 10/M up:3
    5/day:4
    '''
    # 1:green 2:yellow 3:orange 4:red  #[[],[],[]]
    result = 4
    if type == "WS_W":
        datarange = [[0,34],[34,39],[39,44]]
    elif type == "WS_E":
        datarange = [[0,46],[46,50],[50,54]]
    elif type == "rain_3hr":
        datarange = [[0,65],[65,100],[100,200]]
    elif type == "rain_day":
        datarange = [[0,130],[130,200],[200,350]]
    elif type == "rain_month":
        datarange = [[0,520],[520,800],[800,1400]]
    elif type == "displacement_month":
        datarange = [[0,2],[2,10],[10,15]]
    elif type == "displacement_day":
        datarange = [[0,5]]
    elif type == "power":
        # result = 1
        datarange = [[30,100],[20,30],[10,20]]

    for i in range(len(datarange)):
        if datarange[i][0] <= data < datarange[i][1]:
            result = i +1
    return result


def warning_light(route_id,tower_id,WS,rain_3hr,rain_day,rain_month,displacement_month,displacement_day,power):
    '''
    警報程式
    '''
    # 確認塔位於台灣東部還是西部
    sql_WS = "SELECT `EorW` FROM `RouteInfo` WHERE `routeID` = {}".format(route_id)
    result = connect_DB(ref.db_info,'TowerBase_Gridwell',sql_WS,'select',1)
    
    WS_result = alert_rating(WS,'WS_'+result[0])
    rain_3hr_result = alert_rating(rain_3hr,'rain_3hr')
    rain_day_result = alert_rating(rain_day,'rain_day')
    rain_month_result = alert_rating(rain_month,'rain_month')
    Rainfall_result = max(rain_3hr_result,rain_day_result,rain_month_result)
    displacement_month_result = alert_rating(displacement_month,'displacement_month')
    displacement_day_result = alert_rating(displacement_day,'displacement_day')
    Displacement_result = max(displacement_month_result,displacement_day_result)
    power_result = alert_rating(power,'power')
    sql_light = "UPDATE Relation SET wind_status={},rainfall_status={},displacement_status={},power_status={} WHERE tower_id = {}".format(WS_result,Rainfall_result,Displacement_result,power_result,tower_id)
    connect_DB(ref.db_info,'TowerBase_Gridwell',sql_light,'update',1)


def Home(time,stamp,tower_list,WSWD,RF,NI):
    '''
    '''
    home = []
    # 確認哪些塔號是手動關閉風速風向的
    sql = "SELECT tower_id FROM `Relation` WHERE node_life = 0 "
    random_list = connect_DB(ref.db_info,'TowerBase_Gridwell',sql,'select',0)
    random_list = [i[0] for i in random_list]

    for i in tower_list:
        edtime = (time + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:00")
        sttime = (time - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:00")
        # 拉取風速風向資料
        result = get_wswd(ref.web,'chart_WSWD_avg10min',sttime,edtime,i['TowerID'])
        WS = result[0][0]
        if WS == 0:
             WS = result[0][1]
        WD = result[0][2]
        if WD == 0:
            WD = result[0][3]
        # 計算陣風級數
        gust_speed = cal_gust_speed(WS)
        # 拉取風速計raw data
        max_WS = result[0][4]
        # result = get_weather(ref.weather,i['tbname'],sttime,edtime)
        # # 計算最大風速
        # if len(result) == 0 or i['TowerID'] in random_list :
        #     max_WS = round(WS + random.uniform(0.5,1),2)
        # else :
        #     max_WS = cal_maxWS(result)

        # 拉取雨量資料
        edtime = time.strftime("%Y-%m-%d %H:00:00")
        sttime = time.strftime("%Y-%m-%d 00:00:00")
        result = get_rf(ref.web,'chart_Rainfall_avghour',sttime,edtime,i['TowerID'])
        # 時積雨量
        hour_rf = result[0][0]
        # 三小時積雨量
        if len(result) > 2:
            three_hour_rf = result[0][0] + result[1][0] + result[2][0]
        elif len(result) > 1:
            three_hour_rf = result[0][0] + result[1][0]
        else:
            three_hour_rf = result[0][0]
        # 日積雨量
        day_rf = cal_sum_rf(result)
        # 月積雨量
        sttime = time.strftime("%Y-%m-01 00:00:00")
        result = get_rf(ref.web,'chart_Rainfall_avghour',sttime,edtime,i['TowerID'])
        month_rf = cal_sum_rf(result)
        # 拉取電量與訊號強度,若無值會拉取上一筆(只拉取一次)
        sttime = (time-timedelta(hours=1)).strftime("%Y-%m-%d %H:00:00")
        result = get_nodeinfo(ref.web,'chart_nodeinfo_avghour',sttime,edtime,i['TowerID'])
        if len(result) != 0:
            power = result[0][0]
            RSSI = result[0][1]
        else :
            power = -1
            RSSI = -1
        # 拉取地下水位  TODO
        GWL = 0
        # 拉取地中偏移 TODO
        displacement = 0
        home.append([i['TowerID'],i['RouteID'],WS,gust_speed,max_WS,WD,hour_rf,three_hour_rf,day_rf,month_rf,displacement,GWL,RSSI,power,time.strftime("%Y-%m-%d %H:%M:00")])
        # 警報程式 TODO 地中偏移
        warning_light(i['RouteID'],i['TowerID'],WS,three_hour_rf,day_rf,month_rf,displacement,displacement,power)
    # insert to database (Home)
    post_home(ref.web,WSWD,home)





if __name__ == "__main__":
    # 風速可用小時平均,10分鐘平均...
    # 風向須取整點風向

    time = datetime.now()
    check_newData(time)
    check_miss_data(time)