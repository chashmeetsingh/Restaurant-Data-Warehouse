from flask import Flask, render_template, request
import mysql.connector
import pymongo
import json
import dateutil.parser
from datetime import datetime
from bson.objectid import ObjectId

app = Flask(__name__)

# SDB 1 Connection
mysqlConnection = mysql.connector.connect(
    host="localhost",
    user="chashmeet",
    passwd="password",
    auth_plugin='mysql_native_password',
    database='sdb1'
)
sdb1Cursor = mysqlConnection.cursor()

# SDB 2 Connection
mongoClient = pymongo.MongoClient("mongodb://localhost:27017/")
sdb2 = mongoClient["sdb2"]

# Data Warehouse Connection
dwConnection = mysql.connector.connect(
    host="localhost",
    user="chashmeet",
    passwd="password",
    auth_plugin='mysql_native_password',
    database='data_warehouse'
)
dwCursor = dwConnection.cursor()

weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

@app.route("/updateData")
def updateData():

    # Truncate Data
    dwCursor.execute("TRUNCATE TABLE DIM_GUEST")
    dwCursor.execute("TRUNCATE TABLE DIM_RESTAURANT")
    dwCursor.execute("TRUNCATE TABLE DIM_RESERVATION")
    dwCursor.execute("TRUNCATE TABLE dw_fact")

    # Transform Data

    # Get Reservations from SDB1
    sdb1Cursor.execute("SELECT * FROM reservations")
    reservationsSDB1 = sdb1Cursor.fetchall()

    for reservation in reservationsSDB1:
        # print(reservation[1])

        sdb1Cursor.execute("SELECT * FROM GUEST WHERE gid = " + str(reservation[0]))
        guest = sdb1Cursor.fetchall()[0]

        sdb1Cursor.execute("SELECT * FROM RESTAURANT WHERE RID = " + str(reservation[1]))
        restaurant = sdb1Cursor.fetchall()[0]

        # print(guest, restaurant, reservation)
        # print(reservation[3].day, reservation[3].month, reservation[3].year, reservation[3].weekday())

        # return

        try:
            sql = "INSERT INTO DIM_GUEST (gid, name, phone) VALUES(%s, %s, %s)"
            values = (guest[0], guest[1], guest[2])
            dwCursor.execute(sql, values)
            dwConnection.commit()
        except mysql.connector.Error as e:
            print("dim_guest1 issue " + str(e))
            pass

        try:
            sql = "INSERT INTO DIM_RESTAURANT (rid, genre, region, name) VALUES(%s, %s, %s, %s)"
            values = (restaurant[0], restaurant[1], restaurant[2], restaurant[3])
            dwCursor.execute(sql, values)
            dwConnection.commit()
        except mysql.connector.Error as e:
            print("dim_restaurant1 issue " + str(e))
            pass

        try:
            sql = "INSERT INTO DIM_RESERVATION (guest_count, amount_spent) VALUES(%s, %s)"
            values = (reservation[4], reservation[2])
            dwCursor.execute(sql, values)
            dwConnection.commit()
            reserve_id = dwCursor.lastrowid
        except mysql.connector.Error as e:
            print("dim_reservation1 issue " + str(e))
            pass

        try:
            q = ""
            month = reservation[3].month
            if month >= 1 and month <= 3:
                q = "Quarter 1"
            elif month >= 4 and month <= 6:
                q = "Quarter 2"
            elif month >= 7 and month <= 9:
                q = "Quarter 3"
            else:
                q = "Quarter 4"
            sql = "INSERT INTO DIM_DATE (date, month, year, weekday, quarter) VALUES (%s, %s, %s, %s, %s)"
            values = (reservation[3].day, reservation[3].month, reservation[3].year, weekdays[reservation[3].weekday()], q)
            dwCursor.execute(sql, values)
            dwConnection.commit()
        except mysql.connector.Error as e:
            print("dw_fact1 issue " + str(e))
            pass

        try:

            sql = "INSERT INTO dw_fact (gid, rid, did, points, reserve_id) VALUES(%s, %s, %s, %s, %s)"
            values = (reservation[0], reservation[1], dwCursor.lastrowid, reservation[2], reserve_id)
            dwCursor.execute(sql, values)
            dwConnection.commit()
        except mysql.connector.Error as e:
            print("dw_fact1 issue " + str(e))
            pass

        # break

    # Get reservations from SDB2

    reservationCollection = sdb2["reservation"].find({})
    for reservation in reservationCollection:
        # print(reservation)
        guest = sdb2["guest"].find_one({ "_id": reservation["gid"] })
        # print(guest)
        restaurant = sdb2["restaurant"].find_one({ "_id": reservation["rid"] })
        # print(restaurant)

        try:
            sql = "INSERT INTO DIM_GUEST (gid, name, phone) VALUES(%s, %s, %s)"
            values = (str(guest["_id"]), str(guest["name"]), str(guest["phone_number"]))
            dwCursor.execute(sql, values)
            dwConnection.commit()
        except mysql.connector.Error as e:
            print("dim_guest2 issue " + str(e))
            pass

        try:
            sql = "INSERT INTO DIM_RESTAURANT (rid, genre, region, name) VALUES(%s, %s, %s, %s)"
            values = (str(restaurant["_id"]), str(restaurant["genre"]), str(restaurant["region"]), str(restaurant["name"]))
            dwCursor.execute(sql, values)
            dwConnection.commit()
        except mysql.connector.Error as e:
            print("dim_restaurant2 issue " + str(e))
            pass

        try:
            sql = "INSERT INTO DIM_RESERVATION (guest_count, amount_spent) VALUES(%s, %s)"
            values = (str(reservation["guest_count"]), str(reservation["amount_spent"]))
            dwCursor.execute(sql, values)
            reserve_id = dwCursor.lastrowid
            dwConnection.commit()
        except mysql.connector.Error as e:
            print("dim_reservation2 issue " + str(e))
            pass

        try:
            sql = "INSERT INTO DIM_DATE (date, month, year, weekday, quarter) VALUES (%s, %s, %s, %s, %s)"
            q = ""
            if reservation["transaction_date"].month >= 1 and reservation["transaction_date"].month <= 3:
                q = "Quarter 1"
            elif reservation["transaction_date"].month >= 4 and reservation["transaction_date"].month <= 6:
                q = "Quarter 2"
            elif reservation["transaction_date"].month >= 7 and reservation["transaction_date"].month <= 9:
                q = "Quarter 3"
            else:
                q = "Quarter 4"
            values = (reservation["transaction_date"].day, reservation["transaction_date"].month,
                      reservation["transaction_date"].year, weekdays[reservation["transaction_date"].weekday()], q)
            dwCursor.execute(sql, values)
            dwConnection.commit()
        except mysql.connector.Error as e:
            print("dw_fact2 issue " + str(e))
            pass

        try:

            sql = "INSERT INTO dw_fact (gid, rid, did, points, reserve_id) VALUES(%s, %s, %s, %s, %s)"
            values = (str(reservation["gid"]), str(reservation["rid"]), dwCursor.lastrowid, str(reservation["amount_spent"]), reserve_id)
            dwCursor.execute(sql, values)
            dwConnection.commit()
        except mysql.connector.Error as e:
            print("dw_fact2 issue " + str(e))
            pass

        # break

    return render_template("home.html")

