from flask import Flask
from wsh_config import ConfigDev
from wsh_models import login_manager

config_object = ConfigDev()

def create_app():
    app = Flask(__name__)
    app.config.from_object(config_object)

    login_manager.init_app(app)

    from app_package.users.routes import users
    
    app.register_blueprint(users)
    
    return app      
