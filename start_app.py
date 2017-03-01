# coding=utf-8
from app.views import app
from flask import g
try:
    import local_setings
except ImportError:
    local_setings = object



HOST = getattr(local_setings, 'HOST', '0.0.0.0')
PORT = getattr(local_setings, 'PORT', 8000)
DEBUG = getattr(local_setings, 'DEBUG', True)


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, 'sqlite_db', None)
    if db is not None:
        db.close()
if __name__ == '__main__':
    app.run(host=HOST, debug=DEBUG, port=PORT)