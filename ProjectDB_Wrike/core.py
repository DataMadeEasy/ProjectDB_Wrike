import credentials
import json, psycopg2
import urllib2
import os
import requests
import time
import logging
from time import localtime, strftime





#Wrike API Information
wrike_url = credentials.WrikeCredentials['wrike_url']
wrike_clientId = credentials.WrikeCredentials['wrike_clientId']
wrike_clientSecret = credentials.WrikeCredentials['wrike_clientSecret']


logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()
logger.addHandler(logging.FileHandler('wrike-log.log', 'a'))
#print logger.info








def wrike_clearDatabase(dbconnection):


    cursor = dbconnection.cursor()
    
    query =  "TRUNCATE TABLE tasks, comments, tasks_hier,tasks_assignment;"
    cursor.execute(query)
    
    

    
    dbconnection.commit()
    
    

def wrike_loadfolders(dbconnection):

    #Get data from Folders API
    headers = {'Authorization': 'bearer ' + credentials.WrikeCredentials['wrike_bearertoken']}
    response = requests.get('https://www.wrike.com/api/v3/folders/', headers=headers)
    
    
    #Convert response to json object
    jsonFolders =response.json()
    
    #print statements
    #print response.text
    

    
    #loop through Request and pull information about folders
    for folders in jsonFolders["data"]:
        strID = folders['id'] 
        strTitle = folders['title']

        
        cursor = dbconnection.cursor()
        query =  "INSERT INTO tasks (id, title) VALUES (%s, %s);"
        data = (strID, strTitle)
        cursor.execute(query, data)
        
        i = 0
        for child in folders["childIds"]:
            
            strChildID = folders["childIds"][i]
            query =  "INSERT INTO tasks_hier (parent_id, child_id) VALUES (%s, %s);"
            data = (strID, strChildID)
            cursor.execute(query, data)
            i = i+1
            
        
        

    dbconnection.commit()
           


def wrike_gettasks(dbconnection):
    
    headers = {'Authorization': 'bearer ' + credentials.WrikeCredentials['wrike_bearertoken']}
    response = []
    intResponse = 0
    
    response.append(requests.get('https://www.wrike.com/api/v3/tasks?pageSize=1000&fields=["sharedIds","briefDescription","responsibleIds","attachmentCount","dependencyIds","recurrent","authorIds","hasAttachments","parentIds","subTaskIds","superParentIds","metadata","customFields","description","superTaskIds"]', headers=headers))
    
    
    #print response[1].text
    #wrike_loadtasks(dbconnection,response[0])
    
    jsonResponse = response[0].json()
    
    while 'nextPageToken' in jsonResponse:
        
        strNextPageToken = jsonResponse['nextPageToken']
        #print strNextPageToken
        
        response.append(requests.get('https://www.wrike.com/api/v3/tasks?pageSize=1000&nextPageToken=' + strNextPageToken + '&fields=["sharedIds","briefDescription","responsibleIds","attachmentCount","dependencyIds","recurrent","authorIds","hasAttachments","parentIds","subTaskIds","superParentIds","metadata","customFields","description","superTaskIds"]', headers=headers))
        
        intResponse = intResponse +1
        
        jsonResponse = response[intResponse].json() 
    
    
    for x in response:
        
        wrike_loadtasks(dbconnection, x)
        
    print "Done"
    
    