@app.route("/add1")
def add1():
    sdb1Cursor.execute("SELECT * FROM guest")
    guestsData = sdb1Cursor.fetchall()
    guests = [guest[0] for guest in guestsData]
    # print guests

    sdb1Cursor.execute("SELECT * FROM restaurant")
    restaurantsData = sdb1Cursor.fetchall()
    restaurants = [restaurant[0] for restaurant in restaurantsData]
    # print guests

    return render_template("add1.html", guests=guests, restaurants=restaurants)

@app.route("/add2")
def add2():
    guestsData = sdb2["guest"].find({})
    guests = [str(guest["_id"]) for guest in guestsData]
    # print guests

    restaurantsData = sdb2["restaurant"].find({})
    restaurants = [str(restaurant["_id"]) for restaurant in restaurantsData]
    # print restaurants

    return render_template("add2.html", guests=guests, restaurants=restaurants)

@app.route("/sdb1_add_guest")
def sdb1_add_guest():
    print request.args.get('name'), request.args.get('phone_number')
    try:
        name = request.args.get('name')
        phone = request.args.get('phone_number')
        sql = "INSERT INTO guest (name, phone, points) VALUES (%s, %s, %s)"
        data = (name, phone, 0)
        sdb1Cursor.execute(sql, data)
        mysqlConnection.commit()

        sql = "INSERT INTO DIM_GUEST (gid, name, phone) VALUES(%s, %s, %s)"
        values = (sdb1Cursor.lastrowid, name, phone)
        dwCursor.execute(sql, values)
        dwConnection.commit()

        return "true"
    except mysql.connector.Error as e:
        print("dim_guest1 issue " + str(e))
        return "false"

