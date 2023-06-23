import json
import pandas as pd

from numpy import array
from sklearn.metrics import mean_squared_error, r2_score
import xgboost as xgb
import datetime
import math
import sys
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

def firebase_initialize():
    cred = credentials.Certificate("appstock-fe44a-f92cf5e7f6b4.json")
    app = firebase_admin.initialize_app(cred)

def firebase_connection():
    db = firestore.client()
    return db

def return_data(id_preparat):
    db = firebase_connection()
    result_data = []
    if db:
        response = db.collection(u'orders-complete').stream()
        if response:
            for data in response:
                result_data.append({u'id': data.id,
                                    u'products': data.to_dict()}) 
    restaurant_dat_x = []
    restaurant_dat_y = []         
    restaurant_dat_predict_x = []
    restaurant_dat_predict_y = []

    if len(result_data) == 0:
        return [], [], [], []

    today = datetime.date.today()
    first = today.replace(day=1)
    lastMonth = first - datetime.timedelta(days=1)

    for row in result_data:
        json_to_string = json.dumps(row['products'])
        data_keys = json.loads(json_to_string)
        for product in data_keys:
            if product == id_preparat:
                if row['id'] < lastMonth.strftime("01-%m-%Y"):
                    restaurant_dat_x.append([1])
                    restaurant_dat_y.append([row['products'][product]])
                else:
                    restaurant_dat_predict_x.append([1])
                    restaurant_dat_predict_y.append([row['products'][product]])

    if len(restaurant_dat_x) == 0:
        restaurant_dat_x.append([1])

    if len(restaurant_dat_y) == 0:
        restaurant_dat_y.append([1])

    restaurant_dat_x = array(restaurant_dat_x)
    restaurant_dat_y = array(restaurant_dat_y)
    restaurant_dat_predict_x = array(restaurant_dat_predict_x)
    restaurant_dat_predict_y = array(restaurant_dat_predict_y)
    return restaurant_dat_x, restaurant_dat_y, restaurant_dat_predict_x, restaurant_dat_predict_y


def init(restaurant_x_train, restaurant_y_train):

    regressor = xgb.XGBRegressor()
   
    regressor.fit(restaurant_x_train, restaurant_y_train)
    return regressor


def xgboost_regression(id_preparat):
  
    restaurant_dat_x, restaurant_dat_y, restaurant_dat_predict_x, restaurant_dat_predict_y = return_data(id_preparat)

    if len(restaurant_dat_predict_x) != 0 and len(restaurant_dat_predict_y) != 0:
       
        regressor = init(restaurant_dat_x, restaurant_dat_y)

        restaurant_y_pred = regressor.predict(restaurant_dat_predict_x)

        arithmetic_average = 0
        for quantity in restaurant_y_pred[:31]:
            arithmetic_average += quantity
        arithmetic_average /= len(restaurant_y_pred[:31])
        arithmetic_average += mean_squared_error(restaurant_dat_predict_y, restaurant_y_pred)
        db = firebase_connection()
        result_data = []
        response = db.collection(u'stock-prediction').stream()
        if response:
            for data in response:
                result_data.append({u'id': data.id, u'products': data.to_dict()})

        if len(result_data) > 0:
            result_data = list(filter(
                lambda x: x['id'] == datetime.date.today().strftime("%m-%d-%Y") and id_preparat in json.loads(
                    json.dumps(x['products'])), result_data))

        if len(result_data) == 0:
            response = db.collection(u'stock-prediction').document(datetime.date.today().strftime("%m-%d-%Y")).set({
                id_preparat: math.ceil(arithmetic_average)
            }, merge=True)

            if response:
                print(1)
            else:
                print(-1)
        else:
            print(2)

    else:
        print(0)


if __name__ == '__main__':
    firebase_initialize()
    db = firebase_connection()
    result_data = []
    data = db.collection(u'products').stream()
    for product in data:

        xgboost_regression(product.id)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
