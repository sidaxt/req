/*
SELECT distinct --[APPLN],
    [LOG_DT_TM]
    ,[USR_NM]
    --,[RESP_DT_TM]
    ,[model_name]
    --,[RESP_TM_SEC]
    ,[NO_TOKENS]
	,EMP_FRST_NM ,EMP_LST_NM , EMP_BUS_EMAIL_ID ,SUPV_FRST_NM ,SUPV_LST_NM ,Functional_Area ,EMP_POSN_TITL ,case when SLS_FORC_CD is not null then 1 else 0 end field 
FROM [AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]
inner join COMM_EDS.ids.ROSTER_MASTER rm on USR_NM = EMP_BUS_EMAIL_ID
--where DATEDIFF(day,LOG_DT_TM,GETDATE()) < 31
where 
LOG_DT_TM >= '2024-05-06'
--CONVERT(date,getdate())
AND USR_NM NOT IN ('rbhardwaj@dsi.com','mparag@dsi.com','akurapa@dsi.com','rmanhas@dsi.com','ssirish@dsi.com','nojha@dsi.com','srathore@dsi.com','bimanipuzha@dsi.com','sbaliyan@dsi.com',
'amalledevar@dsi.com','susaini@dsi.com')
--NO_TOKENS is not null
order by LOG_DT_TM  desc
*/



SELECT distinct --[APPLN],
    [LOG_DT_TM] AS Login_Date
    ,[USR_NM] AS User_Email
    --,[RESP_DT_TM]
    ,
	[model_name]
    --,[RESP_TM_SEC]
    --,[NO_TOKENS]
	,SUM(NO_TOKENS) AS Tokens_Utilized
	,CASE WHEN model_name = 'gpt-35-turbo-16k' THEN 'Generic Query Response'
		  WHEN model_name = 'gpt-3.5' THEN 'File Upload - CSV, XSLX'
		  WHEN model_name = 'GPT3.5' THEN 'File Upload - PPTX, DOCX, TXT, PDF'
		  --WHEN model_name = 'text-embedding-ada-002' THEN 'File Upload - Only Embeddings'
	 END AS Query_Responses
	 ,EMP_FRST_NM ,EMP_LST_NM , EMP_BUS_EMAIL_ID ,SUPV_FRST_NM ,SUPV_LST_NM ,Functional_Area ,EMP_POSN_TITL ,case when SLS_FORC_CD is not null then 1 else 0 end field 
FROM [AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]
inner join COMM_EDS.ids.ROSTER_MASTER rm on USR_NM = EMP_BUS_EMAIL_ID
--where DATEDIFF(day,LOG_DT_TM,GETDATE()) < 31
where 
LOG_DT_TM >= '2024-06-03'
--CONVERT(date,getdate())
AND USR_NM NOT IN ('rbhardwaj@dsi.com','mparag@dsi.com','akurapa@dsi.com','rmanhas@dsi.com','ssirish@dsi.com','nojha@dsi.com','srathore@dsi.com','bimanipuzha@dsi.com','sbaliyan@dsi.com',
'amalledevar@dsi.com','susaini@dsi.com','adeorukhkar@dsi.com')
--AND model_name IN ('gpt-35-turbo-16k','gpt-3.5','GPT3.5')
--= 'gpt-35-turbo-16k'
--NO_TOKENS is not null
Group by [LOG_DT_TM]
    ,[USR_NM]
    --,[RESP_DT_TM]
    ,
	[model_name]
    --,[RESP_TM_SEC]
    --,[NO_TOKENS]
	,EMP_FRST_NM ,EMP_LST_NM , EMP_BUS_EMAIL_ID ,SUPV_FRST_NM ,SUPV_LST_NM ,Functional_Area ,EMP_POSN_TITL ,SLS_FORC_CD
order by LOG_DT_TM  desc



/*
--model_name			--QnA
text-embedding-ada-002	maybe pptx, docx, txt, pdf in vector_store.py -- this if for embeddings
gpt-35-turbo-16k		Generic Queries
gpt-3.5					CSV, XSLX
GPT3.5					PPTX, DOCX, TXT, PDF
*/


/*
SELECT distinct --[APPLN],
    [LOG_DT_TM]
    ,[USR_NM]
    --,[RESP_DT_TM]
    ,
	[model_name]
    --,[RESP_TM_SEC]
    ,[NO_TOKENS]
	,EMP_FRST_NM ,EMP_LST_NM , EMP_BUS_EMAIL_ID ,SUPV_FRST_NM ,SUPV_LST_NM ,Functional_Area ,EMP_POSN_TITL ,case when SLS_FORC_CD is not null then 1 else 0 end field 
	--,CASE WHEN model_name = 'gpt-35-turbo-16k' THEN 'Generic Query Response'
	--	  WHEN model_name = 'gpt-3.5' THEN 'File Upload - CSV, XSLX'
	--	  WHEN model_name = 'GPT3.5' THEN 'File Upload - PPTX, DOCX, TXT, PDF'
	-- END AS Query_Responses
FROM [AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]
inner join COMM_EDS.ids.ROSTER_MASTER rm on USR_NM = EMP_BUS_EMAIL_ID
--where DATEDIFF(day,LOG_DT_TM,GETDATE()) < 31
where 
LOG_DT_TM >= '2024-05-06'
--CONVERT(date,getdate())
AND USR_NM NOT IN ('rbhardwaj@dsi.com','mparag@dsi.com','akurapa@dsi.com','rmanhas@dsi.com','ssirish@dsi.com','nojha@dsi.com','srathore@dsi.com','bimanipuzha@dsi.com','sbaliyan@dsi.com',
'amalledevar@dsi.com','susaini@dsi.com')
AND model_name IN ('text-embedding-ada-002','GPT3.5')
--NO_TOKENS is not null
--order by LOG_DT_TM  desc
*/

