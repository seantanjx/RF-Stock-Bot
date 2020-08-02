# RF-Stock-Bot
Hi, my name is Sean, an undergraduate at Singapore Management University. I created this simple and user-friendly stock portfolio bot as a side-project out of my own interest during the summer holidays.
The current version of the bot has simple functions, but I made sure that it is robust and will be able to serve as a base code for future improvements.
As I venture deeper into analytics and machine learning models, I intend to integrate analysis functionalities to further extend the practicality of the bot.

# Phase 1 (Complete)
Focus areas

1) User validation
  - Dictionary
  - Database (Separate version)
  
2) Stock validation
  - Ticker
  - Company name
  
3) Minimising human error
  - Inline keyboard/buttons used to minimize user input
  
4) Web Scraping
  - Uses Selenium to retrieve stock information
  - Asynchronous
    - Each instance runs on a separate thread


# Phase 2 (WIP)
Adding stock analysis functionalities

1) Stock trends
  - ARIMA (Auto Regressive Integrated Moving Average) modelling
  - Graphical Representation & Visualisation option

2) Metrics such as (not exhaustive)
  - Industry/Sector
  - PE Ratio
  - EPS
  - ROE
  - Dividends
  
3) Retrieving stock information through API
  - Improving performance (reducing latency)
  - Retrieving historical data for stock analysis
