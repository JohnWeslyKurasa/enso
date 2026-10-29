"""Data Loader and Normalizer for Thelawala Search.

Handles:
- Ingestion of catalog.csv and inventory.csv
- Normalization of metro_feed pricing (paise to INR)
- Resolution of stock status and restock ETAs
- Exclusion of discontinued items
"""

import csv
import os
from typing import Dict, List, Any, Optional

class Product:
    def __init__(
        self,
        sku_id: str,
        name: str,
        brand: str,
        category: str,
        size: str,
        price: float,
        supplier: str,
        description: str,
        stock_qty: int,
        status: str,
        restock_eta: str = "",
        is_private_label: bool = False
    ):
        self.sku_id = sku_id.strip()
        self.name = name.strip()
        self.brand = brand.strip()
        self.category = category.strip()
        self.size = size.strip()
        self.price = price
        self.supplier = supplier.strip()
        self.description = description.strip() if description else ""
        self.stock_qty = stock_qty
        self.status = status.strip()
        self.restock_eta = restock_eta.strip() if restock_eta else ""
        self.is_private_label = is_private_label

    @property
    def is_in_stock(self) -> bool:
        return self.stock_qty > 0 and self.status == 'active'

    @property
    def is_discontinued(self) -> bool:
        return self.status == 'discontinued'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sku_id": self.sku_id,
            "name": self.name,
            "brand": self.brand,
            "category": self.category,
            "size": self.size,
            "price": self.price,
            "supplier": self.supplier,
            "description": self.description,
            "stock_qty": self.stock_qty,
            "status": self.status,
            "restock_eta": self.restock_eta,
            "is_in_stock": self.is_in_stock,
            "is_private_label": self.is_private_label
        }


def find_file(preferred_path: Optional[str], candidates: List[str]) -> Optional[str]:
    if preferred_path and os.path.exists(preferred_path):
        return preferred_path
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return None


def load_catalog_and_inventory(
    catalog_path: Optional[str] = None,
    inventory_path: Optional[str] = None
) -> Dict[str, Product]:
    """Loads and normalizes catalog and inventory datasets using flexible path resolution."""
    resolved_catalog = find_file(catalog_path, [
        "catalog.csv",
        "catalog (1).csv",
        "thelawala-search-data/catalog.csv",
        os.path.join(os.path.dirname(__file__), "..", "catalog.csv"),
        os.path.join(os.path.dirname(__file__), "..", "catalog (1).csv"),
        os.path.join(os.path.dirname(__file__), "..", "thelawala-search-data", "catalog.csv"),
    ])

    resolved_inventory = find_file(inventory_path, [
        "inventory.csv",
        "thelawala-search-data/inventory.csv",
        os.path.join(os.path.dirname(__file__), "..", "inventory.csv"),
        os.path.join(os.path.dirname(__file__), "..", "thelawala-search-data", "inventory.csv"),
    ])

    if not resolved_catalog:
        raise FileNotFoundError(f"Catalog file not found. Checked: {catalog_path or 'catalog.csv / catalog (1).csv'}")
    if not resolved_inventory:
        raise FileNotFoundError(f"Inventory file not found. Checked: {inventory_path or 'inventory.csv'}")

    # 1. Load inventory
    inventory_data: Dict[str, Dict[str, Any]] = {}
    with open(resolved_inventory, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku_id = row["sku_id"].strip()
            try:
                qty = int(row.get("stock_qty", 0))
            except (ValueError, TypeError):
                qty = 0
            inventory_data[sku_id] = {
                "stock_qty": qty,
                "status": row.get("status", "active").strip().lower(),
                "restock_eta": row.get("restock_eta", "").strip()
            }

    # 2. Load catalog and normalize
    products: Dict[str, Product] = {}
    with open(resolved_catalog, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku_id = row["sku_id"].strip()
            name = row.get("name", "").strip()
            brand = row.get("brand", "").strip()
            category = row.get("category", "").strip()
            size = row.get("size", "").strip()
            supplier = row.get("supplier", "").strip().lower()
            desc = row.get("description", "").strip()
            
            # Raw price normalization
            raw_price_str = row.get("price", "0").strip()
            try:
                raw_price = float(raw_price_str)
            except ValueError:
                raw_price = 0.0

            # Normalization rule for metro_feed:
            # metro_feed prices are stored in paise (1 INR = 100 paise)
            if supplier == "metro_feed":
                price = round(raw_price / 100.0, 2)
            else:
                price = round(raw_price, 2)

            # Inventory status
            inv = inventory_data.get(sku_id, {})
            stock_qty = inv.get("stock_qty", 0)
            status = inv.get("status", "active")
            restock_eta = inv.get("restock_eta", "")

            # Skip discontinued products completely (per Sandeep / Ops rule)
            if status == "discontinued":
                continue

            # Check private label ("Thela Select")
            is_private_label = (
                brand.lower() == "thela select" or 
                "thela select" in name.lower()
            )

            prod = Product(
                sku_id=sku_id,
                name=name,
                brand=brand,
                category=category,
                size=size,
                price=price,
                supplier=supplier,
                description=desc,
                stock_qty=stock_qty,
                status=status,
                restock_eta=restock_eta,
                is_private_label=is_private_label
            )
            products[sku_id] = prod

    return products
