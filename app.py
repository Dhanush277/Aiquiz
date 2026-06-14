import os
from flask import Flask, render_template
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config.settings import Config
from backend.routes import main_bp
from backend.auth import User, get_user_by_id

# Initialize Flask App
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config.from_object(Config)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'main.login'

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)

# Initialize Flask-Limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[Config.RATELIMIT_DEFAULT],
    storage_uri=Config.RATELIMIT_STORAGE_URL
)

# Register Blueprints
app.register_blueprint(main_bp)

# Global Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

with app.app_context():
    # Auto-generate dataset and train model if not exists
    from ml.dataset import generate_synthetic_dataset
    from ml.train_model import train_and_save_model
    import os
    
    # Check if running on Vercel to prevent Read-Only file system errors
    if not os.environ.get('VERCEL_ENV') and not os.environ.get('VERCEL'):
        try:
            if not os.path.exists('ml/model.pkl'):
                generate_synthetic_dataset('ml/data.csv', 5000)
                train_and_save_model('ml/data.csv')
        except ImportError as e:
            print(f"Warning: Could not initialize ML model on startup (ImportError): {e}")
        except Exception as e:
            print(f"Warning: Could not initialize ML model on startup: {e}")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
