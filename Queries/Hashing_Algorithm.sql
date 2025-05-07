DECLARE @InputString NVARCHAR(100) = 'Hello, world!';

DECLARE @HashValue VARBINARY(20);

SET @HashValue = HASHBYTES('SHA1', @InputString);

SELECT LEN(@HashValue),@HashValue AS SHA1Hash;
SELECT CONVERT(NVARCHAR(MAX), @HashValue, 2) AS HexadecimalHash;
GO


DECLARE @InputString NVARCHAR(100) = 'Hello, world!';
DECLARE @HashValue VARBINARY(32);

SET @HashValue = HASHBYTES('SHA2_256', @InputString);

SELECT LEN(@HashValue),@HashValue AS SHA256Hash;
SELECT CONVERT(NVARCHAR(MAX), @HashValue, 2) AS HexadecimalHash;
GO


DECLARE @Salt varchar(20) = 'RandomSaltString'

SELECT	HASHBYTES('SHA2_512', 'MyPassword' + @Salt) as PasswordHash,
		LEN(HASHBYTES('SHA2_512', 'MyPassword' + @Salt)) as PasswordHash,
		CONVERT(NVARCHAR(MAX), HASHBYTES('SHA2_512', 'MyPassword' + @Salt), 2) as PasswordHash

--Select	

DECLARE @InputString NVARCHAR(100) = 'Hello, world!';

DECLARE @HashValue VARBINARY(20);

SET @HashValue = HASHBYTES('SHA1', @InputString);

SELECT CONVERT(NVARCHAR(MAX), @HashValue, 2) AS HexadecimalHash;

SELECT CONVERT(NVARCHAR(MAX), HASHBYTES('SHA1', 'Hello, world!'), 2) AS HexadecimalHash;

SELECT	CONVERT(NVARCHAR(MAX), HASHBYTES('SHA1', 'Hello, world!'), 2) AS HexadecimalHash,
		CONVERT(NVARCHAR(MAX), HASHBYTES('SHA1', 'Hello, world'), 2) AS HexadecimalHash,
		CONVERT(NVARCHAR(MAX), HASHBYTES('SHA1', 'Hello world'), 2) AS HexadecimalHash,
		CONVERT(NVARCHAR(MAX), HASHBYTES('SHA1', 'hello, world'), 2) AS HexadecimalHash,
		CONVERT(NVARCHAR(MAX), HASHBYTES('SHA1', 'sidharth'), 2) AS HexadecimalHashsidharth,
		CONVERT(NVARCHAR(MAX), HASHBYTES('SHA1', 'Sidharth'), 2) AS HexadecimalHashSidharth,
		CONVERT(NVARCHAR(MAX), HASHBYTES('SHA1', 'Heaven'), 2) AS HexadecimalHashHeaven,
		CONVERT(NVARCHAR(MAX), HASHBYTES('SHA1', 'heaven'), 2) AS HexadecimalHashheaven

