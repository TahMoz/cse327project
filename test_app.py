
import pytest
from app import app  

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_route(client):
    """Test the home page"""
    response = client.get('/')
    assert response.status_code == 200

def test_products_route(client):
    """Test the products page"""
    response = client.get('/products')
    assert response.status_code == 200

#  more tests for other 
def test_about_route(client):
    """Test about page if it exists"""
    response = client.get('/about')
    assert response.status_code in (200, 404)  # Allow 404 if not implemented
