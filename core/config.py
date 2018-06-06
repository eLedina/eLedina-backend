# coding=utf-8
import configparser
import os
import shutil

# Verify data dir exists
DATA_DIR = os.path.join("..", "data")

REDIS_CONFIG_PATH = os.path.join(DATA_DIR, "redis.ini")
AUTH_CONFIG_PATH = os.path.join(DATA_DIR, "auth.ini")


if not os.path.isdir(DATA_DIR):
    os.mkdir(DATA_DIR)

# Verify redis.ini exists
if not os.path.exists(REDIS_CONFIG_PATH):
    shutil.copy(os.path.join(DATA_DIR, "redis_example.ini"), REDIS_CONFIG_PATH)
    print("Error: redis.ini is missing! Please fill out the copied one.")
    exit(3)

# Verify auth.ini exists
if not os.path.exists(AUTH_CONFIG_PATH):
    shutil.copy(os.path.join(DATA_DIR, "auth_example.ini"), AUTH_CONFIG_PATH)
    print("Error: auth.ini is missing! Please fill out the copied one.")
    exit(3)

redis_config = configparser.ConfigParser()
redis_config.read(REDIS_CONFIG_PATH)

auth_config = configparser.ConfigParser()
auth_config.read(AUTH_CONFIG_PATH)

# For convenience
SALT = auth_config.read("Crypto", "salt")
ROUNDS = auth_config.read("Crypto", "rounds")
