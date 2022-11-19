import json
import yaml
# TODO refactor the code using logger
import logging
import mysql.connector
from mysql.connector import errorcode

### Load the config file
with open('config.yaml') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

# Configure the Logger
logging.getLogger().setLevel(config['logging_level'])

# Colours for prettier printing
# Copied from joeld and Peter Mortensen
# https://stackoverflow.com/questions/287871/how-do-i-print-colored-text-to-the-terminal
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

### Write data into the sql server
## Establish a connection with the sql server

login_success = False
# If wrong credentials were entered, ask again.
while not login_success:
    # Prompt the user to enter credentials
    username = input('Username: ')
    password = input('Password: ')
    try:
        cnx = mysql.connector.connect(user=username,
                                        password=password,
                                        database=config['db_name'])
        print('Successfully established connection with MySQL server')
        login_success = True 
    except mysql.connector.Error as err:
        print(err)
        print('Please re-enter your details.')
cursor = cnx.cursor()

# Use the correct databse
# Create one if it does not exist
db_name = config['db_name']

def create_database(cursor):
    try:
        cursor.execute(
            "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(db_name))
    except mysql.connector.Error as err:
        print("Failed creating database: {}".format(err))
        exit(1)

try:
    cursor.execute("USE {}".format(db_name))
except mysql.connector.Error as err:
    print("Database {} does not exists.".format(db_name))
    if err.errno == errorcode.ER_BAD_DB_ERROR:
        create_database(cursor)
        print("Database {} created successfully.".format(db_name))
        cnx.database = db_name
    else:
        print(err)
        exit(1)
print('Now using database {}'.format(db_name))

def execute_sql_command(command):
    # For prettier printing
    command = command.strip()
    logging.debug('Executing the following sql command')
    logging.debug('------------------------------------------------')
    logging.debug(command)
    logging.debug('------------------------------------------------')
    try:
        cursor.execute(command)
        logging.debug(f'{bcolors.OKGREEN}Success{bcolors.ENDC}')
    except mysql.connector.Error as err:
        logging.error(f'{bcolors.FAIL}{err}{bcolors.ENDC}')

# Update the database schema accordign to the sql file
with open(config['schema_path']) as f:
    file_content = f.read()
commands = file_content.split(';')

for command in commands:
    execute_sql_command(command)

### Insert data

# load the json file
with open(config['data_path']) as f:
    data = json.load(f)

# Insert station data
stations_data = data['stations']
for row in stations_data:
    id = row['id']
    name = row['name']
    insert_station = f'INSERT INTO stations(id, name) VALUES ("{id}", "{name}")'
    execute_sql_command(insert_station)

# Insert line and passing data
lines_data = data['lines']
# the loop is written this way to have id for passes data
# the downside of this is that the trainlines database has to be
# empty before inserting, otherwise the ids will not match.
for id, line in enumerate(lines_data):
    name = line['name']
    insert_line = f'INSERT INTO trainlines(id, name) VALUES ("{id}", "{name}")'
    execute_sql_command(insert_line)
    for passed_station in line['stations']:
        insert_pass = f'INSERT INTO passes(station_id, line_id) VALUES ("{passed_station}", "{id}")'
        execute_sql_command(insert_pass)

cnx.commit()


### Continuously accept user queries

# Exectute an sql query where there is a marker for the user input
def execute_sql_command_with_markers(command, argument):
    # For prettier printing
    command = command.strip()
    logging.debug('Executing the following sql command')
    logging.debug('------------------------------------------------')
    logging.debug(command)
    logging.debug('------------------------------------------------')
    logging.debug('The argument to replace the marker is: {}'.format(argument))
    try:
        # Convert the argument to a tuple as per the mysql connector documentation
        cursor.execute(command, (argument,))
        logging.debug(f'{bcolors.OKGREEN}Success{bcolors.ENDC}')
    except mysql.connector.Error as err:
        logging.error(f'{bcolors.FAIL}{err}{bcolors.ENDC}')

def get_station_info(station_name):
    query_station = """
    select trainlines.name
    from trainlines
    where trainlines.id in
    (select line_id
    from passes
    where passes.station_id in 
    (select id
    from stations
    where stations.name = %s));
    """
    try:
        execute_sql_command_with_markers(query_station, (station_name))
        result = cursor.fetchall()
        print(result)
    except:
        print('No such station')

def get_line_info(line_name):
    # TODO
    pass

def resolve_query(query):
    words = query.split()
    command_term = words[0]
    if command_term == 'station':
        station_name = ' '.join(words[1:])
        get_station_info(station_name)
    elif command_term == 'line':
        line_name = ' '.join(words[1:])
        get_line_info(line_name)
    elif command_term == 'list':
        # TODO implement
        pass
        # show_stations()
        # show_lines()

quit = False
while not quit:
    # Prompt the user to enter a query
    query = input('Please enter a query: ')
    if query == 'quit' or query == 'exit':
        quit = True
    else:
        resolve_query(query)


## TODO Use "list stations" or "list lines" to see all the stations/lines

## TODO Use "help" to see all the possible commands


cursor.close()
cnx.close()

### TODO Allow the user to quit

