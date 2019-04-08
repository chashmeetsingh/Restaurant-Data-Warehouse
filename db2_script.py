import pymongo
from faker import Faker
import random

pymongoClient = pymongo.MongoClient("mongodb://localhost:27017/")

sdb2 = pymongoClient["sdb2"]

dblist = pymongoClient.list_database_names()
print(dblist)

pymongoClient.drop_database('sdb2')

guest = sdb2["guest"]

faker = Faker()

guestData = []

for i in range(500):
    guestData.append({ "name" : faker.name(), "phone_number" : faker.phone_number(), "points_earned" : 0})

guests = guest.insert_many(guestData)

print(len(guests.inserted_ids), " guests inserted.")

restaurant = sdb2["restaurant"]

genres = ['Italian/French', 'Dining bar', 'Yakiniku/Korean food', 'Cafe/Sweets', 'Izakaya', 'Okonomiyaki/Monja/Teppanyaki', 'Bar/Cocktail', 'Japanese food', 'Creative cuisine', 'Other', 'Western food', 'International cuisine', 'Asian', 'Karaoke/Party']
regions = ["Alma" ,"Fleurimont" ,"Longueuil" ,"Gaspe", "Coaticook" ,"LaSalle" ,"Sorel" ,"Gatineau" ,"Laval","Dorval"]

# print(len(regions))
restaurantData = []

for i in range(100):
    restaurantData.append({"genre": random.choice(genres), "region": regions[random.randint(0, 9)], "name": faker.company()})

restaurants = restaurant.insert_many(restaurantData)
print(len(restaurants.inserted_ids), " restaurants inserted.")

# print(restaurants.inserted_ids[4])

reservation = sdb2["reservation"]

reservationData = []

for i in range(10000):
    reservationData.append({ "gid": guests.inserted_ids[random.randint(0, 499)], "rid": restaurants.inserted_ids[random.randint(0, 99)], "amount_spent": faker.pyint() / 100, "transaction_date": faker.date_time_between(start_date='-2y', end_date='now', tzinfo=None), "guest_count": random.randint(1, 10)})

reservations = reservation.insert_many(reservationData)

print(len(reservations.inserted_ids), " reservations inserted.")

# print(mydb.list_collection_names())

guestCol = sdb2["guest"]

for guest in guestCol.find({}):
    reservationCol = sdb2["reservation"]

    money_spent = 0
    for reservation in reservationCol.find({"gid" : guest["_id"]}):
        money_spent += reservation["amount_spent"]

    guestCol.update_one({"_id" : guest["_id"]}, { "$set": { "points_earned": money_spent } })
