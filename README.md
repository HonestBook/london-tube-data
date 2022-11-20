## How to use this application
0. Make sure there is a local MySQL server running.
1. Start the application.
2. Enter user credentials for the MySQL server.
3. You can now make queries, use "help" to see all the possible commands.

## Prerequisites
IMPORTANT: this application requires python 3 as it contains extensive use of the
new f-string and other new features.

# Libraries
1. MySQL Connector/Python for accessing the MySQL server
https://dev.mysql.com/doc/connector-python/en/
2. PyYAML for configuration
https://pypi.org/project/PyYAML/

## Engineering Decisions
# Programmng style
1. Snake case and single quotes (except for multi-line strings) are used throughout
the whole application as per python conventions.
2. Order of functions/code blocks, if block A is dependent on block B, then 
block B is written above block A.
3. A main function is not included as the application is not likely to be used
as a module in another context. But it could be useful for testing purposes.

# Design
1. Configurations (including string literals) are stored in a separate config.yaml
file for better adaptability.
2. Other than foreign key, there is no extra constraint on the database schema. 
Because the user is not supposed to modify the database directly.
3. The schema is written as a separate SQL file for better readability.
Also, it facilitates the possiblity of a potential database migration.
4. Every time the application starts, the required tables are dropped before
loading the data. This can have bad consequences, however, this helps the 
application to be in a predictable state when boot up. Also, if ever London
underground updates (which happens fairly often), the only change need to be
made is on the json file.
