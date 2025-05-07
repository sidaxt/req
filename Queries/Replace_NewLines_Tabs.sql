-- Sample string with new lines and tab spaces
DECLARE @TextWithFormatting NVARCHAR(MAX) = '
    This is a text
    with new lines
    and tab spaces.
';

-- Replace new lines and tab spaces with a specific character (e.g., '|')
DECLARE @TextWithoutFormatting NVARCHAR(MAX) 
--SET @TextWithoutFormatting = REPLACE(REPLACE(@TextWithFormatting, CHAR(13), '|'), CHAR(9), '|');
SET @TextWithoutFormatting = REPLACE(REPLACE(@TextWithFormatting, CHAR(9), '|'), CHAR(13), '|');
--SET @TextWithoutFormatting = REPLACE(REPLACE(@TextWithFormatting, CHAR(13), ''), CHAR(9), '');
--SET @TextWithoutFormatting = REPLACE(REPLACE(@TextWithFormatting, CHAR(13), '``newline``'), CHAR(9), '``tabspace``');

--CHAR(13) represents a carriage return (new line).
--CHAR(9) represents a tab space.

-- Display the result
SELECT	LTRIM(RTRIM(@TextWithoutFormatting)) AS Result,
		@TextWithoutFormatting AS Result,
		Replace(@TextWithoutFormatting,'|','') afterreplace;

