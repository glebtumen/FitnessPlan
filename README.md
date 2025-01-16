# FitnessPlan - meal planner for a week
A Telegram bot that uses openai to 
 - generate meal plan for a week according to your specific measures

### Deployment
Settings of the bot is determined using environment variables or `.env` file
Check the `example.env` file and create your own `.env` file.
```commandline
cp example.env .env
nano .env
```
Then run the bot using `docker compose`
```commandline
docker compose up --build
```
