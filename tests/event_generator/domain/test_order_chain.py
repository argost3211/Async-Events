from event_generator.domain.order_chain import OrderChain


def test_initial_state_next_event_type_is_order_created():
    chain = OrderChain(order_id="ord-1", user_id="user-1")
    assert chain.next_event_type() == "order_created"
    assert chain.completed is False
    assert chain.cancelled is False


def test_advance_once_next_event_type_is_order_paid():
    chain = OrderChain(order_id="ord-1", user_id="user-1")
    chain.advance()
    assert chain.next_event_type() == "order_paid"


def test_advance_through_full_chain():
    chain = OrderChain(order_id="ord-1", user_id="user-1")
    assert chain.next_event_type() == "order_created"
    chain.advance()
    assert chain.next_event_type() == "order_paid"
    chain.advance()
    assert chain.next_event_type() == "order_shipped"
    chain.advance()
    assert chain.next_event_type() == "order_delivered"
    chain.advance()
    assert chain.next_event_type() is None
    assert chain.completed is True


def test_cancel_sets_cancelled_and_completed():
    chain = OrderChain(order_id="ord-1", user_id="user-1")
    chain.advance()
    chain.cancel()
    assert chain.cancelled is True
    assert chain.completed is True
    assert chain.next_event_type() == "order_cancelled"


def test_cancel_from_initial_state():
    chain = OrderChain(order_id="ord-1", user_id="user-1")
    chain.cancel()
    assert chain.cancelled is True
    assert chain.completed is True
    assert chain.next_event_type() == "order_cancelled"


def test_order_id_and_user_id_stored():
    chain = OrderChain(order_id="my-order-99", user_id="user-42")
    assert chain.order_id == "my-order-99"
    assert chain.user_id == "user-42"
