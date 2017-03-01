# coding=utf-8
from flask import Flask, url_for, render_template, request, redirect, jsonify, session, send_file
import models
import json
import datetime
import time
import md5
from werkzeug import secure_filename
app = Flask(__name__)

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'webm', 'mp4', 'avi', 'mov', 'mpeg']

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.template_filter('dt')
def datetimee(date):
    return datetime.datetime.utcfromtimestamp(float(date)).strftime("""%d-%m-%Y %H:%M:%S""")

@app.template_filter('log')
def log(tolog):
    print(tolog)

@app.route('/test')
def test():
    return render_template('test.html', date = int(time.time()))
#@app.route('/<id>')
#def hello_world(id=None):
#    if request.method == 'GET':
#        pass
#    elif resquest.method == 'POST':
#        pass
#    user = models.User.get_user('toot')
#    posts = models.Post.get_posts(user['username'])
#    for post in posts:
#        commentaires = models.Commentaire.get_commentaires(post['id'])
#        post['commentaires'] = commentaires
#        post['nb_com'] = len(commentaires)
#    return render_template('index.html', posts = posts)

#mettre un champ invisible dans les form pour la redirection
#l'url de la form est /login mais on sait ou on doit rediriger si le login est bon
#l'url login doit être accessible en GET pour les messages d'erreurs (trop compliqués à intégrer dans le header)
#!!!!!!!!!!!!!!!!!!!!!

def do_login(nickname, clear_password, redirect_url):
    connection = False
    user = models.user.get_by_name(nickname)
    if user:
        hashed_pass = md5.new(clear_password).hexdigest()
        if hashed_pass == user['password']:
            connection = True
    if connection :
        session.permanent = True
        session['nickname'] = nickname
        session['password'] = clear_password
    else:
        session.clear()
    return redirect(redirect_url)

@app.route('/login', methods=['POST'])
def login():
    return do_login(request.form.get('nickname'), request.form.get('password'), request.form.get('redirect'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    print(request.form)
    if(request.method == 'POST'):
        champs = [
            'nickname',
            'password',
            'password_confirm'
        ]
        result = validate(request.form, champs)
        print result
        if result['valid']:
            #résultat valide
            if not models.user.exist(request.form.get('nickname')):
                #le nickname n'existe pas déjà
                models.user.create(request.form.get('nickname'), md5.new(request.form.get('password')).hexdigest())
                session.permanent = True
                session['nickname'] = request.form.get('nickname')
                session['password'] = request.form.get('password')
                print('session ajoutée')
                return redirect(request.form.get('redirect'))
            else:
                result['errors']['nickname'] = 'Le nickname existe déjà !'.decode('utf-8')
        print(result['errors'])
        return render_template('register.html', redirect=request.form['redirect'], form=result['form'], errors=result['errors'])
    return render_template('register.html')

def validate(form, champs):
    result = {'valid': True, 'form': form, 'errors': {}}
    for champ in champs:
        result['valid'] = result['valid'] and champ_requis(form, champ, errors=result['errors'])
        #if(champ == 'nickname'):
        #    result['form'][champ] = champ
        #else:
        #    result['form'][champ] = ''
    return result

def champ_requis(form, champ, errors):
    if form.get(champ, '') == '':
        errors[champ] = 'le champ {} est requis'.format(champ)
        return False
    else:
        return True

@app.route('/threads/<thread_id>', methods=['GET'])
def thread(thread_id):
    print('ok')
    return render_template('thread.html', nav = models.board.get_nav(None, thread_id), thread=models.thread.get_full(thread_id))

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(request.form['redirect'])

@app.route('/post/<what>/<id>', methods=['POST'])
def post(what, id):
    if(session):
        user = models.user.get_by_name(session['nickname'])
        if(user):
            if not(models.user.check_connect(session['nickname'], md5.new(session['password']).hexdigest())):
                session.clear()
            else:
                print(request.form)
                #uploaded_files = request.files.getlist("file[]")
                #next_post = models.post.get_max
                #for file, index in enumerate(request.files.getlist('file')):
                #                    if(file.filename != ''):
                #                        filename = secure_filename(file.filename)
                
                timestamp = int(time.time())
                if(what == 'thread'):
                    #ici vérifier les input
                    models.thread.create(
                        id,
                        request.form['title'],
                        request.form['content'],
                        user['id'],
                        timestamp)
                elif(what == 'reply'):
                    models.post.create(
                        id, 
                        request.form['content'], 
                        user['id'],
                        timestamp)
        else:
            #l'utilisateur n'existe plus
            session.clear()

    return redirect(request.form['redirect'])

@app.route('/boards/<boardname>', methods=['GET'])
def navboard(boardname):
    if(session):
        print('session ok')
        if not(models.user.check_connect(session['nickname'], md5.new(session['password']).hexdigest())):
            session.clear()
    else:
        print('no session')
    return render_template(
        'board.html',
        nav = models.board.get_nav(boardname, None),
        threads = models.thread.get_threads_review(boardname, 20, 3))

@app.route('/')
def root():
    return redirect('/boards/{}'.format(models.board.get_random_board()))

#@app.route('/create_post', methods=['GET', 'POST'])
#def create_post():
#    champs = [
#        'titre',
#        'contenu'
#    ]
#
#    if request.method == 'GET':
#        return render_template('post.html', champs=champs, form={}, errors={})
#    else:
#        form = request.form
#        result =  validate(form, champs)
#
#        if result['valid']:
#            user = models.User.get_user('toot')
#            models.Post.insert('toot', result['form']['titre'], result['form']['contenu'])
#            return redirect('/')
#
#        else:
#            return render_template('post.html',
#                                   champs=champs,
#                                   form=result['form'],
#                                   errors=result['errors'])
#
#
#def validate(form, champs):
#    result = {'valid': True, 'form': form, 'errors': {}}
#    for champ in champs:
#        result['valid'] = result['valid'] and champ_requis(form, champ, errors=result['errors'])
#
#    return result
#
#def champ_requis(form, champ, errors):
#    if form.get(champ, None) == '':
#        errors[champ] = 'le champ {} est requis'.format(champ)
#        return False
#    else:
#        return True
