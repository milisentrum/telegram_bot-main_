from queue_database.database import setup_database
import threading
from main import bot
from simulator import test_loop, display_current_rows

con = setup_database()

def start_bot():
    bot.infinity_polling()

if __name__ == '__main__':
    print("Before changes:")
    display_current_rows(con)

    bot_thread = threading.Thread(target=start_bot)
    bot_thread.start()

    test_loop(con)
