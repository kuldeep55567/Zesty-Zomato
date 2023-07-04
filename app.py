from flask import Flask,render_template,request,redirect,g
app = Flask(__name__)
import sqlite3
DATABASE = 'database/zesty_zomato.db'
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn
@app.teardown_appcontext
def close_db_connection(exception):
    conn = getattr(g, '_database', None)
    if conn is not None:
        conn.close()
def create_menu_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            availability BOOLEAN NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
create_menu_table()

def create_orders_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS order_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            dish_id INTEGER,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (dish_id) REFERENCES menu (id)
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/admin')
def admin():
    conn = get_db_connection()
    status_filter = request.args.get('statusFilter')
    if status_filter and status_filter != 'all':
        orders = conn.execute('SELECT * FROM orders WHERE status = ?', (status_filter,)).fetchall()
    else:
        orders = conn.execute('SELECT * FROM orders').fetchall()
    orders_list = []
    for order in orders:
        dish_ids = order['dish_ids'].split(',')
        total_price = 0.0
        for dish_id in dish_ids:
            dish = conn.execute('SELECT * FROM menu WHERE id = ?', (dish_id,)).fetchone()
            if dish:
                total_price += dish['price']
        order_dict = dict(order)
        order_dict['total_price'] = total_price
        orders_list.append(order_dict)
    conn.close()
    return render_template('admin.html', orders=orders_list)



@app.route('/add_dish', methods=['POST'])
def add_dish():
    name = request.form['name']
    price = float(request.form['price'])
    availability = int(request.form['availability'])
    conn = get_db_connection()
    conn.execute('INSERT INTO menu (name, price, availability) VALUES (?, ?, ?)', (name, price, availability))
    conn.commit()
    conn.close()
    return redirect('/admin')


@app.route('/remove_dish', methods=['POST'])
def remove_dish():
    dish_id = request.form['dish_id']   
    conn = get_db_connection()
    conn.execute('DELETE FROM menu WHERE id = ?', (dish_id,))
    conn.commit()
    conn.close() 
    return redirect('/admin')


@app.route('/place_order', methods=['POST'])
def place_order():
    customer_name = request.form['customer_name']
    dish_ids = request.form.getlist('dish_ids[]')
    dish_ids_string = ','.join(dish_ids)
    conn = get_db_connection()
    conn.execute('INSERT INTO orders (customer_name, dish_ids, status) VALUES (?, ?, ?)',
                 (customer_name, dish_ids_string, 'received'))
    conn.commit()
    conn.close()
    return redirect('/admin')



@app.route('/update_status', methods=['POST'])
def update_status():
    order_id = request.form['order_id']
    new_status = request.form['new_status']
    conn = get_db_connection()
    conn.execute('UPDATE orders SET status = ? WHERE id = ?', (new_status, order_id))
    conn.commit()
    conn.close()
    return redirect('/admin')


@app.route('/menu', methods=['GET'])
def menu():
    conn = get_db_connection()
    menu = conn.execute('SELECT * FROM menu').fetchall()
    conn.close()
    return render_template('menu.html', menu=menu)

if __name__ == '__main__':
    app.run(debug=True)