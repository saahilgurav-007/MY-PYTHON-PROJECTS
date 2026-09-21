"""Curated training corpus for Smart Desktop Assistant intent recognition."""

from .intent_types import IntentType

# (Utterance, IntentType) pairs
TRAINING_DATA = [
    # --- File Automation ---
    ("organize my downloads folder", IntentType.ORGANIZE_FILES),
    ("organize files in downloads", IntentType.ORGANIZE_FILES),
    ("tidy up my desktop", IntentType.ORGANIZE_FILES),
    ("sort files in downloads", IntentType.ORGANIZE_FILES),
    ("categorize files in desktop", IntentType.ORGANIZE_FILES),
    ("arrange files by type in downloads", IntentType.ORGANIZE_FILES),
    ("clean up and organize folder", IntentType.ORGANIZE_FILES),
    ("group files into folders by category", IntentType.ORGANIZE_FILES),
    ("sort my messy downloads directory", IntentType.ORGANIZE_FILES),
    ("organize documents into folders", IntentType.ORGANIZE_FILES),
    ("move images and documents to their folders", IntentType.ORGANIZE_FILES),

    ("search for files with pdf extension", IntentType.SEARCH_FILES),
    ("find all python files in project", IntentType.SEARCH_FILES),
    ("look for files named report in downloads", IntentType.SEARCH_FILES),
    ("find files modified this week", IntentType.SEARCH_FILES),
    ("search downloads for invoice", IntentType.SEARCH_FILES),
    ("where is my presentation pptx", IntentType.SEARCH_FILES),
    ("find large files bigger than 50MB", IntentType.SEARCH_FILES),
    ("locate all png images", IntentType.SEARCH_FILES),

    ("batch rename files in folder", IntentType.BATCH_RENAME),
    ("rename all text files to md in directory", IntentType.BATCH_RENAME),
    ("add prefix draft to all files", IntentType.BATCH_RENAME),
    ("replace spaces with underscores in folder", IntentType.BATCH_RENAME),
    ("rename files matching test to sample", IntentType.BATCH_RENAME),
    ("bulk rename images in folder", IntentType.BATCH_RENAME),

    ("clean temporary files", IntentType.CLEANUP_TEMP),
    ("clear temp folder", IntentType.CLEANUP_TEMP),
    ("delete cache and temporary files", IntentType.CLEANUP_TEMP),
    ("free up disk space by cleaning temp", IntentType.CLEANUP_TEMP),
    ("purge temporary cache files", IntentType.CLEANUP_TEMP),
    ("empty temp directory", IntentType.CLEANUP_TEMP),

    # --- System & Hardware Automation ---
    ("check system performance", IntentType.SYSTEM_STATS),
    ("show cpu and ram usage", IntentType.SYSTEM_STATS),
    ("how much memory is free", IntentType.SYSTEM_STATS),
    ("check disk space remaining", IntentType.SYSTEM_STATS),
    ("system health check report", IntentType.SYSTEM_STATS),
    ("what is my current battery percentage", IntentType.SYSTEM_STATS),
    ("show system metrics and uptime", IntentType.SYSTEM_STATS),
    ("hardware diagnostic status", IntentType.SYSTEM_STATS),

    ("list running processes", IntentType.LIST_PROCESSES),
    ("show top memory consuming processes", IntentType.LIST_PROCESSES),
    ("what apps are currently running", IntentType.LIST_PROCESSES),
    ("display active tasks and services", IntentType.LIST_PROCESSES),
    ("show high cpu processes", IntentType.LIST_PROCESSES),
    ("view task manager processes list", IntentType.LIST_PROCESSES),

    ("kill process chrome", IntentType.KILL_PROCESS),
    ("terminate notepad process", IntentType.KILL_PROCESS),
    ("force close python", IntentType.KILL_PROCESS),
    ("kill pid 4820", IntentType.KILL_PROCESS),
    ("end task discord", IntentType.KILL_PROCESS),
    ("stop frozen application calc", IntentType.KILL_PROCESS),

    ("take a screenshot", IntentType.TAKE_SCREENSHOT),
    ("capture the screen", IntentType.TAKE_SCREENSHOT),
    ("snapshot screen and save image", IntentType.TAKE_SCREENSHOT),
    ("save desktop screenshot to pictures", IntentType.TAKE_SCREENSHOT),
    ("grab full screen screenshot", IntentType.TAKE_SCREENSHOT),

    ("lock workstation", IntentType.LOCK_WORKSTATION),
    ("lock computer", IntentType.LOCK_WORKSTATION),
    ("lock my pc screen", IntentType.LOCK_WORKSTATION),
    ("lock screen now", IntentType.LOCK_WORKSTATION),

    ("what is on my clipboard", IntentType.CLIPBOARD_GET),
    ("read clipboard text", IntentType.CLIPBOARD_GET),
    ("show clipboard contents", IntentType.CLIPBOARD_GET),
    ("paste clipboard", IntentType.CLIPBOARD_GET),

    ("copy text to clipboard", IntentType.CLIPBOARD_SET),
    ("set clipboard to hello world", IntentType.CLIPBOARD_SET),
    ("store message in clipboard", IntentType.CLIPBOARD_SET),

    # --- Application & Web ---
    ("open notepad", IntentType.LAUNCH_APP),
    ("launch chrome browser", IntentType.LAUNCH_APP),
    ("start visual studio code", IntentType.LAUNCH_APP),
    ("open calculator", IntentType.LAUNCH_APP),
    ("open terminal console", IntentType.LAUNCH_APP),
    ("run command prompt cmd", IntentType.LAUNCH_APP),
    ("launch task manager", IntentType.LAUNCH_APP),
    ("open file explorer", IntentType.LAUNCH_APP),
    ("start msedge", IntentType.LAUNCH_APP),
    ("open paint app", IntentType.LAUNCH_APP),

    ("open website https://github.com", IntentType.OPEN_URL),
    ("go to google.com", IntentType.OPEN_URL),
    ("browse to youtube.com", IntentType.OPEN_URL),
    ("open stackoverflow in browser", IntentType.OPEN_URL),
    ("visit website reddit.com", IntentType.OPEN_URL),

    # --- External APIs ---
    ("what is the weather in Delhi", IntentType.WEATHER_QUERY),
    ("check weather forecast for London", IntentType.WEATHER_QUERY),
    ("is it raining in Mumbai", IntentType.WEATHER_QUERY),
    ("temperature in Tokyo right now", IntentType.WEATHER_QUERY),
    ("weather in New York", IntentType.WEATHER_QUERY),
    ("how is the weather in Paris", IntentType.WEATHER_QUERY),
    ("current weather report Bengaluru", IntentType.WEATHER_QUERY),

    ("summarize quantum computing on wikipedia", IntentType.WIKI_SUMMARY),
    ("tell me about Albert Einstein on wikipedia", IntentType.WIKI_SUMMARY),
    ("wikipedia article for Artificial Intelligence", IntentType.WIKI_SUMMARY),
    ("who is Alan Turing summary", IntentType.WIKI_SUMMARY),
    ("wiki search machine learning", IntentType.WIKI_SUMMARY),

    ("what is my public ip address", IntentType.NETWORK_DIAGNOSTICS),
    ("check internet connection and ping", IntentType.NETWORK_DIAGNOSTICS),
    ("test network latency to google", IntentType.NETWORK_DIAGNOSTICS),
    ("is my internet working properly", IntentType.NETWORK_DIAGNOSTICS),
    ("network ping test", IntentType.NETWORK_DIAGNOSTICS),

    ("convert 100 USD to INR", IntentType.CURRENCY_CONVERT),
    ("exchange rate EUR to USD", IntentType.CURRENCY_CONVERT),
    ("how much is 50 GBP in INR", IntentType.CURRENCY_CONVERT),
    ("currency exchange 200 EUR to JPY", IntentType.CURRENCY_CONVERT),

    # --- Routines & Scheduling ---
    ("create routine morning_setup", IntentType.CREATE_ROUTINE),
    ("new workflow dev_session", IntentType.CREATE_ROUTINE),
    ("save new routine clean_workspace", IntentType.CREATE_ROUTINE),
    ("build macro daily_routine", IntentType.CREATE_ROUTINE),

    ("run morning routine", IntentType.RUN_ROUTINE),
    ("execute dev_session routine", IntentType.RUN_ROUTINE),
    ("trigger clean_workspace workflow", IntentType.RUN_ROUTINE),
    ("start routine morning_setup", IntentType.RUN_ROUTINE),

    ("list all routines", IntentType.LIST_ROUTINES),
    ("show saved workflows", IntentType.LIST_ROUTINES),
    ("what routines do i have available", IntentType.LIST_ROUTINES),
    ("display all automated macros", IntentType.LIST_ROUTINES),

    ("remind me to drink water in 10 minutes", IntentType.SET_REMINDER),
    ("set a timer for 5 minutes", IntentType.SET_REMINDER),
    ("remind me in 30 seconds to check oven", IntentType.SET_REMINDER),
    ("set reminder in 1 hour for team standup", IntentType.SET_REMINDER),
    ("alert me in 15 minutes", IntentType.SET_REMINDER),

    # --- Meta ---
    ("help", IntentType.HELP),
    ("what can you do", IntentType.HELP),
    ("show available commands", IntentType.HELP),
    ("instructions on how to use assistant", IntentType.HELP),

    ("exit", IntentType.EXIT),
    ("quit assistant", IntentType.EXIT),
    ("close program", IntentType.EXIT),
    ("bye", IntentType.EXIT),
]
