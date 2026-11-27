from pwdlib import PasswordHash

password_hasher = PasswordHash.recommended()
dummy_hash = password_hasher.hash("not-a-real-account-password")
