# Farm-to-Table Marketplace

## Project Overview

A Farm-to-Table Marketplace platform that connects consumers directly with local farmers, offering fresh, seasonal produce and products. The platform promotes transparency, convenience, and sustainable agriculture.

## Key Stakeholders

- **Consumers**: End users who browse, purchase, and receive farm products
- **Farmers**: Producers who list, manage, and sell their farm products

## Architecture

### Tech Stack (Recommended)

- **Frontend**: React/Next.js with TypeScript
- **Backend**: Node.js/Express or Python/FastAPI
- **Database**: PostgreSQL with proper indexing
- **Authentication**: JWT-based with secure password hashing (bcrypt)
- **Storage**: Cloud storage for product images (S3 or similar)
- **API**: RESTful API with versioning (v1)

### API Base Path

All API endpoints follow the pattern: `/api/v1/...`

## Core Features (KATA Scope)

### User Management
- User registration and authentication (US-001, US-002)
- User profile management (US-003)
- Farmer registration (US-004)
- Farmer profile setup (US-005)

### Product Management
- Add product listing (US-006)
- Update product listing (US-007)
- Remove product listing (US-008)
- Availability management (US-009)
- Pricing management (US-010)

### Product Discovery
- Product browsing (US-011)
- Product search and filtering (US-012)

## Data Models

### User
- id, email, password_hash, full_name, phone, profile_picture
- address (street, city, state, zip), delivery_instructions
- payment_method, billing_address
- dietary_preferences, communication_preferences
- email_verified, created_at, updated_at

### Farmer (extends User)
- farm_name, farm_address, farm_description
- farming_practices (Organic, Sustainable, etc.)
- farm_media (pictures, videos)
- bank_account_details

### Product
- id, farmer_id (FK), name, category, description
- price, unit (lb, kg, each, dozen, bunch)
- quantity, seasonality (Spring, Summer, Fall, Winter, Year-round)
- images (array), status (active, inactive, archived)
- created_at, updated_at

### Categories
- Vegetables, Fruits, Dairy, Meat, Eggs, Honey, Herbs, Grains, Other

## Development Guidelines

### Security Requirements
- Secure password hashing (bcrypt or similar)
- Rate limiting on authentication endpoints
- Email verification with 24-hour expiry
- Input validation on both frontend and backend
- Protect against OWASP Top 10 vulnerabilities

### Image Handling
- Supported formats: JPG, PNG, WebP
- Optimize on upload (resize, compress)
- Maximum 5 images per product
- Implement lazy loading on frontend

### UI/UX Principles
- User-friendly dashboard for farmers
- Clear validation error messages
- Confirmation prompts for destructive actions
- Responsive design for mobile
- High-quality images and detailed descriptions

### Pagination
- Default 20 items per page
- Support for infinite scroll or pagination

## User Stories Location

All user stories are in `/user_stories/` directory in JSON format:
- US-001 to US-003: User Profile Management
- US-004 to US-005: Farmer Profile Management
- US-006 to US-010: Product Listing Management
- US-011 to US-012: Product Browsing and Search

Each user story includes:
- Acceptance criteria (Given/When/Then format)
- Technical notes
- API endpoints
- Test cases (positive, negative, boundary, security)

## Testing Strategy

### Test Types Required
- **Positive tests**: Valid flows succeed
- **Negative tests**: Invalid inputs handled gracefully
- **Boundary tests**: Edge cases (max lengths, limits)
- **Security tests**: Password storage, injection prevention
- **UI tests**: Lazy loading, responsiveness

### Test Case Structure
```json
{
  "id": "TC-XXX-X",
  "type": "positive|negative|boundary|security|ui|edge",
  "title": "Description",
  "preconditions": ["..."],
  "steps": ["..."],
  "expected_result": "..."
}
```

## KATA Challenge Focus

1. Integrate GenAI capabilities across SDLC phases
2. Focus on MVP with core working features first
3. Apply design principles: SOLID, KISS, YAGNI
4. Prioritize "Must Have" features marked with * in requirements
5. Produce artifacts: prompts, conversations, code, test cases, requirements

## Common Commands

```bash
# Run tests
npm test

# Start development server
npm run dev

# Build for production
npm run build

# Lint code
npm run lint
```

## File Naming Conventions

- User stories: `US-XXX-feature-name.json`
- Components: PascalCase (e.g., `ProductCard.tsx`)
- Utilities: camelCase (e.g., `formatPrice.ts`)
- API routes: kebab-case (e.g., `/api/v1/farmer-products`)
