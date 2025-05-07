SELECT [APPLN]
      ,[LOG_DT_TM]
      ,[USR_NM]
      ,[RESP_DT_TM]
      ,[model_name]
      ,[RESP_TM_SEC]
      ,[NO_TOKENS]
FROM	[AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]
WHERE	LOG_DT_TM between '2025-01-01' and '2025-01-30'
		AND USR_NM NOT IN ('adeorukhkar@dsi.com','amalledevar@dsi.com','indraja.purushottam.ext@dsi.com','bimanipuzha@dsi.com',
		'mparag@dsi.com','rmanhas@dsi.com','sanskar.rathore.ext@daiichisankyo.com','srathore@dsi.com','ssirish@dsi.com'
		)

--20,755,538 -- tokens consumed excluding dev group as of 30-Jan, 8 PM IST
SELECT SUM([NO_TOKENS]) AS TOKEN_CONSUMPTION
FROM	[AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]
WHERE	LOG_DT_TM between '2025-01-01' and '2025-01-30'
		AND USR_NM NOT IN ('adeorukhkar@dsi.com','amalledevar@dsi.com','indraja.purushottam.ext@dsi.com','bimanipuzha@dsi.com',
		'mparag@dsi.com','rmanhas@dsi.com','sanskar.rathore.ext@daiichisankyo.com','srathore@dsi.com','ssirish@dsi.com'
		)

--21,064,608 -- tokens consumed including dev group as of 30-Jan, 8 PM IST
SELECT SUM([NO_TOKENS]) AS TOKEN_CONSUMPTION
FROM	[AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]
WHERE	LOG_DT_TM between '2025-01-01' and '2025-01-30'		

--309070 -- tokens consumed by dev group as of 30-Jan, 8 PM IST
--SELECT	21064608 - 20755538
SELECT SUM([NO_TOKENS]) AS TOKEN_CONSUMPTION
FROM	[AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]
WHERE	LOG_DT_TM between '2025-01-01' and '2025-01-30'
		AND USR_NM  IN ('adeorukhkar@dsi.com','amalledevar@dsi.com','indraja.purushottam.ext@dsi.com','bimanipuzha@dsi.com',
		'mparag@dsi.com','rmanhas@dsi.com','sanskar.rathore.ext@daiichisankyo.com','srathore@dsi.com','ssirish@dsi.com'
		)

/*
--ai-gen
SELECT DISTINCT [APPLN]      
FROM	[AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]
WHERE	LOG_DT_TM between '2025-01-01' and '2025-01-30'

--569 in total including Dev group
SELECT DISTINCT USR_NM
FROM	[AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]
WHERE	LOG_DT_TM between '2025-01-01' and '2025-01-30'
AND (USR_NM LIKE '%malle%' or USR_NM LIKE '%deorukhkar%' or USR_NM LIKE '%rathore%' or USR_NM LIKE '%parag%'
or USR_NM LIKE '%manhas%' or USR_NM LIKE '%sirish%' or USR_NM LIKE '%indraja%' or USR_NM LIKE '%mani%' or USR_NM LIKE '%puru%')
ORDER BY 1

--560 in total excluding Dev group
SELECT DISTINCT USR_NM
FROM	[AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]
WHERE	LOG_DT_TM between '2025-01-01' and '2025-01-30'
		AND USR_NM NOT IN ('adeorukhkar@dsi.com','amalledevar@dsi.com','indraja.purushottam.ext@dsi.com','bimanipuzha@dsi.com',
		'mparag@dsi.com','rmanhas@dsi.com','sanskar.rathore.ext@daiichisankyo.com','srathore@dsi.com','ssirish@dsi.com'
		)

USR_NM
adeorukhkar@dsi.com
amalledevar@dsi.com
bimanipuzha@dsi.com
indraja.purushottam.ext@dsi.com
mparag@dsi.com
rmanhas@dsi.com
sanskar.rathore.ext@daiichisankyo.com
srathore@dsi.com
ssirish@dsi.com

Aditi
Amey
Sanskar
Parag
Rakshit
Sidharth
Bilahari
Indraja

*/

