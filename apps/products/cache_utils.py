def product_public_cache_key(shop_id: int, product_id: int) -> str:
    return f"product:public:v1:{shop_id}:{product_id}"
