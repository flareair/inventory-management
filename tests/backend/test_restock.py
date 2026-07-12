"""
Tests for restocking API endpoints (recommendations and submitted orders).
"""
import pytest


class TestRestockRecommendations:
    """Test suite for the restock recommendations endpoint."""

    def test_get_recommendations_with_budget(self, client):
        """Test getting recommendations respects the provided budget."""
        response = client.get("/api/restock/recommendations?budget=5000")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        total_cost = sum(item["recommended_cost"] for item in data)
        assert total_cost <= 5000

        for item in data:
            assert "sku" in item
            assert "name" in item
            assert "category" in item
            assert "warehouse" in item
            assert "unit_cost" in item
            assert "recommended_quantity" in item
            assert "recommended_cost" in item
            assert "reason" in item
            assert item["recommended_quantity"] > 0

    def test_zero_budget_returns_no_recommendations(self, client):
        """Test that a budget of 0 recommends nothing."""
        response = client.get("/api/restock/recommendations?budget=0")
        assert response.status_code == 200
        assert response.json() == []

    def test_recommendations_prioritize_below_reorder_point(self, client):
        """Items below their reorder point should be recommended before others."""
        response = client.get("/api/restock/recommendations?budget=50000")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0

        below_reorder_indices = [
            i for i, item in enumerate(data)
            if item["quantity_on_hand"] <= item["reorder_point"]
        ]
        other_indices = [
            i for i, item in enumerate(data)
            if item["quantity_on_hand"] > item["reorder_point"]
        ]

        if below_reorder_indices and other_indices:
            assert max(below_reorder_indices) < min(other_indices), \
                "Below-reorder-point items should be ranked before other items"

    def test_larger_budget_recommends_at_least_as_much(self, client):
        """A larger budget should never recommend a lower total cost."""
        small_response = client.get("/api/restock/recommendations?budget=500")
        large_response = client.get("/api/restock/recommendations?budget=50000")

        small_total = sum(item["recommended_cost"] for item in small_response.json())
        large_total = sum(item["recommended_cost"] for item in large_response.json())

        assert large_total >= small_total


class TestRestockOrders:
    """Test suite for submitting and retrieving restock orders."""

    def test_create_restock_order(self, client):
        """Test submitting a restock order returns a valid RestockOrder."""
        payload = {
            "budget": 1000,
            "items": [
                {"sku": "WDG-001", "name": "Industrial Widget Type A", "quantity": 10, "unit_cost": 24.99}
            ]
        }
        response = client.post("/api/restock/orders", json=payload)
        assert response.status_code == 201

        data = response.json()
        assert "id" in data
        assert data["order_number"].startswith("RSK-")
        assert data["status"] == "Submitted"
        assert data["total_cost"] == pytest.approx(249.90)
        assert data["lead_time_days"] > 0
        assert "expected_delivery" in data
        assert "submitted_date" in data

    def test_created_order_appears_in_get_all(self, client):
        """Test that a submitted order shows up in GET /api/restock/orders."""
        payload = {
            "budget": 500,
            "items": [
                {"sku": "SNR-420", "name": "Temperature Sensor Module", "quantity": 5, "unit_cost": 89.5}
            ]
        }
        create_response = client.post("/api/restock/orders", json=payload)
        assert create_response.status_code == 201
        created_order = create_response.json()

        list_response = client.get("/api/restock/orders")
        assert list_response.status_code == 200

        all_orders = list_response.json()
        assert any(order["id"] == created_order["id"] for order in all_orders)

    def test_create_restock_order_requires_items(self, client):
        """Test that submitting an order with no items returns 400."""
        response = client.post("/api/restock/orders", json={"budget": 100, "items": []})
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data

    def test_lead_time_matches_category_lookup(self, client):
        """Controllers category items should get the 14-day lead time."""
        payload = {
            "budget": 500,
            "items": [
                {"sku": "CTL-330", "name": "Logic Controller Board", "quantity": 2, "unit_cost": 45.0}
            ]
        }
        response = client.post("/api/restock/orders", json=payload)
        assert response.status_code == 201
        assert response.json()["lead_time_days"] == 14