@app.route("/sdb1_add_restaurant")
def sdb1_add_restaurant():
    print request.args.get('name'), request.args.get('region'), request.args.get('genre')
    try:
        name = request.args.get('name')
        region = request.args.get('region')
        genre = request.args.get('genre')
        sql = "INSERT INTO restaurant (genre, region, name) VALUES (%s, %s, %s)"
        data = (genre, region, name)
        sdb1Cursor.execute(sql, data)
        mysqlConnection.commit()

        sql = "INSERT INTO DIM_RESTAURANT (rid, genre, region, name) VALUES(%s, %s, %s, %s)"
        values = (sdb1Cursor.lastrowid, genre, region, name)
        dwCursor.execute(sql, values)
        dwConnection.commit()

        return "true"
    except mysql.connector.Error as e:
        print("dim_restaurant1 issue " + str(e))
        return "false"

@app.route("/sdb1_add_reservation")
def sdb1_add_reservation():
    print request.args.get('guest_count'), request.args.get('amt_spent'), request.args.get('gid'), request.args.get('rid'), request.args.get('date')
    try:

        guest_count = request.args.get('guest_count')
        amt_spent = request.args.get('amt_spent')
        gid = request.args.get('gid')
        rid = request.args.get('rid')
        date = request.args.get('date')

        sql = "SELECT * from guest where gid = " + gid
        sdb1Cursor.execute(sql)
        data = sdb1Cursor.fetchall()
        # print data
        points = data[0][3]
        # print points, amt_spent
        points += int(amt_spent)

        sql = "UPDATE guest SET points = " + str(points)
        sdb1Cursor.execute(sql)
        mysqlConnection.commit()

        data = (gid, rid, amt_spent, datetime.strptime(date, '%b %d, %Y'), guest_count)
        sql = "INSERT INTO reservations (gid, rid, amt_spent, date, guest_count) VALUES (%s, %s, %s, %s, %s)"
        sdb1Cursor.execute(sql, data)
        mysqlConnection.commit()

        try:
            sql = "INSERT INTO DIM_RESERVATION (guest_count, amount_spent) VALUES(%s, %s)"
            values = (guest_count, amt_spent)
            dwCursor.execute(sql, values)
            dwConnection.commit()
            reserve_id = dwCursor.lastrowid
        except mysql.connector.Error as e:
            print("dim_reservation1 issue " + str(e))
            pass

        try:
            q = ""
            month = datetime.strptime(date, '%b %d, %Y').month
            if month >= 1 and month <= 3:
                q = "Quarter 1"
            elif month >= 4 and month <= 6:
                q = "Quarter 2"
            elif month >= 7 and month <= 9:
                q = "Quarter 3"
            else:
                q = "Quarter 4"
            sql = "INSERT INTO DIM_DATE (date, month, year, weekday, quarter) VALUES (%s, %s, %s, %s, %s)"
            values = (datetime.strptime(date, '%b %d, %Y').day, datetime.strptime(date, '%b %d, %Y').month, datetime.strptime(date, '%b %d, %Y').year, weekdays[datetime.strptime(date, '%b %d, %Y').weekday()], q)
            dwCursor.execute(sql, values)
            dwConnection.commit()
        except mysql.connector.Error as e:
            print("dw_fact1 issue " + str(e))
            pass

        try:
            sql = "INSERT INTO dw_fact (gid, rid, did, points, reserve_id) VALUES(%s, %s, %s, %s, %s)"
            values = (gid, rid, dwCursor.lastrowid, amt_spent, reserve_id)
            dwCursor.execute(sql, values)
            dwConnection.commit()
        except mysql.connector.Error as e:
            print("dw_fact1 issue " + str(e))
            pass

        return "true"
    except mysql.connector.Error as e:
        print("dim_reservation1 issue " + str(e))
        return "false"

