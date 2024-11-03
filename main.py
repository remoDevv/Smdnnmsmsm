from app import create_app
from utils.discord_bot import run_bot
import threading

def run_flask_app():
    app = create_app()
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    # Start the Flask app in a separate thread
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.start()

    # Start the Discord bot
    run_bot()