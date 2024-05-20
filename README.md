## Telegram Bot with connection to DB (and repl DB)
## Usage
- Step 1: Set the required local parameters
  - inventory:
    - db_host - IP address and user data to connect to the host for the database
    - db_repl_host - IP address and user data to connect to the host for database replication
    - bot_host - IP address and user data to connect to the host for the bot
  - secrets.yml
    - You need to create this file in the main directory. In it you need to define the main environment variables in the format KEY: ‘’VALUE‘’
 
- Step 2: Start the project using this command \
  ```ansible-playbook playbook_tg_bot.yaml -e @secrets.yml```
