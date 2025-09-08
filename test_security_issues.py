#!/usr/bin/env python3
"""
Test file with intentional security issues for bandit testing.
This file should trigger various bandit security warnings.
"""

import os
import subprocess
import hashlib

# B101: Test for assert usage
def test_function(value):
    assert value > 0, "Value must be positive"  # This should trigger B101
    return value * 2

# B102: Test for exec usage
def dangerous_exec():
    user_input = "print('hello')"
    exec(user_input)  # This should trigger B102

# B103: Test for file permissions
def create_file():
    os.chmod("test.txt", 0o777)  # This should trigger B103

# B104: Test for binding to all interfaces
def start_server():
    import socket
    s = socket.socket()
    s.bind(('0.0.0.0', 8080))  # This should trigger B104

# B303: Test for MD5 usage
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()  # This should trigger B303

# B602: Test for subprocess with shell=True
def run_command(cmd):
    subprocess.call(cmd, shell=True)  # This should trigger B602

# B608: Test for SQL injection potential
def query_database(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"  # This should trigger B608
    return query

if __name__ == "__main__":
    print("This file contains intentional security issues for testing")
