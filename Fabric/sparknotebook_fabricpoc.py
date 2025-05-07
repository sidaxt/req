# Welcome to your new notebook
# Type here in the cell editor to add code!
import os

# abfss://Fabric_PoC@onelake.dfs.fabric.microsoft.com/FabricLakehousePoC.Lakehouse/Files/Marketing/CMI_DSI/DSI
# abfss://Fabric_PoC@onelake.dfs.fabric.microsoft.com/FabricLakehousePoC.Lakehouse/Files/Marketing/CMI_DSI/DSI/DSI_Content_Categorization_01102024.txt
# abfss://Fabric_PoC@onelake.dfs.fabric.microsoft.com/FabricLakehousePoC.Lakehouse/Files/Marketing/CMI_DSI/DSI/DSI_control_20231206.csv
# https://onelake.dfs.fabric.microsoft.com/Fabric_PoC/FabricLakehousePoC.Lakehouse/Files/Marketing/CMI_DSI/DSI
# /lakehouse/default/Files/Marketing/CMI_DSI/DSI
# abfss://Fabric_PoC@onelake.dfs.fabric.microsoft.com/FabricLakehousePoC.Lakehouse/Files/Marketing/CMI_DSI/DSI

# input_directory_path = "abfss://Fabric_PoC@onelake.dfs.fabric.microsoft.com/FabricLakehousePoC.Lakehouse/Files/Marketing/CMI_DSI/DSI"
# output_directory_path = "abfss://Fabric_PoC@onelake.dfs.fabric.microsoft.com/FabricLakehousePoC.Lakehouse/Files/Marketing/CMI_DSI/DSI/Output"

input_directory_path = "Files/Marketing/CMI_DSI/DSI"
output_directory_path = "Files/Marketing/CMI_DSI/DSI/Output"

import pandas as pd

# df = spark.read.format("csv").option("header","true").load("Files/Marketing/CMI_DSI/DSI/DSI_control_20231206.csv")
# display(df)

# df2 = spark.read.csv("abfss://Fabric_PoC@onelake.dfs.fabric.microsoft.com/FabricLakehousePoC.Lakehouse/Files/Marketing/CMI_DSI/DSI/DSI_control_20231206.csv", header=True, inferSchema=True)

# Assuming you are dealing with CSV files
for file_name in os.listdir(input_directory_path):
    if file_name.endswith(".csv"):  # Check if the file is a CSV
        file_path = os.path.join(input_directory_path, file_name)
        
        # Read the individual file
        df = spark.read.csv(file_path, header=True, inferSchema=True)
        
        # Define a unique output path for each Parquet file
        parquet_path = os.path.join(output_directory_path, os.path.splitext(file_name)[0] + ".parquet")
        
        # Write the DataFrame to Parquet format
        df.write.parquet(parquet_path)


"""
df = spark.read.format("csv").option("header","true").load("Files/Marketing/CMI_DSI/DSI/DSI_control_20231206.csv")
# df now is a Spark DataFrame containing CSV data from "Files/Marketing/CMI_DSI/DSI/DSI_control_20231206.csv".
display(df)

df = spark.read.format("csv").option("header","true").load("Files/Marketing/CMI_DSI/DSI/DSI_control_20240103.csv")
# df now is a Spark DataFrame containing CSV data from "Files/Marketing/CMI_DSI/DSI/DSI_control_20240103.csv".
display(df)
"""




df = (spark
.read
.format("csv")
.option("header","true")
.load("Files/Marketing/CMI_DSI/DSI/DSI_control_20231206.csv"))

# df now is a Spark DataFrame containing CSV data from "Files/Marketing/CMI_DSI/DSI/DSI_control_20231206.csv".
display(df)






import os
import pandas as pd

from pyspark.sql import *
from pyspark import SparkContext,SparkConf

input_directory_path = "Files/Marketing/CMI_DSI/DSI"
newoutput_directory_path = "Files/Marketing/CMI_DSI/Output"

