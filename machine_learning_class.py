#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import warnings
warnings.filterwarnings('ignore')
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import OneHotEncoder
from imblearn.over_sampling import RandomOverSampler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
import pickle

df_flight = pd.read_csv("kaggle_flights_clean.csv")
df_weather = pd.read_csv("weather_data.csv")

print(df_flight.head())
print(df_weather.head())


# In[ ]:


#Displaying info
print(df_flight.info(),"\n\n")
print(df_weather.info())

#Remove the column ingested_at that was inserted along the data with SQLAlchemy
df_weather.pop("ingested_at")


# In[ ]:


#Remove cancelled flights and drop all unnecessary columns
df_flight = df_flight.loc[df_flight["cancelled"] == False]
df_flight = df_flight.drop(["operating_airline",
                         "tail_number",
                         "flight_number_operating_airline",
                         "originairportid",
                         "destairportid",
                         "wheelsoff",
                         "wheelson",
                         "cancellationcode",
                         "carrierdelay",
                         "weatherdelay",
                         "nasdelay",
                         "securitydelay",
                         "lateaircraftdelay",
                         "cancelled",
                         "cancellationcode",
                         "taxiout",
                         "taxiin",
                         "depdelay",
                         "departuredelaygroups",
                         "crselapsedtime",
                         "actualelapsedtime",
                         "airtime",
                         "arrtime",
                         "arrdel15",
                         "arrdelay",
                         "arrivaldelaygroups",
                         "crsdeptime", "deptime", "crsarrtime", "arrtime"
                         ], axis = 1)
print(df_flight.info())


# In[ ]:


#df_weather.info()
print(df_weather.info())

#columns which will be filled with mean data
mean_col = ["temp","temp_min_c","temp_max_c","relative_humidity","precipitation_mm","wind_speed_kmh","pressure_hpa","cloud_cover"]

#Fill in empty snow data with a 0 assuming that there is no snow if its empty.
df_weather["snow_mm"] = df_weather["snow_mm"].fillna(0)
for col in mean_col:
    df_weather[col] = df_weather[col].fillna(df_weather[col].mean())
print(df_weather.isna().sum())
print(df_weather.info())


# In[ ]:


#Merge our df_flight dataframe with our df_weather dataframe based on date and origin
df_merge = pd.merge(df_flight, df_weather, left_on=["flightdate", "origincityname"], right_on = ["weather_date","location_name"], how="inner")
print(df_merge.info())


# In[ ]:


#drop unnecessary columns and renaming columns to identify them as origin weather data
df_merge = df_merge.drop(["weather_id", "station_id", "location_name", "weather_date"], axis = 1)
df_merge = df_merge.rename(columns={
    "temp":  "temp_o",
    "temp_min_c":  "temp_min_c_o",
    "temp_max_c":  "temp_max_c_o",
    "relative_humidity":  "relative_humidity_o",
    "precipitation_mm":  "precipitation_mm_o",
    "snow_mm":  "snow_mm_o",
    "wind_speed_kmh":  "wind_speed_kmh_o",
    "pressure_hpa":  "pressure_hpa_o",
    "cloud_cover":  "cloud_cover_o"

})

df_merge.info()


# In[ ]:


#Merge our df_merge dataframe with our df_weather dataframe based on date and destination
df_merge = pd.merge(df_merge, df_weather, left_on=["flightdate", "destcityname"], right_on = ["weather_date","location_name"], how="inner")
print(df_merge.info())


# In[ ]:


#drop unnecessary columns and renaming columns to identify them as destination weather data
df_merge = df_merge.drop(["weather_id", "station_id", "location_name", "weather_date"], axis = 1)
df_merge = df_merge.rename(columns={
    "temp":  "temp_d",
    "temp_min_c":  "temp_min_c_d",
    "temp_max_c":  "temp_max_c_d",
    "relative_humidity":  "relative_humidity_d",
    "precipitation_mm":  "precipitation_mm_d",
    "snow_mm":  "snow_mm_d",
    "wind_speed_kmh":  "wind_speed_kmh_d",
    "pressure_hpa":  "pressure_hpa_d",
    "cloud_cover":  "cloud_cover_d"

})


# In[ ]:


#dropping our now obsolete cityname columns and making sure we dont have any leftover nan left.
df_merge = df_merge.drop(["origincityname",
                         "destcityname"
                         ], axis = 1)

df_merge = df_merge.dropna()


df_merge.info()


# In[ ]:


#OBSOLETE ONCE depdel15 IS ALREADY SET AS A BOOLEAN
df_merge["depdel15"] = df_merge["depdel15"].astype(bool)
df_merge.info()


# In[ ]:


#leaving this code in if we decide to use time columns again. For now I just drop the date column

'''
#split date time columns to year month day hour minute
def get_day(date):
    return date.split("-")[2]

def get_month(date):
    return date.split("-")[1]

def get_year(date):
    return date.split("-")[0]

def get_hour(date):
    return date.split("-")[0]

def get_minute(date):
    return date.split("-")[1]

#df_merge["year"] = df_merge["flightdate"].apply(get_year)
#df_merge["month"] = df_merge["flightdate"].apply(get_month)
#df_merge["day"] = df_merge["flightdate"].apply(get_day)

df_merge["crsdeptime"] = pd.to_datetime(df_merge["crsdeptime"])
df_merge["deptime"] = pd.to_datetime(df_merge["deptime"])
df_merge["crsarrtime"] = pd.to_datetime(df_merge["crsarrtime"])
df_merge["arrtime"] = pd.to_datetime(df_merge["arrtime"])
'''
df_merge = df_merge.drop(["flightdate"], axis = 1)
df_merge.info()


# In[ ]:


#split up our columns between our target column and the rest.
feats = df_merge.drop("depdel15", axis = 1)

target = df_merge["depdel15"]


# In[ ]:


#notice that our target data is heavily biased.
target.value_counts(normalize=True)


# In[ ]:


#split between train and test set with the test size being 25%
X_train, X_test, y_train, y_test = train_test_split(feats, target, test_size=0.25)

print(X_train.isna().sum(), X_test.isna().sum())


# In[ ]:


#Process our numeric columns with StandardScaler
scaler = StandardScaler()
num = ["distance",
      "distancegroup",
      "temp_o",
      "temp_min_c_o",
      "temp_max_c_o",
      "relative_humidity_o",
      "precipitation_mm_o",
      "snow_mm_o",
      "wind_speed_kmh_o",
      "pressure_hpa_o",
      "cloud_cover_o",
      "temp_d",
      "temp_min_c_d",
      "temp_max_c_d",
      "relative_humidity_d",
      "precipitation_mm_d",
      "snow_mm_d",
      "wind_speed_kmh_d",
      "pressure_hpa_d",
      "cloud_cover_d"]


X_train[num] = scaler.fit_transform(X_train[num])
X_test[num] = scaler.transform(X_test[num])


# In[ ]:


#Replace our boolean with 0 and 1
def replace_true_false(x):
    if x == False:
        return 0
    if x == True:
        return 1

boo = ["diverted"]

y_train = y_train.apply(replace_true_false)
y_test = y_test.apply(replace_true_false)

for col in boo:
    X_train[col] = X_train[col].apply(replace_true_false)

for col in boo:
    X_test[col] = X_test[col].apply(replace_true_false)


# In[ ]:


#OneHotEncoder for Origin and Destination
ohe = OneHotEncoder(sparse_output=False)
ohe_col = ["origin", "dest"]

#create new dataframes for our OneHotEncoder
ohe_train = ohe.fit_transform(X_train[ohe_col])
ohe_test = ohe.transform(X_test[ohe_col])


# In[ ]:


#Merge our training data with our new ohe dataframes and insert it into their own columns with a fitting name.
X_train = pd.concat(
    [
        X_train,
        pd.DataFrame(ohe_train, index=X_train.index, columns=ohe.get_feature_names_out()),
    ],
    axis="columns",
)
#Merge our test data with our new ohe dataframes and insert it into their own columns with a fitting name.
X_test = pd.concat(
    [
        X_test,
        pd.DataFrame(ohe_test, index=X_test.index, columns=ohe.get_feature_names_out()),
    ],
    axis="columns",
)


# In[ ]:


print(X_train[X_train["dest_ABE"]==1])

X_train.isna().sum()


# In[ ]:


#drop our origin and destination columns now that they are encoded.
X_train = X_train.drop(ohe_col, axis=1)
X_test = X_test.drop(ohe_col, axis=1)


# In[ ]:


#LogisticRegression with our raw data. Test on my local machine ~24 seconds
model = LogisticRegression()

model.fit(X_train, y_train)

print(model.score(X_train, y_train))

print(model.score(X_test, y_test))



# In[ ]:


#prediction
prediction = model.predict(X_test)
print(classification_report(y_test, prediction))

#display the confusion matrix
print(confusion_matrix(y_test, prediction))


# In[ ]:


#oversample our data so our target data isnt heavily biased.
rOs = RandomOverSampler()
X_ro, y_ro = rOs.fit_resample(X_train, y_train)
print('Oversampled sample classes :', dict(pd.Series(y_ro).value_counts(normalize = True)))


# In[ ]:


#LogisticRegression with our oversampled data. Test on my local machine ~38 seconds
model_over = LogisticRegression()
model_over.fit(X_ro, y_ro)

print(model_over.score(X_ro, y_ro))
print(model_over.score(X_test, y_test))



# In[ ]:


#prediction
prediction = model_over.predict(X_test)
print(classification_report(y_test, prediction))

#display the confusion matrix
print(confusion_matrix(y_test, prediction))


# In[ ]:


with open("flight_delay_model_bundle.pkl", "wb") as f:
    pickle.dump({
        "model": model,
        "scaler": scaler,
        "ohe": ohe,
        "num_cols": num,
        "ohe_cols": ohe_col,
        "feature_columns": X_train.columns.tolist()
    }, f)


# In[ ]:


# Here I load the logistic regression model into model_2 to test it out
with open("logistic_regression.pkl", "rb") as f:
    model_2 = pickle.load(f)


#prediction
prediction_2 = model_2.predict(X_test)
print(classification_report(y_test, prediction_2))

#display the confusion matrix
print(confusion_matrix(y_test, prediction_2))


# In[ ]:


# I left the RandomForest models in but for now I just commented them out.
'''
#RandomForest with our raw data. Test on my local machine ~6minutes and 44 seconds
rf = RandomForestClassifier()
rf.fit(X_train, y_train)

print('Score on the train set', rf.score(X_train, y_train))
print('Score on the train set', rf.score(X_test, y_test))
'''


# In[ ]:


'''
y_pred = rf.predict(X_test)

print(pd.crosstab(y_test,y_pred))
print(classification_report(y_test, y_pred))
'''


# In[ ]:


'''
#RandomForest with our oversampled data. Test on my local machine ~10 minutes and 13 seconds
rf = RandomForestClassifier()
rf.fit(X_ro, y_ro)

print('Score on train set', rf.score(X_ro, y_ro))
print('Score on test set', rf.score(X_test, y_test))

from sklearn.metrics import classification_report

y_pred = rf.predict(X_test)


print(pd.crosstab(y_test,y_pred))
print(classification_report(y_test, y_pred))
'''

