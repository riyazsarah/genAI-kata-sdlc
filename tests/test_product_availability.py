"""Tests for product availability management functionality (US-009)."""

from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.product import (
    ProductCategory,
    ProductInDB,
    ProductStatus,
    ProductUnit,
    Seasonality,
    StockStatus,
    InventoryUpdate,
    ThresholdUpdate,
)
from app.repositories.product import ProductRepository
from app.services.product import ProductService


@pytest.fixture
def mock_in_stock_product() -> ProductInDB:
    """Create a mock product with sufficient stock."""
    return ProductInDB(
        id=uuid4(),
        farmer_id=uuid4(),
        name="Fresh Apples",
        category=ProductCategory.FRUITS,
        description="Crisp organic apples",
        price=Decimal("3.99"),
        unit=ProductUnit.LB,
        quantity=50,
        seasonality=[Seasonality.FALL],
        images=["https://example.com/apples.jpg"],
        status=ProductStatus.ACTIVE,
        version=1,
        low_stock_threshold=10,
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )


@pytest.fixture
def mock_low_stock_product() -> ProductInDB:
    """Create a mock product with low stock."""
    return ProductInDB(
        id=uuid4(),
        farmer_id=uuid4(),
        name="Organic Carrots",
        category=ProductCategory.VEGETABLES,
        description="Fresh organic carrots",
        price=Decimal("2.49"),
        unit=ProductUnit.BUNCH,
        quantity=5,
        seasonality=[Seasonality.YEAR_ROUND],
        images=[],
        status=ProductStatus.ACTIVE,
        version=1,
        low_stock_threshold=10,
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )


@pytest.fixture
def mock_out_of_stock_product() -> ProductInDB:
    """Create a mock product that is out of stock."""
    return ProductInDB(
        id=uuid4(),
        farmer_id=uuid4(),
        name="Summer Berries",
        category=ProductCategory.FRUITS,
        description="Mixed seasonal berries",
        price=Decimal("5.99"),
        unit=ProductUnit.LB,
        quantity=0,
        seasonality=[Seasonality.SUMMER],
        images=[],
        status=ProductStatus.ACTIVE,
        version=1,
        low_stock_threshold=10,
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )


@pytest.fixture
def mock_repository() -> MagicMock:
    """Create a mock product repository."""
    return MagicMock(spec=ProductRepository)


@pytest.fixture
def product_service(mock_repository: MagicMock) -> ProductService:
    """Create a product service with mock repository."""
    return ProductService(mock_repository)


class TestStockStatus:
    """Test cases for stock status calculation."""

    def test_in_stock_status(self, mock_in_stock_product: ProductInDB) -> None:
        """TC-009-1: Product with quantity > threshold shows 'in_stock'."""
        assert mock_in_stock_product.stock_status == StockStatus.IN_STOCK

    def test_low_stock_status(self, mock_low_stock_product: ProductInDB) -> None:
        """TC-009-2: Product with quantity <= threshold shows 'low_stock'."""
        assert mock_low_stock_product.stock_status == StockStatus.LOW_STOCK

    def test_out_of_stock_status(self, mock_out_of_stock_product: ProductInDB) -> None:
        """TC-009-3: Product with quantity = 0 shows 'out_of_stock'."""
        assert mock_out_of_stock_product.stock_status == StockStatus.OUT_OF_STOCK


class TestUpdateInventory:
    """Test cases for updating product inventory."""

    def test_update_inventory_success(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_low_stock_product: ProductInDB,
    ) -> None:
        """TC-009-4: Farmer successfully updates inventory quantity."""
        # Arrange
        farmer_id = mock_low_stock_product.farmer_id
        product_id = mock_low_stock_product.id
        new_quantity = 100

        updated_product = ProductInDB(
            **{**mock_low_stock_product.model_dump(), "quantity": new_quantity}
        )

        mock_repository.get_by_farmer_and_id.return_value = mock_low_stock_product
        mock_repository.update_quantity.return_value = updated_product

        # Act
        result = product_service.update_inventory(farmer_id, product_id, new_quantity)

        # Assert
        assert result.success is True
        assert result.product is not None
        assert result.product.quantity == new_quantity
        mock_repository.update_quantity.assert_called_once_with(product_id, new_quantity)

    def test_update_inventory_to_zero(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_in_stock_product: ProductInDB,
    ) -> None:
        """TC-009-5: Farmer can set inventory to zero (out of stock)."""
        # Arrange
        farmer_id = mock_in_stock_product.farmer_id
        product_id = mock_in_stock_product.id

        updated_product = ProductInDB(
            **{**mock_in_stock_product.model_dump(), "quantity": 0}
        )

        mock_repository.get_by_farmer_and_id.return_value = mock_in_stock_product
        mock_repository.update_quantity.return_value = updated_product

        # Act
        result = product_service.update_inventory(farmer_id, product_id, 0)

        # Assert
        assert result.success is True
        assert result.product is not None
        assert result.product.quantity == 0
        assert result.product.stock_status == StockStatus.OUT_OF_STOCK

    def test_update_inventory_product_not_found(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
    ) -> None:
        """TC-009-6: Updating inventory for non-existent product fails."""
        # Arrange
        farmer_id = uuid4()
        product_id = uuid4()
        mock_repository.get_by_farmer_and_id.return_value = None

        # Act
        result = product_service.update_inventory(farmer_id, product_id, 50)

        # Assert
        assert result.success is False
        assert "not found" in result.error.lower()