# abfss://Fabric_PoC@onelake.dfs.fabric.microsoft.com/FabricLakehousePoC.Lakehouse/Files/Marketing/CMI_DSI
# ('abfss://9a1d18cd-bd48-4f79-bd8a-c6fd9b083fd2@onelake.dfs.fabric.microsoft.com/d2793208-ad41-44b1-bb3f-47a56f023633/Files/Marketing/CMI_DSI/DSI/DSI_Content_Categorization_01102024', '.txt')
# ('abfss://9a1d18cd-bd48-4f79-bd8a-c6fd9b083fd2@onelake.dfs.fabric.microsoft.com/d2793208-ad41-44b1-bb3f-47a56f023633/Files/Marketing/CMI_DSI/DSI/DSI_control_20240110', '.csv') 
# abfss://9a1d18cd-bd48-4f79-bd8a-c6fd9b083fd2@onelake.dfs.fabric.microsoft.com/d2793208-ad41-44b1-bb3f-47a56f023633/Files/Marketing/CMI_DSI/DSI/DSI_control_20240110.csv


conf = SparkConf().setMaster("local").setAppName("sparkproject")
sc = SparkContext.getOrCreate(conf=conf)
sqlContext = SQLContext(sc)

# Filelists = sc.wholeTextFiles("Files/Marketing/CMI_DSI/DSI/*.csv").map(lambda x: x[0]).collect()
# Filelists = sc.wholeTextFiles("Files/Marketing/CMI_DSI/DSI/*").map(lambda x: x[0]).collect()
Filelists = sc.wholeTextFiles(input_directory_path + "/*").map(lambda x: x[0]).collect()
# print(sc.wholeTextFiles(input_directory_path + "/*").map(lambda x: x[0]))
# FilelistsReplace = 
# print(Filelists)

# SparkSession = SparkSession(sc)
# # df=SparkSession.read.option("recursiveFileLookup","true").option("header","true")
# .csv(input_directory_path) 
#  + "/DSI_control_20240124.csv")
# sparkfiles =SparkSession.read.option("recursiveFileLookup","true").option("header","true")
# print(sparkfiles)
# for files in sparkfiles:
#     print(files)
# df.show()

for filepath in Filelists:
    # print(filepath, 'fullfile')
    # print(os.path.splitext(filepath),filepath)
    # print(1)
    # ,replace(os.path.splitext(filepath),input_directory_path,''))
    if filepath.endswith(".csv"):
        # print(filepath, 'csvfile')
        # print(os.path.splitext(filepath)[0],os.path.splitext(filepath)[1])
        df = sqlContext.read.csv(filepath, header=True, inferSchema=True)
        df.show()

        # parquet_path = os.path.join(newoutput_directory_path, os.path.splitext(filepath)[0] + ".parquet")
        # print(parquet_path)

        df.write.format("parquet").mode("append").save(newoutput_directory_path)

        # Write the DataFrame to Parquet format
        # df.write.mode("overwrite").parquet(parquet_path)
    elif filepath.endswith(".txt"):
        print(1)
        # print(filepath, 'txtfile')
        # print(os.path.splitext(filepath)[0],os.path.splitext(filepath)[1])



        # df2 = sqlContext.read.text(filepath,lineSep="\n")
        # df2.show()

        # df3 = sqlContext.read.format("text").load(filepath)
        # display(df3)
        
        # df4 = spark.read.csv(filepath)
        # df4.show()

        df5 = spark.read.option("header","True").option("delimiter","\t").csv(filepath)
        df5.show()
        
        # shutil.rmtree(filepath + "/txt")

        df5.write.format("parquet").mode("append").save(newoutput_directory_path_txt)

        # df5 = spark.read.format("txt").option("header","True").option("delimiter","\t").csv(filepath)
        # df5 = spark.read.option("header","True").option("delimiter","\t").options(sep="\t").csv(filepath)
        
        # print(1)
        # print(filepath, 'txtfile')
        # print(os.path.splitext(filepath)[0],os.path.splitext(filepath)[1])


# spark = SparkSession.builder.getOrCreate()
# files = spark.sparkContext.wholeTextFiles(input_directory_path)
# for file in files:
#     file_name = file[0]
#     print(file)
#     # display(file_name)
        



import os
import pandas as pd
import shutil

from pyspark.sql import *
from pyspark import SparkContext,SparkConf

