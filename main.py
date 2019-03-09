from flask import Flask, render_template, request
import mysql.connector
import pymongo
import json
import dateutil.parser

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

@app.route("/updateData")
def home():

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
            sql = "INSERT INTO dw_fact (gid, rid, created_at, points, reserve_id) VALUES(%s, %s, %s, %s, %s)"
            values = (reservation[0], reservation[1], reservation[3], guest[3], reserve_id)
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
            sql = "INSERT INTO dw_fact (gid, rid, created_at, points, reserve_id) VALUES(%s, %s, %s, %s, %s)"
            values = (str(reservation["gid"]), str(reservation["rid"]), str(reservation["transaction_date"]), str(guest["points_earned"]), reserve_id)
            dwCursor.execute(sql, values)
            dwConnection.commit()
        except mysql.connector.Error as e:
            print("dw_fact2 issue " + str(e))
            pass

        # break

    return render_template("about.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/")
def visualize():
    return render_template("home.html")

@app.route("/execute")
def execute():
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
                    "created_at": d[2].strftime('%d-%b-%Y'),
                    "reserve_id": d[3],
                    "points": d[4]
                })
            else:
                params = query.split(" ")[1]
                params = params.split(",")
                res = {}

                for i in range(len(params)):
                    res[params[i]] = d[i]
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

