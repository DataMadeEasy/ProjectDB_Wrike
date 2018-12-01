'''
Created on Dec 1, 2018

@author: tlrausch33
'''
import credentials
from core import wrike_loadfolders, wrike_clearDatabase, wrike_loadtasks, wrike_loadcomments, wrike_gettasks
import time, datetime
import psycopg2



try:
    dbconnection = psycopg2.connect( host=credentials.AWSDbCredentials['hostname'], user=credentials.AWSDbCredentials['username'], password=credentials.AWSDbCredentials['password'], dbname=credentials.AWSDbCredentials['database'], connect_timeout=1 )
    print "Connected to DB"

except:
    print "Unable to connect to db"
    print credentials.AWSDbCredentials['hostname'] + credentials.AWSDbCredentials['username']+ credentials.AWSDbCredentials['password'] + credentials.AWSDbCredentials['database']



wrike_clearDatabase(dbconnection)
print time.strftime("%m/%d/%Y %H:%M:%S")+ ' Wrike Database Cleared'

wrike_loadfolders(dbconnection)
print time.strftime("%m/%d/%Y %H:%M:%S")+ ' Wrike Folders Loaded'

wrike_gettasks(dbconnection)
print time.strftime("%m/%d/%Y %H:%M:%S")+ ' Wrike Tasks Loaded'

wrike_loadcomments(dbconnection)
print time.strftime("%m/%d/%Y %H:%M:%S")+ ' Wrike Comments Loaded'

dbconnection.close()
print time.strftime("%m/%d/%Y %H:%M:%S")+ ' Wrike Process Complete'
