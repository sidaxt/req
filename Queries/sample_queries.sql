SELECT distinct [APPLN],
      [LOG_DT_TM]
      ,[USR_NM]
      ,[RESP_DT_TM]
      ,[model_name]
      ,[RESP_TM_SEC]
      ,[NO_TOKENS]
  FROM [AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]
  where DATEDIFF(day,LOG_DT_TM,GETDATE()) < 31
  --NO_TOKENS is not null
  order by LOG_DT_TM  desc


--Select Datepart(MM,GETDATE())

SELECT * FROM  [AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT] 
WHERE DATEDIFF(day,LOG_DT_TM,GETDATE()) between 0 and 30 


Select DATEDIFF(day,LOG_DT_TM,GETDATE()),LOG_DT_TM
FROM  [AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT] 
WHERE DATEDIFF(day,LOG_DT_TM,GETDATE()) between 0 and 30


Select DATEDIFF(day,LOG_DT_TM,GETDATE()),LOG_DT_TM
FROM  [AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT] 
WHERE DATEDIFF(day,LOG_DT_TM,GETDATE()) < 31

Select DATEDIFF(day,LOG_DT_TM,GETDATE()),LOG_DT_TM
FROM  [AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT] 
WHERE DATEDIFF(day,LOG_DT_TM,GETDATE()) <= 30

Select DATEDIFF(day,LOG_DT_TM,GETDATE()),LOG_DT_TM
FROM  [AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT] 
WHERE CAST(LOG_DT_TM AS DATE) >= GETDATE() - 30


--SELECT LOG_DT_TM FROM [AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT] WHERE DATE(LOG_DT_TM) >= DATE(NOW()) - INTERVAL 30 DAY

Select DATEDIFF(day,LOG_DT_TM,GETDATE()),LOG_DT_TM
FROM  [AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT] 
WHERE DATEDIFF(LOG_DT_TM,GETDATE()) between 0 and 30

SELECT distinct TOP (1000) [APPLN]
      ,[LOG_DT_TM]
      ,[USR_NM]
      ,[RESP_DT_TM]
      ,[model_name]
      ,[RESP_TM_SEC]
      ,[NO_TOKENS]
  FROM [AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]
  where USR_NM like 
  --'%sir%'
'%Notarnicola%' or USR_NM like 
'%Parenti%'or USR_NM like 
'%Nosti%'or USR_NM like 
'%Paradiso%'or USR_NM like 
'%Menniti%'or USR_NM like 
'%Julien%'or USR_NM like 
'%Engel%'or USR_NM like 
'%Gillick%'


  --where USR_NM IN ('joe.paradiso@daiichisankyo.com')
  

  --joe.paradiso@daiichisankyo.com

  --JPARADISO@DSI.COM

