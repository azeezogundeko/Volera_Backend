# Product APIs

### **GET /api/products**
Get all products with pagination and filters.

**Response**
```typescript
{
  products: {
    id: number;
    title: string;
    description: string;
    image: string;
    price: number;
    rating: number;
    stores: {
      name: string;
      price: number;
      link: string;
    }[];
    specifications: Record<string, string>;
    features: string[];
  }[];
  total: number;
  page: number;
  pageSize: number;
}
```

### **GET /api/products/:id**
Get single product details.

**Response**
```typescript
{
  id: number;
  title: string;
  description: string;
  image: string;
  price: number;
  rating: number;
  stores: {
    name: string;
    price: number;
    link: string;
  }[];
  specifications: Record<string, string>;
  features: string[];
  priceHistory: {
    date: string;
    price: number;
  }[];
}
```

# Search APIs

### **POST /api/search**
Text-based search.

**Request**
```typescript
{
  query: string;
  filters?: {
    store?: string;
    minPrice?: number;
    maxPrice?: number;
    rating?: number;
    category?: string;
  };
  page?: number;
  pageSize?: number;
}
```

**Response**
```typescript
{
  products: Product[];
  total: number;
  page: number;
  pageSize: number;
}
```

### **POST /api/search/image**
Image-based search.

**Request**
```typescript
{
  image: File;
  filters?: {
    store?: string;
    minPrice?: number;
    maxPrice?: number;
  };
}
```

# Price Watch APIs

### **POST /api/price-watch**
Create price alert.

**Request**
```typescript
{
  productId: number;
  targetPrice: number;
  email: string;
}
```

### **GET /api/price-watch**
Get user's price alerts.

**Response**
```typescript
{
  alerts: {
    id: number;
    productId: number;
    productTitle: string;
    currentPrice: number;
    targetPrice: number;
    status: 'active' | 'triggered' | 'expired';
    createdAt: string;
  }[];
}
```

# Review APIs

### **GET /api/products/:id/reviews**
Get product reviews.

**Response**
```typescript
{
  reviews: {
    id: number;
    userId: string;
    userName: string;
    rating: number;
    comment: string;
    createdAt: string;
    helpful: number;
  }[];
  averageRating: number;
  totalReviews: number;
}
```

### **POST /api/products/:id/reviews**
Create review.

**Request**
```typescript
{
  rating: number;
  comment: string;
}
```

# Store APIs

### **GET /api/stores**
Get all supported stores.

**Response**
```typescript
{
  stores: {
    id: number;
    name: string;
    logo: string;
    active: boolean;
  }[];
}
```

### **GET /api/stores/:id/products/:productId**
Get product price and availability from specific store.

**Response**
```typescript
{
  available: boolean;
  price: number;
  shipping: number;
  link: string;
  lastUpdated: string;
}
```

# Price History APIs

### **GET /api/products/:id/price-history**
Get price history for a product.

**Request**
```typescript
{
  timeframe: '1w' | '1m' | '3m' | '6m' | '1y' | 'all';
}
```

**Response**
```typescript
{
  history: {
    date: string;
    price: number;
    store: string;
  }[];
  lowestPrice: number;
  highestPrice: number;
  averagePrice: number;
}
```

# User Preferences API

### **GET /api/user/preferences**
Get user preferences.

**Response**
```typescript
{
  preferredStores: string[];
  preferredCurrency: string;
  notifications: {
    email: boolean;
    push: boolean;
    priceDrops: boolean;
    backInStock: boolean;
  };
}
```

### **PUT /api/user/preferences**
Update user preferences.

**Request**
```typescript
{
  preferredStores?: string[];
  preferredCurrency?: string;
  notifications?: {
    email?: boolean;
    push?: boolean;
    priceDrops?: boolean;
    backInStock?: boolean;
  };
}
```

---

# Key Features to Implement in Backend
- **Authentication and Authorization**
- **Real-time Price Tracking**
- **Image Recognition for Visual Search**
- **Price History Tracking and Analytics**
- **Email Notifications**
- **Rate Limiting and API Security**
- **Caching System for Frequent Data**
- **Error Handling and Logging**

# Recommended Technologies
- **Database**: PostgreSQL for structured data, Redis for caching.
- **Image Processing**: TensorFlow or AWS Rekognition for visual search.
- **Search Engine**: Elasticsearch for efficient text search.
- **Queue System**: Redis or RabbitMQ for notifications.
- **API Documentation**: Swagger/OpenAPI.
- **Monitoring**: Prometheus and Grafana.
