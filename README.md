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
1. Snake case and single quotes (except for multi-line strings) are used throughout the whole application as per python conventions.
2. Order of functions/code blocks, if block A is dependent on block B, then block B is written above block A.

# Design
1. Configurations (including string literals) are stored in a separate config.yaml
file for better adaptability.
2. Other than foreign key, there is no extra constraint on the database schema. 
Because the user is not supposed to modify the database directly.

# Behavioural 