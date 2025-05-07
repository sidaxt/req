SELECT [APPLN]
      ,[LOG_DT_TM]
      ,[USR_NM]
      ,[RESP_DT_TM]
      ,[model_name]
      ,[RESP_TM_SEC]
      ,[NO_TOKENS]
FROM	[AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]
WHERE	LOG_DT_TM between '2024-12-01' and '2024-12-31'
		AND USR_NM NOT IN ('adeorukhkar@dsi.com','amalledevar@dsi.com','indraja.purushottam.ext@dsi.com','bimanipuzha@dsi.com',
		'mparag@dsi.com','rmanhas@dsi.com','sanskar.rathore.ext@daiichisankyo.com','srathore@dsi.com','ssirish@dsi.com'
		)

--9,206,329 -- tokens consumed excluding dev group for Dec-2024
SELECT SUM([NO_TOKENS]) AS TOKEN_CONSUMPTION
FROM	[AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]
WHERE	LOG_DT_TM between '2024-12-01' and '2024-12-31'
		AND USR_NM NOT IN ('adeorukhkar@dsi.com','amalledevar@dsi.com','indraja.purushottam.ext@dsi.com','bimanipuzha@dsi.com',
		'mparag@dsi.com','rmanhas@dsi.com','sanskar.rathore.ext@daiichisankyo.com','srathore@dsi.com','ssirish@dsi.com'
		)

--9,467,087 -- tokens consumed including dev group for Dec-2024
SELECT SUM([NO_TOKENS]) AS TOKEN_CONSUMPTION
FROM	[AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]
WHERE	LOG_DT_TM between '2024-12-01' and '2024-12-31'

--260758 -- tokens consumed by dev group as of 31-Dec-2024
--SELECT	9467087 - 9206329
SELECT SUM([NO_TOKENS]) AS TOKEN_CONSUMPTION
FROM	[AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]
WHERE	LOG_DT_TM between '2024-12-01' and '2024-12-31'
		AND USR_NM  IN ('adeorukhkar@dsi.com','amalledevar@dsi.com','indraja.purushottam.ext@dsi.com','bimanipuzha@dsi.com',
		'mparag@dsi.com','rmanhas@dsi.com','sanskar.rathore.ext@daiichisankyo.com','srathore@dsi.com','ssirish@dsi.com'
		)

/*
--ai-gen
SELECT DISTINCT [APPLN]      
FROM	[AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]
WHERE	LOG_DT_TM between '2024-12-01' and '2024-12-31'

--430 in total including Dev group
SELECT DISTINCT USR_NM
FROM	[AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]
WHERE	LOG_DT_TM between '2024-12-01' and '2024-12-31'

--separately add for checking the id's
AND (USR_NM LIKE '%malle%' or USR_NM LIKE '%deorukhkar%' or USR_NM LIKE '%rathore%' or USR_NM LIKE '%parag%'
or USR_NM LIKE '%manhas%' or USR_NM LIKE '%sirish%' or USR_NM LIKE '%indraja%' or USR_NM LIKE '%manipu%' or USR_NM LIKE '%puru%')
ORDER BY 1

--423 in total excluding Dev group
SELECT DISTINCT USR_NM
FROM	[AI_ASSTNT].[LOGGING].[LOG_TABLE_AI_ASSTNT]
WHERE	LOG_DT_TM between '2024-12-01' and '2024-12-31'
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

