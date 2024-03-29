# import the necessary modules
from flask import Flask, render_template, request , session, redirect, url_for
from cryptography.fernet import Fernet
from Crypto.Cipher import DES3, AES,PKCS1_OAEP
from Crypto.Random import get_random_bytes
from Crypto.PublicKey import RSA
import os
import hashlib
import base64

# Initialize flask
app = Flask(__name__)
app.secret_key = 'secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads/'

# User data (username and password hash) dictionary
users = {}

# Generate a new RSA key pair
rsa_key = RSA.generate(2048)

# Use the public key to create a new PKCS1_OAEP cipher object
cipher_rsa = PKCS1_OAEP.new(rsa_key.publickey())

# Generate a new encryption key
key = Fernet.generate_key()
cipher_suite = Fernet(key)
des_key = DES3.new('1234567890123456', DES3.MODE_EAX)

# Define the encryption key
aes_key_128 = b'Sixteen byte key'
aes_key_256 = get_random_bytes(32)  # 32 bytes = 256 bits

cipher_rsa = PKCS1_OAEP.new(rsa_key.publickey())
ciphertext = cipher_rsa.encrypt(aes_key_256)


# Create upload folder if it does not exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
    
# Login required decorator
def login_required(func):
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper

@app.route('/')
def home():
    return render_template('index.html')
    
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

        if username in users:
            return render_template('signup.html', error='Username already taken')

        users[username] = password_hash
        session['username'] = username
        return redirect(url_for('home'))
    else:
        return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

        if username not in users:
            return render_template('login.html', error='Username not found')

        if users[username] != password_hash:
            return render_template('login.html', error='Incorrect password')

        session['username'] = username
        return redirect(url_for('home'))
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        security_question = request.form['security_question']
        security_answer = request.form['security_answer']

        if username not in users:
            return render_template('forgot_password.html', error='Username not found')

        if security_question != 'What was the name of your first pet?' or security_answer != 'Fluffy':
            return render_template('forgot_password.html', error='Incorrect security question or answer')

        session['username'] = username
        session['security_question'] = security_question
        session['security_answer'] = security_answer
        return redirect(url_for('reset_password'))
    else:
        return render_template('forgot_password.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if 'username' not in session or 'security_question' not in session or 'security_answer' not in session:
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        username = session['username']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            return render_template('reset_password.html', error='Passwords do not match')

        password_hash = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
        users[username] = password_hash
        session.pop('username', None)
        session.pop('security_question', None)
        session.pop('security_answer', None)
        return redirect(url_for('login'))
    else:
        username = session['username']
        security_question = session['security_question']
        security_answer = session['security_answer']
        return render_template('reset_password.html', username=username, security_question=security_question, security_answer=security_answer)


@app.route('/encrypt', methods=['POST'])
def encrypt():
    if 'username' not in session:
        return redirect(url_for('login'))
    f = request.files['file']
    filename = f.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    f.save(filepath)

    algorithm = request.form['algorithm']
    if algorithm == 'des':
        # Encrypt the file using 3-DES
        with open(filepath, 'rb') as file:
            data = file.read()
            encrypted_data = cipher_suite.encrypt(data)
        with open(filepath, 'wb') as file:
            file.write(encrypted_data)
 
    elif algorithm == 'aes128':
        # Encrypt the file using AES-128 in CBC mode
        with open(filepath, 'rb') as file:
            data = file.read()
            iv = b"\0" * AES.block_size  # Set the initialization vector to all zeros
            cipher = AES.new(aes_key_128, AES.MODE_CBC, iv)
            padded_data = data + b"\0" * (AES.block_size - len(data) % AES.block_size)  # Padded to the block size
            encrypted_data = cipher.encrypt(padded_data)
        with open(filepath, 'wb') as file:
            file.write(encrypted_data)
    elif algorithm == 'aes256':
        # Encrypt the file using AES-256 in CFB mode
        with open(filepath, 'rb') as file:
            data = file.read()
            iv = b"\0" * AES.block_size  # Set the initialization vector to all zeros
            cipher = AES.new(aes_key_256, AES.MODE_CFB, iv)
            encrypted_data = cipher.encrypt(data)
        with open(filepath, 'wb') as file:
            file.write(encrypted_data)
    elif algorithm == 'rsa':
        # Encrypt the file using RSA public key encryption
        with open(filepath, 'rb') as file:
            data = file.read()
            cipher = PKCS1_OAEP.new(rsa_key.publickey())
            encrypted_data = cipher.encrypt(data)
        with open(filepath, 'wb') as file:
            file.write(encrypted_data)
   
    return 'File encrypted successfully!'


    
@app.route('/decrypt', methods=['POST'])
def decrypt():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Get the selected algorithm from the form
    algorithm = request.form.get('algorithm')

    # Get the uploaded file
    f = request.files['file']
    filename = f.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    f.save(filepath)

    # Decrypt the file based on the selected algorithm
    if algorithm == 'des':
        with open(filepath, 'rb') as file:
            encrypted_data = file.read()
            decrypted_data = cipher_suite.decrypt(encrypted_data)
        
        with open(filepath, 'wb') as file:
            file.write(decrypted_data)
            
          
      
    elif algorithm == 'aes128':
        with open(filepath, 'rb') as file:
            data = file.read()
            iv = b"\0" * AES.block_size  # Set the initialization vector to all zeros
            cipher = AES.new(aes_key_128, AES.MODE_CBC, iv)
            decrypted_data = cipher.decrypt(data)
            # Remove the padding
            decrypted_data = decrypted_data.rstrip(b"\0")
        with open(filepath, 'wb') as file:
            file.write(decrypted_data)

    elif algorithm == 'aes256':
        with open(filepath, 'rb') as file:
            data = file.read()
            iv = b"\0" * AES.block_size  # Set the initialization vector to all zeros
            cipher = AES.new(aes_key_256, AES.MODE_CFB, iv)
            decrypted_data = cipher.decrypt(data)
        with open(filepath, 'wb') as file:
            file.write(decrypted_data)

    elif algorithm == 'rsa':
        with open(filepath, 'rb') as file:
            data = file.read()
            cipher = PKCS1_OAEP.new(rsa_key)
            decrypted_data = cipher.decrypt(data)
        with open(filepath, 'wb') as file:
            file.write(decrypted_data)

    return 'File decrypted successfully!'


@app.route('/hash', methods=['POST'])
def hash():
    if 'username' not in session:
        return redirect(url_for('login'))
    f = request.files['file']
    filename = f.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    f.save(filepath)

    with open(filepath, 'rb') as file:
        data = file.read()
        hash_object = hashlib.sha256(data)
        hex_dig = hash_object.hexdigest()

    return f'The hash of {filename} is: {hex_dig}'

@app.route('/compare', methods=['POST'])
def compare():
    if 'username' not in session:
        return redirect(url_for('login'))
    f1 = request.files['file1']
    f2 = request.files['file2']
    filename1 = f1.filename
    filename2 = f2.filename
    filepath1 = os.path.join(app.config['UPLOAD_FOLDER'], filename1)
    filepath2 = os.path.join(app.config['UPLOAD_FOLDER'], filename2)
    f1.save(filepath1)
    f2.save(filepath2)

    with open(filepath1, 'rb') as file1:
        data1 = file1.read()
        hash_object1 = hashlib.sha256(data1)
        hex_dig1 = hash_object1.hexdigest()

    with open(filepath2, 'rb') as file2:
        data2 = file2.read()
        hash_object2 = hashlib.sha256(data2)
        hex_dig2 = hash_object2.hexdigest()

    if hex_dig1 == hex_dig2:
        return f'The hashes of {filename1} and {filename2} match!'
    else:
        return f'The hashes of {filename1} and {filename2} do not match!'



if __name__ == '__main__':
    app.run(debug=True)
