import pytest
from order import order

@pytest.fixture
def client():
    order.config['TESTING'] = True
    with order.test_client() as client:
        yield client

def test_add_to_cart(client):
    response = client.post('/add_to_cart', data={'product_id': '5', 'quantity': '3'}, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/product_list')

    with client.session_transaction() as session:
        cart = session.get('cart', {})
        assert cart.get('5') == 3
