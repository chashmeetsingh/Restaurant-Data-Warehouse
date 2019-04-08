import mysql.connector
from faker import Faker
import random

sdb1 = mysql.connector.connect(
    host="localhost",
    user="chashmeet",
    passwd="password",
    auth_plugin='mysql_native_password'
)

# print(mydb)

sdb1Cursor = sdb1.cursor()

sdb1Cursor.execute("DROP DATABASE sdb1")

sdb1Cursor.execute("CREATE DATABASE sdb1")

sdb1Cursor.execute("SHOW DATABASES")

# for x in mycursor:
#   print(x)

sdb1 = mysql.connector.connect(
    host="localhost",
    user="chashmeet",
    passwd="password",
    auth_plugin='mysql_native_password',
    database='sdb1'
)

# print(mydb)

sdb1Cursor = sdb1.cursor()

sdb1Cursor.execute("CREATE TABLE IF NOT EXISTS Guest (gid INT AUTO_INCREMENT, name VARCHAR(50) NOT NULL, phone VARCHAR(30), points INT, PRIMARY KEY (gid, phone))")
sdb1Cursor.execute("CREATE TABLE IF NOT EXISTS Restaurant (rid INT AUTO_INCREMENT, genre VARCHAR(30) NOT NULL, region VARCHAR(35), name VARCHAR(45) , PRIMARY KEY (rid, name, region))")
sdb1Cursor.execute("CREATE TABLE IF NOT EXISTS Reservations(gid INT, rid INT, amt_spent INT, date DATE, guest_count INT, foreign key (gid) references guest(gid), foreign key (rid) references restaurant(rid))")

sdb1Cursor.execute("SHOW TABLES")

for x in sdb1Cursor:
  print(x)

faker = Faker()

guestData = []

for i in range(500):
    guestData.append((faker.name(), faker.phone_number(), 0))

# print(guestData)

sql = "INSERT INTO guest (name, phone, points) VALUES (%s, %s, %s)"

sdb1Cursor.executemany(sql, guestData)

sdb1.commit()

print(sdb1Cursor.rowcount, "guests were inserted.")

sdb1Cursor.execute("SELECT * FROM guest")

guests = sdb1Cursor.fetchall()

# for guest in guests:
#   print(guest)

genres = ['Italian/French', 'Dining bar', 'Yakiniku/Korean food', 'Cafe/Sweets', 'Izakaya', 'Okonomiyaki/Monja/Teppanyaki', 'Bar/Cocktail', 'Japanese food', 'Creative cuisine', 'Other', 'Western food', 'International cuisine', 'Asian', 'Karaoke/Party']
#regions = ["Alma" ,"Fleurimont" ,"Longueuil" ,"Amos" ,"Gaspe" ,"Marieville" ,"Anjou" ,"Gatineau" ,"Mount Royal" ,"Aylmer" ,"Hull" ,"Montreal" ,"Beauport" ,"Joliette" ,"Montreal Region" ,"Bromptonville" ,"Jonquiere" ,"Montreal-Est" ,"Brosssard" ,"Lachine" ,"Quebec" ,"Chateauguay" ,"Lasalle" ,"Saint-Leonard" ,"Chicoutimi" ,"Laurentides" ,"Sherbrooke" ,"Coaticook" ,"LaSalle" ,"Sorel" ,"Coaticook" ,"Laval" ,"Thetford Mines" ,"Dorval" ,"Lennoxville" ,"Victoriaville" ,"Drummondville" ,"Levis"]
regions = ["Alma" ,"Fleurimont" ,"Longueuil" ,"Gaspe", "Coaticook" ,"LaSalle" ,"Sorel" ,"Gatineau" ,"Laval","Dorval"]
# print(len(regions))
restaurantData = []

for i in range(100):
    restaurantData.append((random.choice(genres), regions[random.randint(0, 9)], faker.company()))

sql = "INSERT INTO restaurant (genre, region, name) VALUES (%s, %s, %s)"

sdb1Cursor.executemany(sql, restaurantData)

sdb1.commit()

print(sdb1Cursor.rowcount, "restaurants were inserted.")

sdb1Cursor.execute("SELECT * FROM restaurant")

restaurants = sdb1Cursor.fetchall()

# for restaurant in restaurants:
#     print(restaurant)

reservationsData = []

for i in range(10000):
    reservationsData.append((random.randint(1, 500), random.randint(1, 100), faker.pyint() / 100, faker.date_time_between(start_date='-2y', end_date='now', tzinfo=None), random.randint(1, 10)))

sql = "INSERT INTO reservations (gid, rid, amt_spent, date, guest_count) VALUES (%s, %s, %s, %s, %s)"

sdb1Cursor.executemany(sql, reservationsData)

sdb1.commit()

print(sdb1Cursor.rowcount, "reservations were inserted.")

sdb1Cursor.execute("SELECT * FROM reservations")

reservations = sdb1Cursor.fetchall()

# for reservation in reservations:
#   print(reservation)

for guest in guests:
    sql = "Select * from reservations where gid = " + str(guest[0])
    sdb1Cursor.execute(sql)
    reservations_made_by_guest = sdb1Cursor.fetchall()

    money_spent = 0
    for reservation in reservations_made_by_guest:
        money_spent += reservation[2]

    sql = "Update guest set points = " + str(money_spent) + " where gid = " + str(guest[0])
    sdb1Cursor.execute(sql)
    sdb1.commit()
