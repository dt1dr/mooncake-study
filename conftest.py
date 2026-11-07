"""Offline tests: any accidental Python socket connection is a test failure."""

import socket

import pytest


@pytest.fixture(autouse=True)
def no_network(request, monkeypatch):
    if request.node.get_closest_marker("integration"):
        return  # Linux Store integration tests use local sockets only.

    def forbidden(*args, **kwargs):
        raise AssertionError("Tests must not access the network; stage data before testing")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
