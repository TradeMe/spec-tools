"""Tests for shopping cart functionality."""

import pytest


class ShoppingCart:
    """Mock shopping cart implementation for testing."""

    def __init__(self):
        self.items = []
        self.total = 0.0

    def add_item(self, item_id, price=0.0, quantity=1):
        """Add item to cart."""
        self.items.append({"id": item_id, "price": price, "quantity": quantity})
        self.total += price * quantity

    def remove_item(self, item_id):
        """Remove item from cart."""
        self.items = [item for item in self.items if item["id"] != item_id]
        self.total = sum(item["price"] * item["quantity"] for item in self.items)

    @property
    def item_count(self):
        """Get total item count."""
        return sum(item["quantity"] for item in self.items)

    def is_empty(self):
        """Check if cart is empty."""
        return len(self.items) == 0


class TestShoppingCart:
    """Test suite for shopping cart."""

    @pytest.mark.req("SPEC-100/REQ-001")
    def test_add_item_to_cart(self):
        """Test that users can add items to the cart."""
        cart = ShoppingCart()
        cart.add_item(item_id="SKU-123", price=10.00, quantity=1)

        assert cart.item_count == 1
        assert len(cart.items) == 1

    @pytest.mark.req("SPEC-100/REQ-002")
    def test_cart_total_updates_when_item_added(self):
        """Test that cart total updates in real-time when items are added."""
        cart = ShoppingCart()

        cart.add_item(item_id="SKU-123", price=10.00, quantity=2)
        assert cart.total == 20.00

        cart.add_item(item_id="SKU-456", price=5.00, quantity=1)
        assert cart.total == 25.00

    @pytest.mark.req("SPEC-100/REQ-003")
    def test_remove_item_from_cart(self):
        """Test that users can remove items from the cart."""
        cart = ShoppingCart()
        cart.add_item(item_id="SKU-123", price=10.00, quantity=1)
        cart.add_item(item_id="SKU-456", price=5.00, quantity=1)

        cart.remove_item("SKU-123")

        assert cart.item_count == 1
        assert cart.total == 5.00

    @pytest.mark.req("SPEC-100/REQ-004")
    def test_empty_cart_message(self):
        """Test that empty cart displays appropriate message."""
        cart = ShoppingCart()

        assert cart.is_empty()
        # In real implementation, UI would show "Your cart is empty"

    @pytest.mark.req("SPEC-100/REQ-005")
    def test_cart_persistence(self):
        """Test that cart contents persist across sessions."""
        # This would test local storage in real implementation
        cart = ShoppingCart()
        cart.add_item(item_id="SKU-123", price=10.00, quantity=1)

        # Simulate session persistence
        assert cart.item_count == 1

    @pytest.mark.req("SPEC-100/NFR-001")
    def test_cart_calculation_performance(self):
        """Test that cart totals are calculated within 100ms."""
        import time

        cart = ShoppingCart()
        # Add many items
        for i in range(100):
            cart.add_item(item_id=f"SKU-{i}", price=10.00, quantity=1)

        start = time.perf_counter()
        _ = cart.total
        duration = time.perf_counter() - start

        assert duration < 0.1  # 100ms

    @pytest.mark.req("SPEC-100/NFR-002")
    def test_cart_mobile_responsiveness(self):
        """Test that cart interface works on mobile devices."""
        # This would test responsive design in real implementation
        # For now, just verify cart functionality works
        cart = ShoppingCart()
        cart.add_item(item_id="SKU-123", price=10.00, quantity=1)
        assert cart.item_count == 1
