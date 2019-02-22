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

    # Transform Data

    # Get Reservations
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
            print(e)
            continue

        try:
            sql = "INSERT INTO DIM_RESTAURANT (rid, genre, region, name) VALUES(%s, %s, %s, %s)"
            values = (restaurant[0], restaurant[1], restaurant[2], restaurant[3])
            dwCursor.execute(sql, values)
            dwConnection.commit()
        except mysql.connector.Error as e:
            print(e)
            continue

        try:
            sql = "INSERT INTO DIM_RESERVATION (guest_count, amount_spent) VALUES(%s, %s)"
            values = (reservation[4], reservation[2])
            dwCursor.execute(sql, values)
            dwConnection.commit()
            reserve_id = dwCursor.lastrowid
        except mysql.connector.Error as e:
            print(e)
            continue

        try:
            sql = "INSERT INTO dw_fact (gid, rid, created_at, points, reserve_id) VALUES(%s, %s, %s, %s, %s)"
            values = (reservation[0], reservation[1], reservation[3], guest[3], reserve_id)
            dwCursor.execute(sql, values)
            dwConnection.commit()
        except mysql.connector.Error as e:
            print(e)
            continue

        # break

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
            print(e)
            continue

        try:
            sql = "INSERT INTO DIM_RESTAURANT (rid, genre, region, name) VALUES(%s, %s, %s, %s)"
            values = (str(restaurant["_id"]), str(restaurant["genre"]), str(restaurant["region"]), str(restaurant["name"]))
            dwCursor.execute(sql, values)
            dwConnection.commit()
        except mysql.connector.Error as e:
            print(e)
            continue

        try:
            sql = "INSERT INTO DIM_RESERVATION (guest_count, amount_spent) VALUES(%s, %s)"
            values = (str(reservation["guest_count"]), str(reservation["amount_spent"]))
            dwCursor.execute(sql, values)
            reserve_id = dwCursor.lastrowid
            dwConnection.commit()
        except mysql.connector.Error as e:
            print(e)
            continue

        try:
            sql = "INSERT INTO dw_fact (gid, rid, created_at, points, reserve_id) VALUES(%s, %s, %s, %s, %s)"
            values = (str(reservation["gid"]), str(reservation["rid"]), str(reservation["transaction_date"]), str(guest["points_earned"]), reserve_id)
            dwCursor.execute(sql, values)
            dwConnection.commit()
        except mysql.connector.Error as e:
            print(e)
            continue

        # break

    return render_template("home.html")

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
        return "Invalid query"

    cursorData = dwCursor.fetchall()
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


    return json.dumps(data)

if __name__ == "__main__":
    app.run(debug=True)