@app.route("/sdb2_add_guest")
def sdb2_add_guest():
    print request.args.get('name'), request.args.get('phone_number')

    try:
        name = request.args.get('name')
        phone = request.args.get('phone_number')
        guestCollection = sdb2["guest"]
        guest = guestCollection.insert({
            'name': name,
            'phone_number': phone,
            'points_earned': 0
        })

        sql = "INSERT INTO DIM_GUEST (gid, name, phone) VALUES(%s, %s, %s)"
        values = (str(guest), name, phone)
        dwCursor.execute(sql, values)
        dwConnection.commit()

        return "true"
    except Exception as e:
        print("dim_guest2 issue " + str(e))
        return "false"

@app.route("/sdb2_add_restaurant")
def sdb2_add_restaurant():
    print request.args.get('name'), request.args.get('region'), request.args.get('genre')
    try:
        name = request.args.get('name')
        region = request.args.get('region')
        genre = request.args.get('genre')
        restaurantCollection = sdb2["restaurant"]
        restaurant = restaurantCollection.insert({
            "genre": genre,
            "region": region,
            "name": name
        })

        sql = "INSERT INTO DIM_RESTAURANT (rid, genre, region, name) VALUES(%s, %s, %s, %s)"
        values = (str(restaurant), genre, region, name)
        dwCursor.execute(sql, values)
        dwConnection.commit()

        return "true"
    except mysql.connector.Error as e:
        print("dim_restaurant1 issue " + str(e))
        return "false"

@app.route("/sdb2_add_reservation")
def sdb2_add_reservation():
    print request.args.get('guest_count'), request.args.get('amt_spent'), request.args.get('gid'), request.args.get('rid'), request.args.get('date')
    try:

        guest_count = request.args.get('guest_count')
        amt_spent = request.args.get('amt_spent')
        gid = request.args.get('gid')
        rid = request.args.get('rid')
        date = request.args.get('date')

        guestCollection = sdb2["guest"]
        cursor = guestCollection.find({"_id": ObjectId(gid)})

        for guest in cursor:
            # print guest
            guestCollection.update_one({"_id": ObjectId(gid)},
                                       {"$set": {"points_earned": str(int(amt_spent) + int(guest["points_earned"]))}})
            break

        reservationCollection = sdb2["reservation"]
        reservation = reservationCollection.insert({
            "gid": gid,
            "rid": rid,
            "amount_spent": amt_spent,
            "transaction_date": datetime.strptime(date, '%b %d, %Y'),
            "guest_count": guest_count
        })

        try:
            sql = "INSERT INTO DIM_RESERVATION (guest_count, amount_spent) VALUES(%s, %s)"
            values = (guest_count, amt_spent)
            dwCursor.execute(sql, values)
            dwConnection.commit()
            reserve_id = dwCursor.lastrowid
        except mysql.connector.Error as e:
            print("dim_reservation1 issue " + str(e))
            return "false"

        try:
            q = ""
            month = datetime.strptime(date, '%b %d, %Y').month
            if month >= 1 and month <= 3:
                q = "Quarter 1"
            elif month >= 4 and month <= 6:
                q = "Quarter 2"
            elif month >= 7 and month <= 9:
                q = "Quarter 3"
            else:
                q = "Quarter 4"
            sql = "INSERT INTO DIM_DATE (date, month, year, weekday, quarter) VALUES (%s, %s, %s, %s, %s)"
            values = (datetime.strptime(date, '%b %d, %Y').day, datetime.strptime(date, '%b %d, %Y').month, datetime.strptime(date, '%b %d, %Y').year, weekdays[datetime.strptime(date, '%b %d, %Y').weekday()], q)
            dwCursor.execute(sql, values)
            dwConnection.commit()
        except mysql.connector.Error as e:
            print("dw_fact1 issue " + str(e))
            return "false"

        try:
            sql = "INSERT INTO dw_fact (gid, rid, did, points, reserve_id) VALUES(%s, %s, %s, %s, %s)"
            values = (str(gid), str(rid), dwCursor.lastrowid, amt_spent, reserve_id)
            dwCursor.execute(sql, values)
            dwConnection.commit()
        except mysql.connector.Error as e:
            print("dw_fact1 issue " + str(e))
            return "false"

        return "true"
    except mysql.connector.Error as e:
        print("dim_reservation1 issue " + str(e))
        return "false"

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/dw")
def render_dw():
    return render_template("dw.html")

