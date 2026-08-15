import random

LOCALITIES = [
   "Tulasamma Vedhi", "Vadaparru", "Gollavilli", "Uppalaguptam", "Kunavaram", "Sannavilli"
]

FIRST_NAMES = [
   "Siva", "Balu", "Balaji", "Srinu", "Vinnu", "Pardhu", "Raju", "Raja", "Ravi", "Pavan", "Surya", "Hari", "Kalyan", "Arjun", "Venu", "Sai"
]

LAST_NAMES = [
   "Saladi", "Nagulapalli", "Adapa", "Manchem", "Marisetti", "Yella", "Perabattula", "Thatavarti", "Goud", "Penta"
]

CUSTOMERS = []

for customer_id in range(1, 201):
   name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
   region = random.choice(LOCALITIES)

   CUSTOMERS.append({
      "customer_id": customer_id,
      "name": name,
      "region": region
   })