def wrike_loadtasks(dbconnection, response):

     
    #Convert response to json object
    jsonTasks =response.json()
    

    
    #loop through Request and pull information about folders
    for task in jsonTasks["data"]:
        
        #Get Task information
        strID = task['id'] 
        strTitle = task['title']
        strStatus = task['status']
        strImportance = task['importance']
        strCreatedDate = task['createdDate']
        strUpdatedDate = task['updatedDate']
        strCompletedDate = None
        strCustomStatusID = task['customStatusId']
        strPermalink  = task['permalink']
        strPriority = task['priority']
        
        if 'superTaskIds' in task:
            listSuperTaskIDs = task['superTaskIds']
        if 'description' in task:
            strDescription = task['description']
        
        listDates = task['dates']
        strPlannedStart = None
        strPlannedDue = None
        strPlannedDuration = None
        strObjectType = None
        strTaskNotes = None
        strIssue = None
        boolProjLevel = False
        
        #Get Custom Field Information
        if 'customFields' in task:
            listCustomFields = task['customFields']
            strObjectType = ""
            strTaskNotes = None
            strIssue = None
            boolProjLevel = False

            for dictCustomFields in listCustomFields:
                if dictCustomFields['id']== 'IEABXVKXJUAATWIB':
                    strObjectType = dictCustomFields['value']
                elif dictCustomFields['id']== 'IEABXVKXJUAAZBPY':
                    strTaskNotes = dictCustomFields['value']
                elif dictCustomFields['id']== 'IEABXVKXJUAAZIR6':
                    strIssue = dictCustomFields['value']
                elif dictCustomFields['id']== 'IEABXVKXJUAASPHH':
                    boolProjLevel = dictCustomFields['value']
        
        
        if 'completedDate' in task:
            strCompletedDate = task['completedDate']
        
        #Get Date Information
        if listDates['type'] == 'Planned':
            strPlannedStart = listDates['start']
            strPlannedDue = listDates['due']
            if 'duration' in listDates:
                strPlannedDuration = listDates['duration']
             
        
        cursor = dbconnection.cursor()
        query =  "INSERT INTO tasks (id, title, status, importance, created_date, updated_date, completed_date, custom_status_id, permalink,priority,planned_start, planned_due, planned_duration, description, object_type,task_notes,issue,project_reporting) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s,%s,%s,%s,%s);"
        data = (strID, strTitle, strStatus,strImportance,strCreatedDate,strUpdatedDate, strCompletedDate, strCustomStatusID,strPermalink,strPriority, strPlannedStart, strPlannedDue, strPlannedDuration, strDescription, strObjectType, strTaskNotes,strIssue, boolProjLevel)
        cursor.execute(query, data)
        dbconnection.commit()
        
        i = 0
        if not listSuperTaskIDs:
            
            for parent in task["parentIds"]:          
                strParentID = task["parentIds"][i]
                cursor = dbconnection.cursor()
                query =  "INSERT INTO tasks_hier (parent_id, child_id) VALUES (%s, %s);"
                data = (strParentID, strID)
                cursor.execute(query, data)
                dbconnection.commit()
                i = i+1
        else:
            for supertask in task["superTaskIds"]:          
                strParentID = task["superTaskIds"][i]
                cursor = dbconnection.cursor()
                query =  "INSERT INTO tasks_hier (parent_id, child_id) VALUES (%s, %s);"
                data = (strParentID, strID)
                cursor.execute(query, data)
                dbconnection.commit()
                i = i+1
        
        #Get Assignee infor
        listAssignee = task['responsibleIds']
        for strAssignee in listAssignee: 
            query =  "INSERT INTO tasks_assignment (task_id,user_id) VALUES (%s, %s);"
            data = (strID,strAssignee)
            cursor.execute(query,data)
            
      

    dbconnection.commit()
    #print 'tasks committed'


def wrike_loadcomments(dbconnection):

    headers = {'Authorization': 'bearer ' + credentials.WrikeCredentials['wrike_bearertoken']}
    response = requests.get('https://www.wrike.com/api/v3/comments?plainText=true', headers=headers)
        
    #Convert response to json object
    jsonTasks =response.json()
    
    #print statements 
    #print response.text

    

    
    #loop through Request and pull information about folders
    for comment in jsonTasks["data"]:
        strCommentID = comment['id'] 
        strText = comment['text']
        strCreatedDate = comment['createdDate']
        strUpdatedDate = comment['updatedDate']
        strTaskID = comment['taskId']
        strAuthorId = comment['authorId']
        
        cursor = dbconnection.cursor()
        query =  "INSERT INTO comments (comment_id, author_id, comment, updated_date, created_date, task_id) VALUES (%s, %s, %s, %s, %s, %s);"
        data = (strCommentID, strAuthorId, strText,strUpdatedDate, strCreatedDate, strTaskID)
        cursor.execute(query, data)
        
       
    dbconnection.commit()
    #print 'comments committed'
