# Art Gallery – Redis Key-Value POC

A Holberton PLD demonstration of artists creating artworks and customers buying artworks using Redis hashes and sets.

## Preloaded sample customers

`customers.csv` includes **40 fictional customer records** (IDs 1–40), each with
`name`, `email`, `city`, and `status`. All addresses use `example.com` and are
sample data, not real customer information.

Running `python3 art_gallery.py` automatically imports all 40 records into Redis
as `customer:1` through `customer:40`, and adds their IDs to the Redis set
`customers:all`. Re-running the import updates the same customer keys rather
than duplicating them. Existing purchases are not deleted.

Check the data with:

```bash
docker exec art-gallery-redis redis-cli SCARD customers:all
docker exec art-gallery-redis redis-cli HGETALL customer:1
docker exec art-gallery-redis redis-cli HGETALL customer:40
```

The CSV is the bundled seed dataset; the live database is populated after you
run the Python script while Redis is running.

## Data model

- `artist:1` — Redis hash for an artist
- `artist:1:artworks` — set of artwork IDs owned by that artist
- `artwork:101` — Redis hash with title, artist ID, price and availability
- `customer:1` through `customer:40` — Redis hashes for 40 customers
- `customers:all` — set of all seeded customer IDs
- `purchase:1` — Redis hash recording customer, artwork, amount and status
- `customer:1:purchases` — set of purchase IDs
- `cart:customer:1` — temporary cart key with a 60-second TTL

Relationships are enforced in application logic, not with SQL foreign keys. The purchase uses an atomic Redis Lua script to avoid selling the same artwork twice.

## Run

```bash
docker compose up -d
docker exec art-gallery-redis redis-cli PING
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 art_gallery.py
```

For a fresh demo, run `docker exec art-gallery-redis redis-cli FLUSHDB` **only if this Redis instance is dedicated to this demo**. `FLUSHDB` deletes all keys in the selected database.

Stop the container: `docker compose down`.

## What the demo demonstrates

1. **Create:** Save artists, customers, and artworks with `HSET`.
2. **Read:** Retrieve records with `HGETALL` and the artist's artwork IDs with `SMEMBERS`.
3. **Update:** Set artwork availability to `false` on purchase.
4. **Delete:** Redis supports `DEL` (try `DEL cart:customer:1` in redis-cli after the demo).
5. **Distinctive feature:** `EX 60` sets a cart key to expire automatically; `TTL` reads remaining seconds.

This is an educational proof of concept, not a payment system. A recorded purchase does **not** charge a customer. Production systems would need authentication, authorization, durable order/payment records, idempotency, and suitable persistence settings.

## Comparing models

Redis excels at key-based access and expiring temporary data. Relational databases such as PostgreSQL are usually a better fit for durable payments and strongly enforced relationships. A production gallery could use PostgreSQL for orders and Redis for temporary carts and sessions.
