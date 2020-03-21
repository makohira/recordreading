from flask import Flask, render_template, request, escape, session, redirect
from checker import check_logged_in
from hashlib import sha256
from DBcm import UseDatabase

app = Flask(__name__)

app.config['dbconfig'] = {'host': 'private.2fesw.tyo2.database-hosting.conoha.io',
                          'user': '2fesw_rruser',
                          'password': 'passwd4rruser@DB',
                          'database': '2fesw_record_reading', }
appdir = '/recordreading'
@app.route(appdir + '/hello')
def hello() -> str:
    return 'hello'

@app.route(appdir + '/index.html')
@app.route(appdir + '/')
@check_logged_in
def mainpage() -> 'html':
    book_list = []
    with UseDatabase(app.config['dbconfig']) as db:
        _SQL = """
                   SELECT
                          id, name 
                     FROM
                          books
                    WHERE
                          user_id = %s 
                 ORDER BY
                          created_at DESC;
               """
        db.cursor.execute(_SQL,(session['user_id'],))
        book_list = [{'id': book[0], 'name': book[1]} for book in db.cursor.fetchall()]
    return render_template('mainpage.html', 
        the_title='読書記録',
        app_dir=appdir,
        user_name=session['user_name'],
        list_size=20,
        books = book_list)


@app.route(appdir + '/newnote')
@check_logged_in
def new_note() -> str:
    session['book_id'] = 0
    return render_template('editnote.html', app_dir=appdir)


@app.route(appdir + '/editnote', methods=['POST'])
@check_logged_in
def edit_note() -> str:
    input_book_id = request.form.get('book')
    input_read_at = ''
    if input_book_id:
        session['book_id'] = int(input_book_id)
    else:
        session['book_id'] = 0
        return render_template('editnote.html',app_dir=appdir)
    
    with UseDatabase(app.config['dbconfig']) as db:
        _SQL = """
                   SELECT
                          name, read_at 
                     FROM
                          books 
                    WHERE
                          id = %s 
               """
        db.cursor.execute(_SQL, (session['book_id'],))
        res = db.cursor.fetchone()
        if res:
            name = res[0]
            input_read_at = res[1]
        
        # Kデータの取得
        k_list = []
        _SQL = """
                   SELECT
                          memo 
                     FROM
                          notes 
                    WHERE
                              book_id = %s 
                          AND category = '1' 
                 ORDER BY
                          row_no ASC;
               """
        db.cursor.execute(_SQL, (session['book_id'],))
        k_list = [book[0] for book in db.cursor.fetchall()]

        # Wデータの取得
        w_list = []
        _SQL = """
                   SELECT
                          memo 
                     FROM
                          notes 
                    WHERE
                              book_id = %s 
                          AND category = '2' 
                 ORDER BY
                          row_no ASC;
               """
        db.cursor.execute(_SQL, (session['book_id'],))
        w_list = [book[0] for book in db.cursor.fetchall()]

        # Lデータの取得
        l_list = []
        _SQL = """
                   SELECT
                          memo 
                     FROM
                          notes 
                    WHERE
                              book_id = %s 
                          AND category = '3' 
                 ORDER BY
                          row_no ASC;
               """
        db.cursor.execute(_SQL, (session['book_id'],))
        l_list = [book[0] for book in db.cursor.fetchall()]
        return render_template('editnote.html', 
                                app_dir=appdir,
                                book_name=name,
                                read_at=input_read_at,
                                ks=k_list,
                                ws=w_list,
                                ls=l_list)


@app.route(appdir + '/updatenote', methods=['POST'])
@check_logged_in
def update_note() -> str:
    with UseDatabase(app.config['dbconfig']) as db:
        # 旧データ削除
        _SQL = """ DELETE FROM notes WHERE book_id = %s """
        db.cursor.execute(_SQL, (session['book_id'],))
        db.conn.commit()

        # データ登録
        # 書籍データ
        if session['book_id'] == 0:
            _SQL = """ INSERT INTO books(user_id, name, created_at, read_at) VALUES(%s, %s, now(), %s);"""
            db.cursor.execute(_SQL, (session['user_id'],request.form['bookName'], request.form['inputReadAt'],))
            db.conn.commit()
            session['book_id'] = db.cursor.lastrowid
        else:
            _SQL = """ UPDATE books SET name = %s, updated_at = now(), read_at = %s WHERE id = %s;"""
            db.cursor.execute(_SQL, (request.form['bookName'], request.form['inputReadAt'], session['book_id'],))
            db.conn.commit()
                
        # Kデータ
        k_data = request.form['noteForK']
        if k_data:
            for i, k in enumerate(str(k_data).splitlines()):
                _SQL = """
                           INSERT INTO
                                       notes(book_id, category, row_no, memo, created_at) 
                                VALUES
                                       (%s, '1', %s, %s, now());
                       """
                db.cursor.execute(_SQL,(session['book_id'], i, k,))
        
        # Wデータ
        w_data = request.form['noteForW']
        if w_data:
            for i, w in enumerate(str(w_data).splitlines()):
                _SQL = """
                           INSERT INTO
                                       notes(book_id, category, row_no, memo, created_at) 
                                VALUES
                                       (%s, '2', %s, %s, now());
                       """
                db.cursor.execute(_SQL,(session['book_id'], i, w,))
        
        # Lデータ
        l_data = request.form['noteForL']
        if l_data:
            for i, l in enumerate(str(l_data).splitlines()):
                _SQL = """
                           INSERT INTO
                                       notes(book_id, category, row_no, memo, created_at) 
                                VALUES
                                       (%s, '3', %s, %s, now());
                       """
                db.cursor.execute(_SQL,(session['book_id'], i, l,))
    return redirect(appdir + '/')

@app.route(appdir + '/login', methods=['POST'])
def do_login() -> str:
    with UseDatabase(app.config['dbconfig']) as db:
        _SQL = """
                  SELECT 
                         id, name, password 
                    FROM 
                         users
                   WHERE 
                         email = %s;
               """
        db.cursor.execute(_SQL, (request.form['email'],))
        result = db.cursor.fetchone()
        if not result is None:
            user_id, user_name, pwd = result
            if sha256(str(request.form['password']).encode()).hexdigest() == pwd:
                session['logged_in'] = True
                session['user_id'] = user_id
                session['user_name'] = user_name
                return redirect(appdir + '/')
            else:
                return render_template('login.html', the_title='読書記録', app_dir=appdir, login_fail='ログインに失敗しました。')
        else:
            return render_template('login.html', the_title='読書記録', app_dir=appdir, login_fail='ログインに失敗しました。')
    return redirect(appdir + '/')

@app.route(appdir + '/logout')
def do_logout() -> str:
    if 'logged_in' in session:
        session.pop('logged_in')
    if 'user_id' in session:
        session.pop('user_id')
    if 'user_name' in session:
        session.pop('user_name')
    return redirect(appdir + '/')


app.secret_key = 'YouWillNeverGuessThisRnSecretKey'

if __name__ == '__main__':
    app.run(host='0.0.0.0')
