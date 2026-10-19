#!/usr/bin/env python3
"""Art Gallery Redis proof of concept: artists, artworks, customers, purchases."""
import csv
from pathlib import Path

import redis


def seed_customers(db):
    """Load 40 fictional customers from the bundled CSV into Redis hashes."""
    csv_path = Path(__file__).resolve().parent / "customers.csv"
    with csv_path.open("r", encoding="utf-8", newline="") as file:
        customers = list(csv.DictReader(file))

    for customer in customers:
        customer_id = customer.pop("customer_id")
        db.hset("customer:" + customer_id, mapping=customer)
        db.sadd("customers:all", customer_id)
    return len(customers)


def main():
    db = redis.Redis(host="localhost", port=6379, decode_responses=True)
    db.ping()

    # Demo records use fixed IDs for a repeatable presentation.
    db.hset("artist:1", mapping={"name": "Dana", "email": "artist@example.com"})
    customer_count = seed_customers(db)
    print("Seeded customer records:", customer_count)
    db.hset("artwork:101", mapping={"title": "Sunset Painting", "artist_id": "1", "price": "500", "available": "true"})
    db.hset("artwork:102", mapping={"title": "Abstract Art", "artist_id": "1", "price": "700", "available": "true"})
    db.sadd("artist:1:artworks", "101", "102")

    print("Customer 1:", db.hgetall("customer:1"))
    print("Total customer IDs:", db.scard("customers:all"))
    print("Artist:", db.hgetall("artist:1"))
    print("Artworks by artist 1:")
    for artwork_id in sorted(db.smembers("artist:1:artworks")):
        print(" ", artwork_id, db.hgetall("artwork:" + artwork_id))

    # Transactional purchase: only one customer can purchase this artwork.
    purchase_script = """
    if redis.call('HGET', KEYS[1], 'available') ~= 'true' then
        return 0
    end
    if redis.call('EXISTS', KEYS[2]) == 1 then
        return -1
    end
    local price = redis.call('HGET', KEYS[1], 'price')
    redis.call('HSET', KEYS[1], 'available', 'false')
    redis.call('HSET', KEYS[2], 'customer_id', ARGV[1], 'artwork_id', ARGV[2], 'amount', price, 'status', 'recorded')
    redis.call('SADD', KEYS[3], ARGV[3])
    return 1
    """
    result = db.eval(purchase_script, 3, "artwork:101", "purchase:1", "customer:1:purchases", "1", "101", "1")
    print("Purchase result:", {1: "recorded", 0: "unavailable", -1: "purchase ID exists"}[result])
    print("Artwork after purchase:", db.hgetall("artwork:101"))
    print("Purchase:", db.hgetall("purchase:1"))

    # TTL demo: temporary cart, automatically expires after 60 seconds.
    db.set("cart:customer:1", "artwork:102", ex=60)
    print("Cart TTL (seconds):", db.ttl("cart:customer:1"))
    print("Note: this POC records a purchase; it does not process real payments.")


if __name__ == "__main__":
    main()
