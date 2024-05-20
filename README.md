## Telegram Bot with connection to DB (and repl DB)
## Usage
- Step 1: Set the required local parameters
  - .env
    - You need to create this file in the main directory. In it you need to define the main environment variables in the format KEY=VALUE
 
- Step 2: Start the project using this command \
  ```docker compose up```

Installing the required packages to host: 
- sudo apt-get install ca-certificates curl 

- sudo install -m 0755 -d /etc/apt/keyrings
  sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  sudo chmod a+r /etc/apt/keyrings/docker.asc

- echo \
	  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
- sudo apt-get update

- sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
