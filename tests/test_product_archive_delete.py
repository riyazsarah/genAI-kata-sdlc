"""Tests for product archive/delete functionality (US-008)."""

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
)
from app.repositories.product import ProductRepository
from app.services.product import ProductService


@pytest.fixture
def mock_active_product() -> ProductInDB:
    """Create a mock active product for testing."""
    return ProductInDB(
        id=uuid4(),
        farmer_id=uuid4(),
        name="Organic Tomatoes",
        category=ProductCategory.VEGETABLES,
        description="Fresh organic tomatoes",
        price=Decimal("4.99"),
        unit=ProductUnit.LB,
        quantity=100,
        seasonality=[Seasonality.SUMMER],
        images=["https://example.com/tomato1.jpg"],
        status=ProductStatus.ACTIVE,
        version=1,
        low_stock_threshold=10,
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )


@pytest.fixture
def mock_archived_product() -> ProductInDB:
    """Create a mock archived product for testing."""
    return ProductInDB(
        id=uuid4(),
        farmer_id=uuid4(),
        name="Old Carrots",
        category=ProductCategory.VEGETABLES,
        description="Archived carrots",
        price=Decimal("2.99"),
        unit=ProductUnit.LB,
        quantity=0,
        seasonality=[Seasonality.FALL],
        images=[],
        status=ProductStatus.ARCHIVED,
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


class TestArchiveProduct:
    """Test cases for archiving products (US-008)."""

    def test_archive_product_success(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_active_product: ProductInDB,
    ) -> None:
        """TC-008-1: Farmer successfully archives an active product."""
        # Arrange
        farmer_id = mock_active_product.farmer_id
        product_id = mock_active_product.id
        archived_product = ProductInDB(
            **{**mock_active_product.model_dump(), "status": ProductStatus.ARCHIVED}
        )

        mock_repository.get_by_farmer_and_id.return_value = mock_active_product
        mock_repository.archive.return_value = archived_product

        # Act
        result = product_service.archive_product(farmer_id, product_id)

        # Assert
        assert result.success is True
        assert result.product is not None
        assert result.product.status == ProductStatus.ARCHIVED
        mock_repository.archive.assert_called_once_with(product_id)

    def test_archive_already_archived_product_fails(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_archived_product: ProductInDB,
    ) -> None:
        """TC-008-2: Archiving an already archived product should fail."""
        # Arrange
        farmer_id = mock_archived_product.farmer_id
        product_id = mock_archived_product.id
        mock_repository.get_by_farmer_and_id.return_value = mock_archived_product

        # Act
        result = product_service.archive_product(farmer_id, product_id)

        # Assert
        assert result.success is False
        assert "already archived" in result.error.lower()
        mock_repository.archive.assert_not_called()

    def test_archive_product_not_found(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
    ) -> None:
        """TC-008-3: Archiving a non-existent product should fail."""
        # Arrange
        farmer_id = uuid4()
        product_id = uuid4()
        mock_repository.get_by_farmer_and_id.return_value = None

        # Act
        result = product_service.archive_product(farmer_id, product_id)

        # Assert
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_archive_product_unauthorized(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_active_product: ProductInDB,
    ) -> None:
        """TC-008-4: Farmer cannot archive another farmer's product."""
        # Arrange
        different_farmer_id = uuid4()
        product_id = mock_active_product.id
        mock_repository.get_by_farmer_and_id.return_value = None

        # Act
        result = product_service.archive_product(different_farmer_id, product_id)

        # Assert
        assert result.success is False
        assert "not found" in result.error.lower() or "permission" in result.error.lower()


class TestReactivateProduct:
    """Test cases for reactivating archived products."""

    def test_reactivate_product_success(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_archived_product: ProductInDB,
    ) -> None:
        """TC-008-5: Farmer successfully reactivates an archived product."""
        # Arrange
        farmer_id = mock_archived_product.farmer_id
        product_id = mock_archived_product.id
        reactivated_product = ProductInDB(
            **{**mock_archived_product.model_dump(), "status": ProductStatus.ACTIVE}
        )

        mock_repository.get_by_farmer_and_id.return_value = mock_archived_product
        mock_repository.reactivate.return_value = reactivated_product

        # Act
        result = product_service.reactivate_product(farmer_id, product_id)

        # Assert
        assert result.success is True
        assert result.product is not None
        assert result.product.status == ProductStatus.ACTIVE
        mock_repository.reactivate.assert_called_once_with(product_id)

    def test_reactivate_active_product_fails(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_active_product: ProductInDB,
    ) -> None:
        """TC-008-6: Reactivating a non-archived product should fail."""
        # Arrange
        farmer_id = mock_active_product.farmer_id
        product_id = mock_active_product.id
        mock_repository.get_by_farmer_and_id.return_value = mock_active_product

        # Act
        result = product_service.reactivate_product(farmer_id, product_id)

        # Assert
        assert result.success is False
        assert "archived" in result.error.lower()
        mock_repository.reactivate.assert_not_called()

    def test_reactivate_product_not_found(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
    ) -> None:
        """Reactivating a non-existent product should fail."""
        # Arrange
        farmer_id = uuid4()
        product_id = uuid4()
        mock_repository.get_by_farmer_and_id.return_value = None

        # Act
        result = product_service.reactivate_product(farmer_id, product_id)

        # Assert
        assert result.success is False
        assert "not found" in result.error.lower()


class TestDeleteProduct:
    """Test cases for permanently deleting products."""

    def test_delete_product_success(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_active_product: ProductInDB,
    ) -> None:
        """TC-008-7: Farmer successfully deletes a product without pending orders."""
        # Arrange
        farmer_id = mock_active_product.farmer_id
        product_id = mock_active_product.id

        mock_repository.get_by_farmer_and_id.return_value = mock_active_product
        mock_repository.has_pending_orders.return_value = False
        mock_repository.delete.return_value = True

        # Act
        result = product_service.delete_product(farmer_id, product_id)

        # Assert
        assert result.success is True
        mock_repository.delete.assert_called_once_with(product_id)

    def test_delete_product_with_pending_orders_fails(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_active_product: ProductInDB,
    ) -> None:
        """TC-008-8: Deleting a product with pending orders should fail."""
        # Arrange
        farmer_id = mock_active_product.farmer_id
        product_id = mock_active_product.id

        mock_repository.get_by_farmer_and_id.return_value = mock_active_product
        mock_repository.has_pending_orders.return_value = True

        # Act
        result = product_service.delete_product(farmer_id, product_id)

        # Assert
        assert result.success is False
        assert "pending orders" in result.error.lower()
        mock_repository.delete.assert_not_called()

    def test_delete_product_not_found(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
    ) -> None:
        """TC-008-9: Deleting a non-existent product should fail."""
        # Arrange
        farmer_id = uuid4()
        product_id = uuid4()
        mock_repository.get_by_farmer_and_id.return_value = None

        # Act
        result = product_service.delete_product(farmer_id, product_id)

        # Assert
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_delete_product_unauthorized(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_active_product: ProductInDB,
    ) -> None:
        """TC-008-10: Farmer cannot delete another farmer's product."""
        # Arrange
        different_farmer_id = uuid4()
        product_id = mock_active_product.id
        mock_repository.get_by_farmer_and_id.return_value = None

        # Act
        result = product_service.delete_product(different_farmer_id, product_id)

        # Assert
        assert result.success is False
        assert "not found" in result.error.lower() or "permission" in result.error.lower()

    def test_delete_archived_product_success(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_archived_product: ProductInDB,
    ) -> None:
        """TC-008-11: Farmer can delete an archived product."""
        # Arrange
        farmer_id = mock_archived_product.farmer_id
        product_id = mock_archived_product.id

        mock_repository.get_by_farmer_and_id.return_value = mock_archived_product
        mock_repository.has_pending_orders.return_value = False
        mock_repository.delete.return_value = True

        # Act
        result = product_service.delete_product(farmer_id, product_id)

        # Assert
        assert result.success is True
        mock_repository.delete.assert_called_once_with(product_id)
