from app import create_app, socketio

app = create_app('config.Config')
if __name__ =='__main__':
    socketio.run(app)