input_directory_path = "Files/Marketing/CMI_DSI/DSI"
newoutput_directory_path_csv = "Files/Marketing/CMI_DSI/Output/csv"
newoutput_directory_path_txt = "Files/Marketing/CMI_DSI/Output/txt"

conf = SparkConf().setMaster("local").setAppName("sparkproject")
sc = SparkContext.getOrCreate(conf=conf)
sqlContext = SQLContext(sc)

Filelists = sc.wholeTextFiles(input_directory_path + "/*").map(lambda x: x[0]).collect()

for filepath in Filelists:    
    if filepath.endswith(".txt"):
        df5 = spark.read.option("header","True").option("delimiter","\t").csv(filepath)
        # .schema(schema)
        # df5columnlist = df5.columns.str.replace('-','_')
        # df5.printSchema()
        # dfColumns = df5.selectExpr('Creative UTM AS Creative_UTM')
        # dfColumns.show()
        # display(df5columnlist)

        df6 = (df5.withColumnRenamed('Creative UTM','Creative_UTM')
        .withColumnRenamed('Content UTM','Content_UTM')
        .withColumnRenamed('Brand-Audience','Brand_Audience')
        .withColumnRenamed('Brand-Indication-Audience','Brand_Indication_Audience')
        .withColumnRenamed('Creative Code','Creative_Code')
        .withColumnRenamed('Campaign UTM','Campaign_UTM')
        .withColumnRenamed('Medium UTM','Medium_UTM')
        .withColumnRenamed('Source UTM','Source_UTM')
        .withColumnRenamed('Content Category','Content_Category')
        .withColumnRenamed('Placement UTM','Placement_UTM')
        .withColumnRenamed('Destination URL','Destination_URL')
        .withColumnRenamed('Anchor Tag','Anchor_Tag')
        .withColumnRenamed('Placement ID','Placement_ID')
        )
        df6.printSchema()

        # df5.show()





import os
import pandas as pd
import shutil

from pyspark.sql import *
from pyspark import SparkContext,SparkConf

input_directory_path = "Files/Marketing/CMI_DSI/DSI"
newoutput_directory_path_csv = "Files/Marketing/CMI_DSI/Output/csv"
newoutput_directory_path_txt = "Files/Marketing/CMI_DSI/Output/txt"

conf = SparkConf().setMaster("local").setAppName("sparkproject")
sc = SparkContext.getOrCreate(conf=conf)
sqlContext = SQLContext(sc)

Filelists = sc.wholeTextFiles(input_directory_path + "/*").map(lambda x: x[0]).collect()

for filepath in Filelists:
    if filepath.endswith(".csv"):
        df = sqlContext.read.csv(filepath, header=True, inferSchema=True)

        df2 = (df.withColumnRenamed('No of records','No_of_records')
        .withColumnRenamed('Metric sum','Metric_sum')
        .withColumnRenamed('File size','File_size')
        .withColumnRenamed('Date generated','Date_generated')
        .withColumnRenamed('Activity Date Min','Activity_Date_Min')
        .withColumnRenamed('Activity Date Max','Activity_Date_Max')
        .withColumnRenamed('Restatement (Y/N) (Optional)','Restatement_YN_Optional')
        )
        # df2.printSchema()

        df2.show()






df.write.format("delta").saveAsTable("DSI_control_20231206")







import pandas as pd
# Load data into pandas DataFrame from "/lakehouse/default/" + "Files/Marketing/CMI_DSI/DSI/DSI_control_20231206.csv"
df = pd.read_csv("/lakehouse/default/" + "Files/Marketing/CMI_DSI/DSI/DSI_control_20231206.csv")
display(df)






import os
import pandas as pd
import shutil

from pyspark.sql import *
from pyspark import SparkContext,SparkConf

input_directory_path = "Files/Marketing/CMI_DSI/DSI"
newoutput_directory_path_csv = "Files/Marketing/CMI_DSI/Output/csv"
newoutput_directory_path_txt = "Files/Marketing/CMI_DSI/Output/txt"


conf = SparkConf().setMaster("local").setAppName("sparkproject")
sc = SparkContext.getOrCreate(conf=conf)
sqlContext = SQLContext(sc)