@app.route("/sdb1")
def render_sdb1():
    return render_template("sdb1.html")

@app.route("/sdb2")
def render_sdb2():
    return render_template("sdb2.html")

@app.route("/queries")
def queries():
    return render_template("query.html")

@app.route("/query_one")
def query_one():
    query = "Select count(*), restaurant.region, sum(reservation.amount_spent), dim_date.month, dim_date.year from dw_fact dw, dim_guest guest, dim_restaurant restaurant, dim_reservation reservation, dim_date where dw.gid = guest.gid and dw.rid = restaurant.rid and dw.reserve_id = reservation.res_id and dim_date.did = dw.did and dim_date.year = 2018 group by restaurant.region, dim_date.month"
    try:
        dwCursor.execute(query)
        query_data = dwCursor.fetchall()
        data = []
        for q in query_data:
            data.append(({ 'count': q[0], 'region': q[1], 'amount_spent': int(q[2]), 'month': int(q[3]), 'year': int(q[4]) }))
        return json.dumps(data)
    except Exception as e:
        print 'Error:', e
        return e.message

@app.route("/query_two")
def query_two():
    query = "Select count(*), restaurant.region, sum(reservation.amount_spent), dim_date.year, dim_date.quarter from dw_fact dw, dim_guest guest, dim_restaurant restaurant, dim_reservation reservation, dim_date where dw.gid = guest.gid and dw.rid = restaurant.rid and dw.reserve_id = reservation.res_id and dim_date.did = dw.did and dim_date.year = 2018 group by restaurant.region, dim_date.quarter"
    try:
        dwCursor.execute(query)
        query_data = dwCursor.fetchall()
        data = []
        for q in query_data:
            data.append(({ 'count': q[0], 'region': q[1], 'amount_spent': int(q[2]), 'year': int(q[3]), 'quarter': q[4] }))
        return json.dumps(data)
    except Exception as e:
        print 'Error:', e
        return e.message

@app.route("/query_three")
def query_three():
    query = "Select count(*), restaurant.genre, sum(reservation.amount_spent), dim_date.year, dim_date.month from dw_fact dw, dim_restaurant restaurant, dim_reservation reservation, dim_date where dw.rid = restaurant.rid and dw.reserve_id = reservation.res_id and dim_date.did = dw.did and dim_date.year = 2018 group by dim_date.month, restaurant.genre"
    try:
        dwCursor.execute(query)
        query_data = dwCursor.fetchall()
        data = []
        for q in query_data:
            data.append(({ 'count': q[0], 'genre': q[1], 'amount_spent': int(q[2]), 'year': int(q[3]), 'month': q[4] }))
        return json.dumps(data)
    except Exception as e:
        print 'Error:', e
        return e.message

@app.route("/query_four")
def query_four():
    query = "Select count(*), restaurant.genre, sum(reservation.amount_spent), dim_date.year, dim_date.quarter from dw_fact dw, dim_restaurant restaurant, dim_reservation reservation, dim_date where dw.rid = restaurant.rid and dw.reserve_id = reservation.res_id and dim_date.did = dw.did and dim_date.year = 2018 group by dim_date.quarter, restaurant.genre"
    try:
        dwCursor.execute(query)
        query_data = dwCursor.fetchall()
        data = []
        for q in query_data:
            data.append(({ 'count': q[0], 'genre': q[1], 'amount_spent': int(q[2]), 'year': int(q[3]), 'quarter': q[4] }))
        return json.dumps(data)
    except Exception as e:
        print 'Error:', e
        return e.message

