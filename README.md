# E-Commerce Platform

Professional Django REST Framework e-commerce backend with comprehensive admin management system and JWT authentication.

## 🚀 Features

### Core Functionality
- **Product Management**: Complete CRUD operations with categories, pricing, and image galleries
- **Order System**: Sequential order ID generation (YYYYMMDD-XXXXXX format)
- **User Management**: Custom user model with JWT authentication
- **Category System**: Product categorization
- **Shopping Cart**: Full cart management functionality

### Authentication & Security
- **JWT Authentication**: Access tokens (60 minutes) and refresh tokens (7 days)
- **Custom User Model**: Email-based authentication
- **Permission System**: Role-based access control
- **Secure API Endpoints**: Protected routes with proper authorization

### Admin Panel Features
- **Professional Admin Interface**: Enhanced Django admin with custom actions
- **Advanced Filtering**: Multiple filter options for all models
- **Bulk Operations**: Mass update capabilities for products and orders
- **Statistics Dashboard**: Comprehensive analytics and reporting
- **Image Preview**: In-admin image preview functionality

### Performance Optimization
- **Database Indexing**: Strategic indexes for optimal query performance
- **Query Optimization**: Efficient database queries with select_related and prefetch_related
- **Pagination**: Optimized pagination for large datasets
- **Caching Ready**: Prepared for Redis integration

## 🛠 Tech Stack

- **Backend**: Django 4.x + Django REST Framework
- **Database**: PostgreSQL with optimized indexing
- **Authentication**: Django Simple JWT
- **API Documentation**: Swagger/OpenAPI integration
- **Containerization**: Docker & Docker Compose
- **Web Server**: Nginx (production ready)

## 📁 Project Structure

```
ecommerce/
├── apps/
│   ├── api/                 # API configuration
│   ├── cart/               # Shopping cart functionality
│   ├── category/           # Product categories
│   ├── order/              # Order management
│   ├── product/            # Product catalog
│   └── users/              # User management
├── core/                   # Project settings
├── media/                  # User uploaded files
├── static/                 # Static files
├── nginx/                  # Nginx configuration
├── docker-compose.yml      # Docker services
├── Dockerfile             # Docker image
└── requirements.txt       # Python dependencies
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 13+
- Docker & Docker Compose (optional)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Abdulazizovv/ecommerce.git
cd ecommerce
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment configuration**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

5. **Database setup**
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

6. **Run development server**
```bash
python manage.py runserver
```

### Docker Deployment

1. **Build and run with Docker Compose**
```bash
docker-compose up --build
```

2. **Create superuser (in Docker)**
```bash
docker-compose exec web python manage.py createsuperuser
```

## 📚 API Documentation

### Authentication Endpoints
```
POST /api/auth/login/          # User login
POST /api/auth/register/       # User registration
POST /api/auth/refresh/        # Refresh token
POST /api/auth/logout/         # User logout
```

### Product Endpoints
```
GET    /api/products/          # List products
POST   /api/products/          # Create product
GET    /api/products/{id}/     # Product details
PUT    /api/products/{id}/     # Update product
DELETE /api/products/{id}/     # Delete product
```

### Order Endpoints
```
GET    /api/orders/            # List user orders
POST   /api/orders/            # Create order
GET    /api/orders/{id}/       # Order details
PUT    /api/orders/{id}/       # Update order
```

### Category Endpoints
```
GET    /api/categories/        # List categories
POST   /api/categories/        # Create category
GET    /api/categories/{id}/   # Category details
```

### Cart Endpoints
```
GET    /api/cart/              # Get cart items
POST   /api/cart/add/          # Add to cart
PUT    /api/cart/update/       # Update cart item
DELETE /api/cart/remove/       # Remove from cart
```

## 🔧 Admin Panel

Access the admin panel at `/admin/` with superuser credentials.

### Admin Features
- **Product Management**: Bulk actions, advanced filtering, image preview
- **Order Management**: Status updates, customer information, order analytics
- **User Management**: User statistics, bulk operations, activity tracking
- **Category Management**: Hierarchical structure, SEO optimization
- **Statistics Dashboard**: Sales analytics, user metrics, performance data

## 🗄 Database Schema

### Key Models
- **User**: Custom user model with email authentication
- **Product**: Product catalog with pricing, categories, and images
- **Category**: Product categorization system
- **Order**: Order management with sequential ID generation
- **OrderItem**: Individual items within orders
- **Cart**: Shopping cart functionality

### Database Indexes
Optimized indexes for:
- Product searches and filtering
- Order queries by date and status
- User lookups and authentication
- Category-based product filtering

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **CORS Configuration**: Proper cross-origin resource sharing
- **Input Validation**: Comprehensive data validation
- **SQL Injection Protection**: Parameterized queries
- **XSS Protection**: Output sanitization

## 📊 Performance

- **Database Optimization**: Strategic indexing for common queries
- **Query Efficiency**: Optimized ORM usage
- **Pagination**: Efficient data loading
- **Caching Ready**: Prepared for Redis integration

## 🧪 Testing

Run tests with:
```bash
python manage.py test
```

## 📝 Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# JWT Settings
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_LIFETIME=60  # minutes
JWT_REFRESH_TOKEN_LIFETIME=7  # days

# Django Settings
DEBUG=False
SECRET_KEY=your-django-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Media Files
MEDIA_URL=/media/
STATIC_URL=/static/
```

## 🚀 Deployment

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Set up PostgreSQL database
- [ ] Configure static file serving
- [ ] Set up media file storage
- [ ] Configure email backend
- [ ] Set up monitoring and logging

### Docker Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Abdulazizov**
- GitHub: [@Abdulazizovv](https://github.com/Abdulazizovv)
- Email: [aqllibola567@gmail.com](mailto:aqllibola567@gmail.com)

## 🙏 Acknowledgments

- Django and DRF communities
- Contributors and testers
- Open source libraries used in this project

---

**Built with ❤️ using Django REST Framework**