Filelists = sc.wholeTextFiles(input_directory_path + "/*").map(lambda x: x[0]).collect()

for filepath in Filelists:    
    if filepath.endswith(".csv"):
        print(filepath)
        df = sqlContext.read.csv(filepath, header=True, inferSchema=True)
        df2 = (df.withColumnRenamed('No of records','No_of_records')
        .withColumnRenamed('Metric sum','Metric_sum')
        .withColumnRenamed('File size','File_size')
        .withColumnRenamed('Date generated','Date_generated')
        .withColumnRenamed('Activity Date Min','Activity_Date_Min')
        .withColumnRenamed('Activity Date Max','Activity_Date_Max')
        .withColumnRenamed('Restatement (Y/N) (Optional)','Restatement_YN_Optional')
        )

        # df2.show()
        df2.write.format("parquet").mode("append").save(newoutput_directory_path_csv)

    elif filepath.endswith(".txt"):
        df5 = spark.read.option("header","True").option("delimiter","\t").csv(filepath)
        df6 = (df5.withColumnRenamed('Creative UTM','Creative_UTM')
        .withColumnRenamed('Content UTM','Content_UTM')
        .withColumnRenamed('Brand-Audience','Brand_Audience')
        .withColumnRenamed('Brand-Indication-Audience','Brand_Indication_Audience')
        .withColumnRenamed('Creative Code','Creative_Code')
        .withColumnRenamed('Campaign UTM','Campaign_UTM')
        .withColumnRenamed('Medium UTM','Medium_UTM')
        .withColumnRenamed('Source UTM','Source_UTM')
        .withColumnRenamed('Content Category','Content_Category')
        .withColumnRenamed('Placement UTM','Placement_UTM')
        .withColumnRenamed('Destination URL','Destination_URL')
        .withColumnRenamed('Anchor Tag','Anchor_Tag')
        .withColumnRenamed('Placement ID','Placement_ID')
        )
        
        # df6.show()
        
        df6.write.format("parquet").mode("append").save(newoutput_directory_path_txt)

        # df5 = spark.read.format("txt").option("header","True").option("delimiter","\t").csv(filepath)
        # df5 = spark.read.option("header","True").option("delimiter","\t").options(sep="\t").csv(filepath)
        
        # print(1)
        # print(filepath, 'txtfile')
        # print(os.path.splitext(filepath)[0],os.path.splitext(filepath)[1])





import os
import pandas as pd
import shutil

from pyspark.sql import *
from pyspark.sql import functions as F
from pyspark import SparkContext,SparkConf
from pyspark.sql.functions import input_file_name,regexp_extract

input_directory_path = "Files/Marketing/CMI_DSI/DSI"
newoutput_directory_path_csv = "Files/Marketing/CMI_DSI/Output/csv"
newoutput_directory_path_txt = "Files/Marketing/CMI_DSI/Output/txt"


conf = SparkConf().setMaster("local").setAppName("sparkproject")
sc = SparkContext.getOrCreate(conf=conf)
sqlContext = SQLContext(sc)

Filelists = sc.wholeTextFiles(input_directory_path + "/*").map(lambda x: x[0]).collect()

FilesNames = sc.wholeTextFiles(input_directory_path + "/*").map(
    lambda x: ( '/'.join(x[0].split('/')[-2:]), x[1] )
)

print(FilesNames)

# df = Filelists.map(lambda x: (x[0].split("/")[-1],x[1])).toDF(["file_name"],"content")
# df.show()

# df = pd.read_csv("/lakehouse/default/" + "Files/Marketing/CMI_DSI/DSI/DSI_control_20231206.csv")
# display(df)


