import json
import yaml
import logging
import mysql.connector
from mysql.connector import errorcode

### Initialisations
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

def green_msg(str):
    return f'{bcolors.OKGREEN}{str}{bcolors.ENDC}'

def red_msg(str):
    return f'{bcolors.FAIL}{str}{bcolors.ENDC}'

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
                                        password=password)
        logging.debug(green_msg('Successfully established connection with MySQL server.'))
        login_success = True 
    except mysql.connector.Error as err:
        logging.error(red_msg(f'{err}'))
        logging.info('Please re-enter your details.')
cursor = cnx.cursor()

# Use the correct databse
# Create one if it does not exist
db_name = config['db_name']

def create_database(cursor):
    try:
        cursor.execute(
            "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(db_name))
        logging.debug(green_msg(f'Database {db_name} created successfully.'))
    except mysql.connector.Error as err:
        logging.error(red_msg(f'Failed creating database: {err}'))

# Use the correct databse
# Create one if it does not exist
try:
    cursor.execute(f'USE {db_name}')
except mysql.connector.Error as err:
    logging.error(red_msg(f'Database {db_name} does not exists.'))
    if err.errno == errorcode.ER_BAD_DB_ERROR:
        create_database(cursor)
        cnx.database = db_name
    else:
        print(err)
logging.info(green_msg(f'Successfully connected to {db_name} database.'))

# Convert query result, which is a list of (single-element) tuples, to a list of strings
def flatten_result(result):
    return [row[0] for row in result]

def execute_sql_command(command):
    # For prettier printing
    command = command.strip()
    logging.debug('Executing the following sql command')
    logging.debug('------------------------------------------------')
    logging.debug(command)
    logging.debug('------------------------------------------------')
    try:
        cursor.execute(command)
        logging.debug(green_msg('Success'))
        return flatten_result(cursor.fetchall())
    except mysql.connector.Error as err:
        logging.error(red_msg(f'{err}'))

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

def insert_pair_into_table(table, column1, column2, v1, v2):
    query = f'INSERT INTO {table}({column1}, {column2}) VALUES ("{v1}", "{v2}")'
    execute_sql_command(query)

# Insert station data
stations_data = data['stations']
for row in stations_data:
    insert_pair_into_table('stations', 'id', 'name', row['id'], row['name'])

# Insert line and passing data
lines_data = data['lines']
# the loop is written this way to have id for passes data
# the downside of this is that the trainlines database has to be
# empty before inserting, otherwise the ids will not match.
for id, trainline in enumerate(lines_data):
    insert_pair_into_table('trainlines', 'id', 'name', id, trainline['name'])
    for passed_station in trainline['stations']:
        insert_pair_into_table('passes', 'station_id', 'line_id', passed_station, id)

cnx.commit()

### Functions for resolving user queries

def get_station_info(station_name):
    station_query = f"""
    SELECT trainlines.name
    FROM trainlines
    WHERE trainlines.id IN
    (SELECT line_id
    FROM passes
    WHERE passes.station_id IN 
    (SELECT id
    FROM stations
    WHERE stations.name = "{station_name}"));
    """
    try:
        result = execute_sql_command(station_query)
        if not result:
            logging.info(red_msg('There is no such station'))
        else:
            logging.info(f'{bcolors.OKCYAN}{station_name.capitalize()}{bcolors.ENDC} Station has the following lines passing through:')
            logging.info(result)
    except mysql.connector.Error as err:
        logging.error(err)

def get_line_info(line_name):
    line_query = f"""
    SELECT stations.name
    FROM stations
    WHERE stations.id IN
    (SELECT station_id
    FROM passes
    WHERE passes.line_id IN 
    (SELECT id
    FROM trainlines
    WHERE trainlines.name = "{line_name}"));
    """
    try:
        result = execute_sql_command(line_query)
        if not result:
            logging.info(red_msg('There is no such line'))
        else:
            logging.info(f'{bcolors.OKCYAN}{line_name.capitalize()}{bcolors.ENDC} Line passes through the following stations:')
            logging.info(result)
    except mysql.connector.Error as err:
        logging.error(err)

def show_names_in_table(table):
    query = f"SELECT name FROM {table}"
    try:
        result = execute_sql_command(query)
        if result is not None:
            for item in result:
                print(item)
        logging.info(green_msg(f'Above are all the {table} in the database'))
    except mysql.connector.Error as err:
        logging.error(err)

def show_stations():
    show_names_in_table('stations')

def show_lines():
    show_names_in_table('trainlines')

def show_help():
    help_str = f"""
    Available commands:
    {bcolors.OKCYAN}station <station-name>{bcolors.ENDC} - show what lines go through a specific station
    {bcolors.OKCYAN}line <line-name>{bcolors.ENDC} - show the stations that a specific line goes through
    {bcolors.OKCYAN}list <stations|lines>{bcolors.ENDC} - show all the stations or lines
    {bcolors.OKCYAN}quit{bcolors.ENDC}|{bcolors.OKCYAN}exit{bcolors.ENDC} - terminate this application
    {bcolors.OKCYAN}help{bcolors.ENDC} - display this help message
    """
    print(help_str)

### Continuously accept user queries
quit = False

# Resolve a single query from user
def resolve_query(query):
    words = query.split()
    # The first word in a query is the command term
    # Whatever comes afterwards are treated collectively as argument term
    command_term = words[0]
    argument_term = ' '.join(words[1:])
    if query == 'quit' or query == 'exit':
        global quit
        quit = True
        logging.info('Bye')
    elif command_term == 'station':
        get_station_info(argument_term)
    elif command_term == 'line':
        get_line_info(argument_term)
    elif command_term == 'list':
        if argument_term == 'stations':
            show_stations()
        elif argument_term == 'lines':
            show_lines()
        else:
            logging.error(red_msg('Query is not recognised. Try "list stations" or "list lines"'))
    elif command_term == 'help':
        show_help()
    else:
        logging.error(red_msg('Query is not recognised.'))

while not quit:
    logging.info(f'Try {bcolors.OKCYAN}help{bcolors.ENDC} to see the list of possible queries.')
    # Prompt the user to enter a query
    query = input('Please enter a query: ')
    resolve_query(query)

# Terminate the connection to MySQL server
cursor.close()
cnx.close()
