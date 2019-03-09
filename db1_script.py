import mysql.connector
from faker import Faker
import random

mydb = mysql.connector.connect(
    host="localhost",
    user="chashmeet",
    passwd="password",
    auth_plugin='mysql_native_password'
)

# print(mydb)

mycursor = mydb.cursor()

mycursor.execute("DROP DATABASE sdb1")

mycursor.execute("CREATE DATABASE sdb1")

mycursor.execute("SHOW DATABASES")

# for x in mycursor:
#   print(x)

mydb = mysql.connector.connect(
    host="localhost",
    user="chashmeet",
    passwd="password",
    auth_plugin='mysql_native_password',
    database='sdb1'
)

# print(mydb)

mycursor = mydb.cursor()

mycursor.execute("CREATE TABLE IF NOT EXISTS Guest (gid INT AUTO_INCREMENT, name VARCHAR(50) NOT NULL, phone VARCHAR(30), points INT, PRIMARY KEY (gid))")
mycursor.execute("CREATE TABLE IF NOT EXISTS Restaurant (rid INT AUTO_INCREMENT, genre VARCHAR(30) NOT NULL, region VARCHAR(35), name VARCHAR(45) , PRIMARY KEY (rid))")
mycursor.execute("CREATE TABLE IF NOT EXISTS Reservations(gid INT, rid INT, amt_spent INT, date DATE, guest_count INT, foreign key (gid) references guest(gid), foreign key (rid) references restaurant(rid))")

mycursor.execute("SHOW TABLES")

for x in mycursor:
  print(x)

fake = Faker()

guestData = []

for i in range(500):
    guestData.append((fake.name(), fake.phone_number(), 0))

# print(guestData)

sql = "INSERT INTO guest (name, phone, points) VALUES (%s, %s, %s)"

mycursor.executemany(sql, guestData)

mydb.commit()

print(mycursor.rowcount, "guests were inserted.")

mycursor.execute("SELECT * FROM guest")

guests = mycursor.fetchall()

# for guest in guests:
#   print(guest)

genres = ['Italian/French', 'Dining bar', 'Yakiniku/Korean food', 'Cafe/Sweets', 'Izakaya', 'Okonomiyaki/Monja/Teppanyaki', 'Bar/Cocktail', 'Japanese food', 'Creative cuisine', 'Other', 'Western food', 'International cuisine', 'Asian', 'Karaoke/Party']
regions = ["Ajax" ,"Halton" ,"Peterborough" ,"Atikokan" ,"Halton Hills" ,"Pickering" ,"Barrie" ,"Hamilton" ,"Port Bruce" ,"Belleville" ,"Hamilton-Wentworth" ,"Port Burwell" ,"Blandford-Blenheim" ,"Hearst" ,"Port Colborne" ,"Blind River" ,"Huntsville" ,"Port Hope" ,"Brampton" ,"Ingersoll" ,"Prince Edward" ,"Brant" ,"James" ,"Quinte West" ,"Brantford" ,"Kanata" ,"Renfrew" ,"Brock" ,"Kincardine" ,"Richmond Hill" ,"Brockville" ,"King" ,"Sarnia" ,"Burlington" ,"Kingston" ,"Sault Ste. Marie" ,"Caledon" ,"Kirkland Lake" ,"Scarborough" ,"Cambridge" ,"Kitchener" ,"Scugog" ,"Chatham-Kent" ,"Larder Lake" ,"Souix Lookout CoC Sioux Lookout" ,"Chesterville" ,"Leamington" ,"Smiths Falls" ,"Clarington" ,"Lennox-Addington" ,"South-West Oxford" ,"Cobourg" ,"Lincoln" ,"St. Catharines" ,"Cochrane" ,"Lindsay" ,"St. Thomas" ,"Collingwood" ,"London" ,"Stoney Creek" ,"Cornwall" ,"Loyalist Township" ,"Stratford" ,"Cumberland" ,"Markham" ,"Sudbury" ,"Deep River" ,"Metro Toronto" ,"Temagami" ,"Dundas" ,"Merrickville" ,"Thorold" ,"Durham" ,"Milton" ,"Thunder Bay" ,"Dymond" ,"Nepean" ,"Tillsonburg" ,"Ear Falls" ,"Newmarket" ,"Timmins" ,"East Gwillimbury" ,"Niagara" ,"Toronto" ,"East Zorra-Tavistock" ,"Niagara Falls" ,"Uxbridge" ,"Elgin" ,"Niagara-on-the-Lake" ,"Vaughan" ,"Elliot Lake" ,"North Bay" ,"Wainfleet" ,"Flamborough" ,"North Dorchester" ,"Wasaga Beach" ,"Fort Erie" ,"North Dumfries" ,"Waterloo" ,"Fort Frances" ,"North York" ,"Waterloo" ,"Gananoque" ,"Norwich" ,"Welland" ,"Georgina" ,"Oakville" ,"Wellesley" ,"Glanbrook" ,"Orangeville" ,"West Carleton" ,"Gloucester" ,"Orillia" ,"West Lincoln" ,"Goulbourn" ,"Osgoode" ,"Whitby" ,"Gravenhurst" ,"Oshawa" ,"Wilmot" ,"Grimsby" ,"Ottawa" ,"Windsor" ,"Guelph" ,"Ottawa-Carleton" ,"Woolwich" ,"Haldimand-Norfork" ,"Owen Sound" ,"York"]
# print(len(regions))
restaurantData = []

for i in range(100):
    restaurantData.append((random.choice(genres), regions[random.randint(0, 99)], fake.company()))

sql = "INSERT INTO restaurant (genre, region, name) VALUES (%s, %s, %s)"

mycursor.executemany(sql, restaurantData)

mydb.commit()

print(mycursor.rowcount, "restaurants were inserted.")

mycursor.execute("SELECT * FROM restaurant")

restaurants = mycursor.fetchall()

# for restaurant in restaurants:
#     print(restaurant)

reservationsData = []

for i in range(10000):
    reservationsData.append((random.randint(1, 500), random.randint(1, 100), fake.pyint() / 100, fake.date_time_between(start_date='-2y', end_date='now', tzinfo=None), random.randint(1,10)))

sql = "INSERT INTO reservations (gid, rid, amt_spent, date, guest_count) VALUES (%s, %s, %s, %s, %s)"

mycursor.executemany(sql, reservationsData)

mydb.commit()

print(mycursor.rowcount, "reservations were inserted.")

mycursor.execute("SELECT * FROM reservations")

reservations = mycursor.fetchall()

# for reservation in reservations:
#   print(reservation)

for guest in guests:
    sql = "Select * from reservations where gid = " + str(guest[0])
    mycursor.execute(sql)
    reservations_made_by_guest = mycursor.fetchall()

    money_spent = 0
    for reservation in reservations_made_by_guest:
        money_spent += reservation[2]

    sql = "Update guest set points = " + str(money_spent) + " where gid = " + str(guest[0])
    mycursor.execute(sql)
    mydb.commit()