for filepath in Filelists:    
    if filepath.endswith(".csv"):
        print(filepath)
        # data = pd.read_csv(filepath)
        data = sqlContext.read.csv(filepath, header=True, inferSchema=True)
        # if 'filepathnamenewcolumn' not in data.columns:
        #     data.withColumn('filepathnamenewcolumn',filepath)
        #     # data3 = data.withColumn(filepath,input_file_name())
        #     print(data,'data2')
        
        data.withColumn("filepathnamenewcolumn",F.col(filepath))
        print(data,'data2')



        # display(data)
        # print(data,'dataframe name')
        regex_str = "[\/]([^\/]+[\/][^\/]+)$"
        # print(os.path.splitext(filepath),regexp_extract(os.path.splitext(filepath),regex_str,1))
        # data3 = data2.withColumn(filepath,regexp_extract(filepath,regex_str,1))
        print(data3, 'data output')
        data4 = data.withColumn(filepath,regexp_extract(filepath,regex_str,1))
        print(data4, 'data4')
        # print(filepath,'filepath name',regexp_extract(os.path.splitext(filepath),regex_str,1),'regex output')







import os
import pandas as pd
import shutil

from pyspark.sql import *
from pyspark.sql import functions as F
from pyspark import SparkContext,SparkConf
from pyspark.sql.functions import input_file_name,regexp_extract,col,substring

input_directory_path = "Files/Marketing/CMI_DSI/DSI"
newoutput_directory_path_csv = "Files/Marketing/CMI_DSI/Output/csv"
newoutput_directory_path_txt = "Files/Marketing/CMI_DSI/Output/txt"


conf = SparkConf().setMaster("local").setAppName("sparkproject")
sc = SparkContext.getOrCreate(conf=conf)
sqlContext = SQLContext(sc)

Filelists = sc.wholeTextFiles(input_directory_path + "/*").map(lambda x: x[0]).collect()

# df = Filelists.map(lambda x: (x[0].split("/")[-1],x[1])).toDF(["file_name"],"content")
# df.show()

# df = pd.read_csv("/lakehouse/default/" + "Files/Marketing/CMI_DSI/DSI/DSI_control_20231206.csv")
# display(df)


FilesNames = sc.wholeTextFiles(input_directory_path + "/*").map(
    lambda x: ( '/'.join(x[0].split('/')[-2:]), x[1] )
)

print(FilesNames,'FilesNames')

FilesNamesCollect = FilesNames.collect()
FilesNamesTake = FilesNames.take(5)

filenames = 'abfss://9a1d18cd-bd48-4f79-bd8a-c6fd9b083fd2@onelake.dfs.fabric.microsoft.com/d2793208-ad41-44b1-bb3f-47a56f023633/Files/Marketing/CMI_DSI/DSI/DSI_control_20231206.csv'

for filename in FilesNamesTake:
    if filename[0].endswith(".csv"):
        # print(filename[0].replace('DSI/','').replace('.csv',''),'filenamecsv')
        filenamewithoutcsvextension = filename[0].replace('DSI/','').replace('.csv','')
        print(filenamewithoutcsvextension,'filenamewithoutcsvextension')
    elif filename[0].endswith(".txt"):
        # print(filename[0].replace('DSI/',''),'filenametxt')
        filenamewithouttxtextension = filename[0].replace('DSI/','').replace('.txt','')
        print(filenamewithouttxtextension,'filenamewithouttxtextension')


# for filepath in Filelists:
#     if filepath.endswith(".csv"):
#         print(filepath)
#         # data = pd.read_csv(filepath)
#         data = sqlContext.read.csv(filepath, header=True, inferSchema=True)
#         regex_str = "[\/]([^\/]+[\/][^\/]+)$"
#         filename = os.path.splitext(filepath)[0]
#         regexp_output = regexp_extract(filename,regex_str,1)
#         print(regexp_output,'regexp')
#         print(filename,'filename output')
#         data.withColumn("filepathnamenewcolumn",F.col(regexp_output))
#         print(data,'data2')



#         # display(data)
#         # print(data,'dataframe name')
#         regex_str = "[\/]([^\/]+[\/][^\/]+)$"
#         # print(os.path.splitext(filepath),regexp_extract(os.path.splitext(filepath),regex_str,1))
#         # data3 = data2.withColumn(filepath,regexp_extract(filepath,regex_str,1))
#         print(data3, 'data output')
#         data4 = data.withColumn(filepath,regexp_extract(filepath,regex_str,1))
#         print(data4, 'data4')
#         # print(filepath,'filepath name',regexp_extract(os.path.splitext(filepath),regex_str,1),'regex output')








