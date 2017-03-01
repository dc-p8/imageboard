# coding=utf-8
from __future__ import absolute_import
import sqlite3
from flask import g

def connect_db():
    conn = sqlite3.connect('data.db')
    # la doc de sqlite3 dit que les foreign_keys sont désactivés par défaut et qu'il faut les avtiver
    # pour CHAQUE nouvelle connexion à la base de données.
    # Si on le fait pas, le retour de 'PRAGMA foreign_keys' est 0 même si on l'a mit en ON dans le .sql
    conn.execute('PRAGMA foreign_keys=ON;') 
    return conn

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

######################################
# Class board
##################
class board(object):
    # l'object nav de la view en fonction du nom ()
    @classmethod
    def get_nav(cls, boardname, thread_id):
        return {
            'board_current':board.get_board(boardname, thread_id),
            'board_list':board.get_boards()}
    # nom d'une board aléatoire
    @classmethod
    def get_random_board(cls):
        db = get_db()
        cur = db.execute("""SELECT name
            FROM board
            ORDER BY RANDOM()
            LIMIT 1""")
        result = cur.fetchone()
        return result[0]

    # toutes les boards (nom et description)
    @classmethod
    def get_boards(cls):
        db = get_db()
        cur = db.execute("""
            SELECT name, description
            FROM board""")
        result = cur.fetchall()
        return [{
            'name':board[0],
            'description':board[1]}for board in result]

    # l'object board_current de la view en fonction de son nom ou d'un de ses thread
    @classmethod
    def get_board(cls, boardname, thread_id):
        db = get_db()
        if(thread_id is not None):
            cur = db.execute("""
                SELECT b.name, b.description, b.id
                FROM board b
                INNER JOIN thread t ON t.board_id = b.id
                WHERE t.id = ?""", [thread_id])
        else:
            cur = db.execute("""
                SELECT b.name, b.description, b.id
                FROM board b
                WHERE b.name=?""", [boardname])
        result = cur.fetchone()
        return {
            'name':result[0],
            'description':result[1],
            'id':result[2]} 


######################################
# Class file
##################
class file(object):
    @classmethod
    def get_files(cls, post_id):
        db = get_db()
        cur = db.execute("""
            SELECT f.id, f.name
            FROM file f
            WHERE f.post_id = ?
            ORDER BY f.name""", [post_id])
        result = cur.fetchall()
        return [{
            'id':file[0],
            'name':file[1]} for file in result]


######################################
# Class post
##################
class post(object):
    # créer une réponse
    @classmethod
    def create(cls, thread_id, content, user_id, time_created):
        db = get_db()
        cur = db.execute("""
            INSERT INTO post (content, time_created, thread_id, user_id)
            VALUES (?, ?, ?, ?)""", [content, time_created, thread_id, user_id])
        db.commit()
    # obtenir les infos d'un post
    @classmethod
    def get_post(cls, postid):
        db = get_db()
        cur = db.execute("""
            SELECT u.name, p.content, p.time_created, p.time_modified
            FROM post p
            INNER JOIN user u ON u.id = p.user_id
            WHERE p.id=?""", [postid])
        result = cur.fetchone()
        if result:
            result = {
                'id': postid,
                'nickname': result[0],
                'content': result[1],
                'time_created': result[2],
                'time_modified': result[3],
                'files': file.get_files(postid)}
        return result
    # obtenir toutes les réponses d'un thread 
    @classmethod
    def get_posts(cls, thread_id):
        db=get_db()
        cur = db.execute("""
            SELECT p.id, u.name, p.content, p.time_created, p.time_modified
            FROM post p
            INNER JOIN user u ON u.id = p.user_id
            WHERE p.thread_id = ?
            ORDER BY p.time_created ASC""", [thread_id])
        result = cur.fetchall()
        return [{
            'id': _post[0],
            'nickname':_post[1],
            'content':_post[2],
            'time_created':_post[3],
            'time_modified':_post[4]} for _post in result]
    # liste des posts d'un thread en mode review (premier et derniers posts seulement)
    @classmethod
    def get_posts_review(cls, author_post_id, thread_id, n):
        db = get_db()
        author_post = post.get_post(author_post_id)
        cur = db.execute("""
            SELECT *
            FROM(
                SELECT p.id, u.name, p.content, p.time_created, p.time_modified
                FROM post p
                INNER JOIN user u ON u.id = p.user_id
                LEFT JOIN thread t ON t.id = ?
                WHERE p.thread_id = ? AND p.id != t.post_id
                GROUP BY p.id
                ORDER BY p.time_created DESC
                LIMIT ?)
            ORDER BY 4 ASC
            """, [thread_id, thread_id, n])
        result = cur.fetchall()
        return [author_post] + [{
            'id': _post[0],
            'nickname':_post[1],
            'content':_post[2],
            'time_created':_post[3],
            'time_modified':_post[4]}for _post in result]

