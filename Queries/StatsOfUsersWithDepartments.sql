--select EMP_FRST_NM ,EMP_LST_NM , EMP_BUS_EMAIL_ID ,SUPV_FRST_NM ,SUPV_LST_NM ,Functional_Area ,EMP_POSN_TITL ,case when SLS_FORC_CD is not null then 1 else 0 end field 
--from COMM_EDS.ids.ROSTER_MASTER rm where TERM_FLG <>'Y' and emp_typ_flg=1 and Functional_Area like '%corp%'

--Select distinct functional_area from COMM_EDS.ids.ROSTER_MASTER rm where TERM_FLG <>'Y' and emp_typ_flg=1
--and Functional_Area like '%corp%'

/*
SELECT distinct --[APPLN],
    [LOG_DT_TM]
    ,[USR_NM]
    ,[RESP_DT_TM]
    ,[model_name]
    --,[RESP_TM_SEC]
    ,[NO_TOKENS]
	,EMP_FRST_NM ,EMP_LST_NM , EMP_BUS_EMAIL_ID ,SUPV_FRST_NM ,SUPV_LST_NM ,Functional_Area ,EMP_POSN_TITL ,case when SLS_FORC_CD is not null then 1 else 0 end field 
FROM [AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]
inner join COMM_EDS.ids.ROSTER_MASTER rm on USR_NM = EMP_BUS_EMAIL_ID
--where DATEDIFF(day,LOG_DT_TM,GETDATE()) < 31
where 
--DATEDIFF(day,LOG_DT_TM,GETDATE()) < 1 OR 
LOG_DT_TM = CONVERT(date,getdate())
AND USR_NM NOT IN ('rbhardwaj@dsi.com','mparag@dsi.com','akurapa@dsi.com','rmanhas@dsi.com','ssirish@dsi.com','nojha@dsi.com','srathore@dsi.com','bimanipuzha@dsi.com','sbaliyan@dsi.com',
'amalledevar@dsi.com','susaini@dsi.com')
--NO_TOKENS is not null
order by LOG_DT_TM  desc
*/

--Select datepart(D,GETDATE()),CONVERT(date,getdate())


SELECT distinct 
COUNT(distinct USR_NM)
--[USR_NM],EMP_FRST_NM ,EMP_LST_NM ,
--Functional_Area --,count([USR_NM])
--,EMP_POSN_TITL 
FROM [AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]
inner join COMM_EDS.ids.ROSTER_MASTER rm on USR_NM = EMP_BUS_EMAIL_ID
where LOG_DT_TM = CONVERT(date,getdate())
AND USR_NM NOT IN ('rbhardwaj@dsi.com','mparag@dsi.com','akurapa@dsi.com','rmanhas@dsi.com','ssirish@dsi.com','nojha@dsi.com','srathore@dsi.com','bimanipuzha@dsi.com','sbaliyan@dsi.com',
'amalledevar@dsi.com','susaini@dsi.com')
--group by Functional_Area