class TestUpdateThreshold:
    """Test cases for updating low-stock threshold."""

    def test_update_threshold_success(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_in_stock_product: ProductInDB,
    ) -> None:
        """TC-009-7: Farmer successfully updates low-stock threshold."""
        # Arrange
        farmer_id = mock_in_stock_product.farmer_id
        product_id = mock_in_stock_product.id
        new_threshold = 20

        updated_product = ProductInDB(
            **{**mock_in_stock_product.model_dump(), "low_stock_threshold": new_threshold}
        )

        mock_repository.get_by_farmer_and_id.return_value = mock_in_stock_product
        mock_repository.update_threshold.return_value = updated_product

        # Act
        result = product_service.update_threshold(farmer_id, product_id, new_threshold)

        # Assert
        assert result.success is True
        assert result.product is not None
        assert result.product.low_stock_threshold == new_threshold
        mock_repository.update_threshold.assert_called_once_with(product_id, new_threshold)

    def test_update_threshold_affects_stock_status(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_in_stock_product: ProductInDB,
    ) -> None:
        """TC-009-8: Increasing threshold can change stock status to low_stock."""
        # Arrange
        farmer_id = mock_in_stock_product.farmer_id
        product_id = mock_in_stock_product.id
        new_threshold = 60  # Current quantity is 50

        updated_product = ProductInDB(
            **{**mock_in_stock_product.model_dump(), "low_stock_threshold": new_threshold}
        )

        mock_repository.get_by_farmer_and_id.return_value = mock_in_stock_product
        mock_repository.update_threshold.return_value = updated_product

        # Act
        result = product_service.update_threshold(farmer_id, product_id, new_threshold)

        # Assert
        assert result.success is True
        assert result.product is not None
        # Stock status should now be low_stock since quantity (50) <= threshold (60)
        assert result.product.stock_status == StockStatus.LOW_STOCK

    def test_update_threshold_product_not_found(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
    ) -> None:
        """TC-009-9: Updating threshold for non-existent product fails."""
        # Arrange
        farmer_id = uuid4()
        product_id = uuid4()
        mock_repository.get_by_farmer_and_id.return_value = None

        # Act
        result = product_service.update_threshold(farmer_id, product_id, 15)

        # Assert
        assert result.success is False
        assert "not found" in result.error.lower()


class TestGetLowStockProducts:
    """Test cases for getting low-stock products."""

    def test_get_low_stock_products_success(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_low_stock_product: ProductInDB,
        mock_out_of_stock_product: ProductInDB,
    ) -> None:
        """TC-009-10: Farmer can view all low-stock products."""
        # Arrange
        farmer_id = mock_low_stock_product.farmer_id
        mock_repository.get_low_stock_products.return_value = [
            mock_low_stock_product,
            mock_out_of_stock_product,
        ]

        # Act
        result = product_service.get_low_stock_products(farmer_id)

        # Assert
        assert result.success is True
        assert result.products is not None
        assert len(result.products) == 2
        mock_repository.get_low_stock_products.assert_called_once_with(farmer_id)

    def test_get_low_stock_products_empty(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
    ) -> None:
        """TC-009-11: Returns empty list when no products are low on stock."""
        # Arrange
        farmer_id = uuid4()
        mock_repository.get_low_stock_products.return_value = []

        # Act
        result = product_service.get_low_stock_products(farmer_id)

        # Assert
        assert result.success is True
        assert result.products is not None
        assert len(result.products) == 0