######################################
# Class thread
##################
class thread(object):
    # liste des thread d'une board en mode review (threads actualisés récement d'abord)
    @classmethod
    def get_threads_review(cls, boardname, n_threads, n_replies):
        db = get_db()
        cur = db.execute("""
            SELECT t.id, t.post_id, t.title, COUNT()
            FROM thread t
            JOIN board b ON b.id = t.board_id
            JOIN post p ON p.thread_id = t.id
            WHERE b.name = ?
            GROUP BY t.post_id
            ORDER BY p.time_created DESC
            LIMIT ?""", [boardname, n_threads])
        result = cur.fetchall()
        return [{
            'id':_thread[0],
            'title':_thread[2],
            'nb_replies':_thread[3],
            'posts':post.get_posts_review(_thread[1], _thread[0], n_replies)}for _thread in result]
    # toutes les infos d'un thread
    @classmethod
    def get_full(cls, thread_id):
        db = get_db()
        cur = db.execute("""
            SELECT t.title, COUNT()
            FROM thread t
            WHERE t.id = ?
            """, [thread_id])
        result = cur.fetchone()
        return {
            'id':thread_id,
            'title':result[0],
            'nb_replies':result[1],
            'posts':post.get_posts(thread_id)}
    # créer un nouveau thread 
    # la difficulté étant qu'il faut insérer dans deux tables réciproquement liés par des foreign_keys
    # selon la doc, si le champ vaut null (on ne précise pas de valeur, il n'y a pas de valeur par défaut), la FK n'a pas besoin d'être respectée
    @classmethod
    def create(cls, board_id, title, content, user_id, time):
        db = get_db()
        #d'abord créer le post pour avoir son ID
        cur = db.execute("""
            INSERT INTO post (content, time_created, user_id)
            VALUES(?, ?, ?)""", [content, time, user_id])
        db.commit()
        post_id = cur.lastrowid
        print('DERNIER POST : ' + str(post_id))
        cur = db.execute("""
            INSERT INTO thread (title, post_id, board_id)
            VALUES(?, ?, ?)""", [title, post_id, board_id])
        db.commit()
        thread_id = cur.lastrowid
        print('DERNIER THREAD : ' + str(thread_id))
        db.execute("""
            UPDATE post
            SET thread_id = ?
            WHERE id=?""", [thread_id, post_id])
        db.commit()

######################################
# Class user
##################
class user(object):
    # les infos d'un user en fonction de son pseudo
    @classmethod
    def get_by_name(cls, nickname):
        db = get_db()
        cur = db.execute("""
            SELECT u.id, u.password
            FROM user u
            WHERE u.name=?""", [nickname])
        result = cur.fetchone()
        if result :
            return {'id':result[0], 'password':result[1]}
        return None
    # renvoit vrai si le mot de passe correspond au pseudo
    @classmethod
    def check_connect(cls, nickname, hashed_password):
        db = get_db()
        cur = db.execute("""
            SELECT u.id
            FROM user u
            WHERE u.name = ? AND u.password = ?""", [nickname, hashed_password])
        return cur.fetchone() is not None
    # vérifie si l'utilisateur existe
    @classmethod
    def exist(cls, nickname):
        db = get_db()
        cur = db.execute("""
            SELECT u.id
            FROM user u
            WHERE u.name = ?""", [nickname])
        return cur.fetchone() is not None
    # inscription d'un utilisateur
    @classmethod
    def create(cls, nickname, hashed_password):
        db = get_db()
        cur = db.execute("""
            INSERT INTO user (name, password)
            VALUES (?, ?)
            """, [nickname, hashed_password])
        db.commit()