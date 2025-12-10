"""Tests for product update functionality (US-007)."""

from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.models.product import (
    ProductCategory,
    ProductInDB,
    ProductStatus,
    ProductUnit,
    ProductUpdate,
    Seasonality,
)
from app.repositories.product import ProductRepository
from app.services.product import ProductService


@pytest.fixture
def mock_product() -> ProductInDB:
    """Create a mock product for testing."""
    return ProductInDB(
        id=uuid4(),
        farmer_id=uuid4(),
        name="Organic Tomatoes",
        category=ProductCategory.VEGETABLES,
        description="Fresh organic tomatoes grown without pesticides",
        price=Decimal("4.99"),
        unit=ProductUnit.LB,
        quantity=100,
        seasonality=[Seasonality.SUMMER],
        images=["https://example.com/tomato1.jpg"],
        status=ProductStatus.ACTIVE,
        version=1,
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


class TestProductUpdate:
    """Test cases for product update functionality."""

    def test_update_product_name_success(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_product: ProductInDB,
    ) -> None:
        """TC-007-1: Farmer successfully updates product name."""
        # Arrange
        farmer_id = mock_product.farmer_id
        product_id = mock_product.id
        updated_product = ProductInDB(
            **{**mock_product.model_dump(), "name": "Heirloom Tomatoes", "version": 2}
        )

        mock_repository.get_by_farmer_and_id.return_value = mock_product
        mock_repository.update_with_version.return_value = (updated_product, None)

        update_data = ProductUpdate(name="Heirloom Tomatoes", version=1)

        # Act
        result = product_service.update_product(farmer_id, product_id, update_data)

        # Assert
        assert result.success is True
        assert result.product is not None
        assert result.product.name == "Heirloom Tomatoes"
        assert result.product.version == 2
        mock_repository.update_with_version.assert_called_once()

    def test_update_product_price_success(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_product: ProductInDB,
    ) -> None:
        """TC-007-2: Farmer updates product price."""
        # Arrange
        farmer_id = mock_product.farmer_id
        product_id = mock_product.id
        new_price = Decimal("5.49")
        updated_product = ProductInDB(
            **{**mock_product.model_dump(), "price": new_price, "version": 2}
        )

        mock_repository.get_by_farmer_and_id.return_value = mock_product
        mock_repository.update_with_version.return_value = (updated_product, None)

        update_data = ProductUpdate(price=new_price, version=1)

        # Act
        result = product_service.update_product(farmer_id, product_id, update_data)

        # Assert
        assert result.success is True
        assert result.product is not None
        assert result.product.price == new_price

    def test_update_product_seasonality(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_product: ProductInDB,
    ) -> None:
        """TC-007-5: Farmer updates product seasonality."""
        # Arrange
        farmer_id = mock_product.farmer_id
        product_id = mock_product.id
        new_seasonality = [Seasonality.YEAR_ROUND]
        updated_product = ProductInDB(
            **{**mock_product.model_dump(), "seasonality": new_seasonality, "version": 2}
        )

        mock_repository.get_by_farmer_and_id.return_value = mock_product
        mock_repository.update_with_version.return_value = (updated_product, None)

        update_data = ProductUpdate(seasonality=new_seasonality, version=1)

        # Act
        result = product_service.update_product(farmer_id, product_id, update_data)

        # Assert
        assert result.success is True
        assert result.product is not None
        assert result.product.seasonality == new_seasonality

    def test_update_fails_without_version(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_product: ProductInDB,
    ) -> None:
        """Update should fail when version is not provided."""
        # Arrange
        farmer_id = mock_product.farmer_id
        product_id = mock_product.id
        mock_repository.get_by_farmer_and_id.return_value = mock_product

        update_data = ProductUpdate(name="New Name")  # No version

        # Act
        result = product_service.update_product(farmer_id, product_id, update_data)

        # Assert
        assert result.success is False
        assert "version is required" in result.error.lower()

    def test_update_fails_with_version_conflict(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_product: ProductInDB,
    ) -> None:
        """Update should fail when version doesn't match (optimistic locking)."""
        # Arrange
        farmer_id = mock_product.farmer_id
        product_id = mock_product.id

        mock_repository.get_by_farmer_and_id.return_value = mock_product
        mock_repository.update_with_version.return_value = (
            None,
            "Version conflict: expected 2, found 1. Product was modified by another user.",
        )

        update_data = ProductUpdate(name="New Name", version=2)  # Wrong version

        # Act
        result = product_service.update_product(farmer_id, product_id, update_data)

        # Assert
        assert result.success is False
        assert "version conflict" in result.error.lower()

    def test_update_fails_product_not_found(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
    ) -> None:
        """Update should fail when product is not found."""
        # Arrange
        farmer_id = uuid4()
        product_id = uuid4()
        mock_repository.get_by_farmer_and_id.return_value = None

        update_data = ProductUpdate(name="New Name", version=1)

        # Act
        result = product_service.update_product(farmer_id, product_id, update_data)

        # Assert
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_update_fails_unauthorized(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_product: ProductInDB,
    ) -> None:
        """Update should fail when farmer doesn't own the product."""
        # Arrange
        different_farmer_id = uuid4()
        product_id = mock_product.id
        mock_repository.get_by_farmer_and_id.return_value = None

        update_data = ProductUpdate(name="New Name", version=1)

        # Act
        result = product_service.update_product(
            different_farmer_id, product_id, update_data
        )

        # Assert
        assert result.success is False
        assert "not found" in result.error.lower() or "permission" in result.error.lower()


class TestProductImageManagement:
    """Test cases for product image management."""

    def test_add_images_success(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_product: ProductInDB,
    ) -> None:
        """TC-007-3: Farmer adds new image to existing product."""
        # Arrange
        farmer_id = mock_product.farmer_id
        product_id = mock_product.id
        new_image = "https://example.com/tomato2.jpg"

        updated_product = ProductInDB(
            **{
                **mock_product.model_dump(),
                "images": mock_product.images + [new_image],
            }
        )

        mock_repository.get_by_farmer_and_id.return_value = mock_product
        mock_repository.add_images.return_value = updated_product

        # Act
        result = product_service.add_product_images(
            farmer_id, product_id, [new_image]
        )

        # Assert
        assert result.success is True
        assert result.product is not None
        assert len(result.product.images) == 2
        assert new_image in result.product.images

    def test_add_images_exceeds_limit(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_product: ProductInDB,
    ) -> None:
        """Adding images should fail when exceeding the 5 image limit."""
        # Arrange
        farmer_id = mock_product.farmer_id
        product_id = mock_product.id

        # Product already has 4 images
        product_with_4_images = ProductInDB(
            **{
                **mock_product.model_dump(),
                "images": [
                    "https://example.com/1.jpg",
                    "https://example.com/2.jpg",
                    "https://example.com/3.jpg",
                    "https://example.com/4.jpg",
                ],
            }
        )
        mock_repository.get_by_farmer_and_id.return_value = product_with_4_images

        # Try to add 2 more images
        new_images = [
            "https://example.com/5.jpg",
            "https://example.com/6.jpg",
        ]

        # Act
        result = product_service.add_product_images(farmer_id, product_id, new_images)

        # Assert
        assert result.success is False
        assert "max 5" in result.error.lower() or "cannot add" in result.error.lower()

    def test_remove_image_success(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_product: ProductInDB,
    ) -> None:
        """TC-007-4: Farmer removes image from product."""
        # Arrange
        farmer_id = mock_product.farmer_id
        product_id = mock_product.id
        image_to_remove = mock_product.images[0]

        updated_product = ProductInDB(
            **{**mock_product.model_dump(), "images": []}
        )

        mock_repository.get_by_farmer_and_id.return_value = mock_product
        mock_repository.remove_image.return_value = updated_product

        # Act
        result = product_service.remove_product_image(
            farmer_id, product_id, image_to_remove
        )

        # Assert
        assert result.success is True
        assert result.product is not None
        assert len(result.product.images) == 0

    def test_remove_image_not_found(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_product: ProductInDB,
    ) -> None:
        """Removing non-existent image should fail."""
        # Arrange
        farmer_id = mock_product.farmer_id
        product_id = mock_product.id
        mock_repository.get_by_farmer_and_id.return_value = mock_product

        # Act
        result = product_service.remove_product_image(
            farmer_id, product_id, "https://example.com/nonexistent.jpg"
        )

        # Assert
        assert result.success is False
        assert "not found" in result.error.lower()


class TestProductUpdateValidation:
    """Test cases for product update validation (TC-007-6)."""

    def test_update_with_empty_name_fails(self) -> None:
        """TC-007-6: Update fails with invalid data (empty name)."""
        # Pydantic validation should fail for empty name
        with pytest.raises(ValueError):
            ProductUpdate(name="", version=1)

    def test_update_with_negative_price_fails(self) -> None:
        """Update should fail with negative price."""
        with pytest.raises(ValueError):
            ProductUpdate(price=Decimal("-1.00"), version=1)

    def test_update_with_negative_quantity_fails(self) -> None:
        """Update should fail with negative quantity."""
        with pytest.raises(ValueError):
            ProductUpdate(quantity=-1, version=1)

    def test_update_with_valid_partial_data(self) -> None:
        """Partial update with valid data should succeed."""
        update = ProductUpdate(
            name="New Name",
            version=1,
        )
        assert update.name == "New Name"
        assert update.price is None
        assert update.quantity is None


class TestGetProduct:
    """Test cases for getting product details (AC-007-1)."""

    def test_get_product_success(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
        mock_product: ProductInDB,
    ) -> None:
        """Farmer can access product details for editing."""
        # Arrange
        farmer_id = mock_product.farmer_id
        product_id = mock_product.id
        mock_repository.get_by_farmer_and_id.return_value = mock_product

        # Act
        result = product_service.get_product(farmer_id, product_id)

        # Assert
        assert result.success is True
        assert result.product is not None
        assert result.product.id == product_id
        assert result.product.name == mock_product.name
        assert result.product.version == mock_product.version

    def test_get_product_not_found(
        self,
        product_service: ProductService,
        mock_repository: MagicMock,
    ) -> None:
        """Getting non-existent product should fail."""
        # Arrange
        farmer_id = uuid4()
        product_id = uuid4()
        mock_repository.get_by_farmer_and_id.return_value = None

        # Act
        result = product_service.get_product(farmer_id, product_id)

        # Assert
        assert result.success is False
        assert "not found" in result.error.lower()