class TestMarkOutOfStock:
    """Test cases for marking products as out of stock."""

    def test_mark_out_of_stock_success(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_in_stock_product: ProductInDB,
    ) -> None:
        """TC-009-12: Farmer successfully marks product as out of stock."""
        # Arrange
        farmer_id = mock_in_stock_product.farmer_id
        product_id = mock_in_stock_product.id

        updated_product = ProductInDB(
            **{**mock_in_stock_product.model_dump(), "quantity": 0}
        )

        mock_repository.get_by_farmer_and_id.return_value = mock_in_stock_product
        mock_repository.update_quantity.return_value = updated_product

        # Act
        result = product_service.mark_out_of_stock(farmer_id, product_id)

        # Assert
        assert result.success is True
        assert result.product is not None
        assert result.product.quantity == 0
        assert result.product.stock_status == StockStatus.OUT_OF_STOCK

    def test_mark_out_of_stock_product_not_found(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
    ) -> None:
        """Marking non-existent product as out of stock fails."""
        # Arrange
        farmer_id = uuid4()
        product_id = uuid4()
        mock_repository.get_by_farmer_and_id.return_value = None

        # Act
        result = product_service.mark_out_of_stock(farmer_id, product_id)

        # Assert
        assert result.success is False
        assert "not found" in result.error.lower()


class TestMarkInStock:
    """Test cases for marking products as in stock."""

    def test_mark_in_stock_success(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_out_of_stock_product: ProductInDB,
    ) -> None:
        """TC-009-13: Farmer successfully marks product as in stock."""
        # Arrange
        farmer_id = mock_out_of_stock_product.farmer_id
        product_id = mock_out_of_stock_product.id
        restock_quantity = 25

        updated_product = ProductInDB(
            **{**mock_out_of_stock_product.model_dump(), "quantity": restock_quantity}
        )

        mock_repository.get_by_farmer_and_id.return_value = mock_out_of_stock_product
        mock_repository.update_quantity.return_value = updated_product

        # Act
        result = product_service.mark_in_stock(farmer_id, product_id, restock_quantity)

        # Assert
        assert result.success is True
        assert result.product is not None
        assert result.product.quantity == restock_quantity
        assert result.product.stock_status == StockStatus.IN_STOCK

    def test_mark_in_stock_with_zero_quantity_fails(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_out_of_stock_product: ProductInDB,
    ) -> None:
        """TC-009-14: Marking in stock with quantity 0 should fail."""
        # Arrange
        farmer_id = mock_out_of_stock_product.farmer_id
        product_id = mock_out_of_stock_product.id

        # Act
        result = product_service.mark_in_stock(farmer_id, product_id, 0)

        # Assert
        assert result.success is False
        assert "greater than 0" in result.error.lower()

    def test_mark_in_stock_with_negative_quantity_fails(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_out_of_stock_product: ProductInDB,
    ) -> None:
        """TC-009-15: Marking in stock with negative quantity should fail."""
        # Arrange
        farmer_id = mock_out_of_stock_product.farmer_id
        product_id = mock_out_of_stock_product.id

        # Act
        result = product_service.mark_in_stock(farmer_id, product_id, -5)

        # Assert
        assert result.success is False
        assert "greater than 0" in result.error.lower()


class TestInventoryUpdateValidation:
    """Test cases for inventory update request validation."""

    def test_inventory_update_valid(self) -> None:
        """Valid inventory update model creation."""
        update = InventoryUpdate(quantity=50)
        assert update.quantity == 50

    def test_inventory_update_zero_valid(self) -> None:
        """Zero quantity is valid for inventory update."""
        update = InventoryUpdate(quantity=0)
        assert update.quantity == 0

    def test_inventory_update_negative_invalid(self) -> None:
        """Negative quantity should fail validation."""
        with pytest.raises(ValueError):
            InventoryUpdate(quantity=-1)


class TestThresholdUpdateValidation:
    """Test cases for threshold update request validation."""

    def test_threshold_update_valid(self) -> None:
        """Valid threshold update model creation."""
        update = ThresholdUpdate(low_stock_threshold=15)
        assert update.low_stock_threshold == 15

    def test_threshold_update_zero_valid(self) -> None:
        """Zero threshold is valid (disables low-stock alerts)."""
        update = ThresholdUpdate(low_stock_threshold=0)
        assert update.low_stock_threshold == 0

    def test_threshold_update_negative_invalid(self) -> None:
        """Negative threshold should fail validation."""
        with pytest.raises(ValueError):
            ThresholdUpdate(low_stock_threshold=-1)