@app.route("/query_five")
def query_five():
    query = "select count(*), sum(reservation.amount_spent), dim_date.weekday, restaurant.region from dw_fact dw, dim_restaurant restaurant, dim_reservation reservation, dim_date where dw.rid = restaurant.rid and dw.reserve_id = reservation.res_id and dim_date.did = dw.did and dim_date.year = 2018 group by dim_date.weekday, restaurant.region"
    try:
        dwCursor.execute(query)
        query_data = dwCursor.fetchall()
        data = []
        for q in query_data:
            data.append(({ 'count': q[0], 'amount_spent': int(q[1]), 'weekday': q[2], 'region': q[3] }))
        return json.dumps(data)
    except Exception as e:
        print 'Error:', e
        return e.message

@app.route("/sdb1_execute")
def sdb1_execute():
    query = request.args.get('query')
    print(query)
    try:
        sdb1Cursor.execute(query)
    except mysql.connector.Error as e:
        print("dw_fact2 issue " + str(e))
        return "Invalid query", 500

    cursorData = sdb1Cursor.fetchall()
    # print(len(cursorData))
    data = []
    for d in cursorData:
        if "guest" in query:
            if "*" in query:
                data.append({
                    "gid": d[0],
                    "name": d[1],
                    "phone": d[2],
                    "points": d[3]
                })
            else:
                params = query.split(" ")[1]
                params = params.split(",")
                res = {}

                for i in range(len(params)):
                    res[params[i]] = d[i]
                data.append(res)

        elif "restaurant" in query:
            if "*" in query:
                data.append({
                    "rid": d[0],
                    "genre": d[1],
                    "region": d[2],
                    "name": d[3]
                })
            else:
                params = query.split(" ")[1]
                params = params.split(",")
                res = {}

                for i in range(len(params)):
                    res[params[i]] = d[i]
                data.append(res)

        elif "reservation" in query:
            if "*" in query:
                data.append({
                    "gid": d[0],
                    "rid": d[1],
                    "amt_spent": d[2],
                    "date": d[3].strftime('%b %d, %Y'),
                    "guest_count": d[4]
                })
            else:
                params = query.split(" ")[1]
                params = params.split(",")
                res = {}

                for i in range(len(params)):
                    res[params[i]] = d[i]
                data.append(res)

    return json.dumps(data)

@app.route("/dw_execute")
def dw_execute():
    query = request.args.get('query')
    print(query)
    try:
        dwCursor.execute(query)
    except:
        return "Invalid query", 500

    cursorData = dwCursor.fetchall()
    # print(len(cursorData))
    data = []
    for d in cursorData:
        if "dw_fact" in query:
            if "*" in query:
                data.append({
                    "gid": d[0],
                    "rid": d[1],
                    "did": d[2],
                    "reserve_id": d[3],
                    "points": d[4]
                })
            else:
                params = query.split(" ")[1]
                params = params.split(",")
                res = {}

                for i in range(len(params)):
                    res[params[i]] = str(d[i])
                data.append(res)

        elif "dim_guest" in query:
            if "*" in query:
                data.append({
                    "gid": d[0],
                    "name": d[1],
                    "phone": d[2]
                })
            else:
                params = query.split(" ")[1]
                params = params.split(",")
                res = {}

                for i in range(len(params)):
                    res[params[i]] = d[i]
                data.append(res)

        elif "dim_restaurant" in query:
            if "*" in query:
                data.append({
                    "rid": d[0],
                    "genre": d[1],
                    "region": d[2],
                    "name": d[3]
                })
            else:
                params = query.split(" ")[1]
                params = params.split(",")
                res = {}

                for i in range(len(params)):
                    res[params[i]] = d[i]
                data.append(res)

        elif "dim_reservation" in query:
            if "*" in query:
                data.append({
                    "res_id": d[0],
                    "guest_count": d[1],
                    "amount_spent": d[2]
                })
            else:
                params = query.split(" ")[1]
                params = params.split(",")
                res = {}

                for i in range(len(params)):
                    res[params[i]] = d[i]
                data.append(res)

    return json.dumps(data)

if __name__ == "__main__":
    app.run(debug=True)

