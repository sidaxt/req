/*
SELECT TOP (1000) [APPLN]
      ,[LOG_DT_TM]
      ,[USR_NM]
      ,[RESP_DT_TM]
      ,[model_name]
      ,[RESP_TM_SEC]
      ,[NO_TOKENS]
  FROM [AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]
*/
  

--SELECT distinct model_name  FROM [AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]


--gpt-35-turbo-16k -- generic qna - query responses

SELECT *-- [model_name]
FROM [AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]
where model_name IN ('gpt-35-turbo-16k') and USR_NM = 'ssirish@dsi.com' and LOG_DT_TM = '2024-05-07'
order by LOG_DT_TM desc


--GPT3.5 -- document upload - query responses

SELECT *-- [model_name]
FROM [AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]
where model_name IN ('GPT3.5') and USR_NM = 'ssirish@dsi.com' and LOG_DT_TM = '2024-05-07'
order by LOG_DT_TM desc


--gpt-3.5 -- csv,xlsx upload - query responses

SELECT *-- [model_name]
FROM [AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]
where model_name IN ('gpt-3.5') and USR_NM = 'ssirish@dsi.com' and LOG_DT_TM = '2024-05-07'
order by LOG_DT_TM desc

