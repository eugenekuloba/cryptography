## **File Encryption and Hashing with Flask**

This is a Flask web application that provides file encryption and hashing functionalities. It uses the cryptography and hashlib libraries for encryption and hashing, respectively.

### *Prerequisites*

<ul>
  <li>Python 3.7 or higher</li>
 </ul>


### *Installation*

<ul>
  <li>Clone this repository: git clone https://github.com/eugenekuloba/cryptography</li>
  <li>cd cryptography</li>
  <li>pip install -r requirements.txt</li>
</ul>

### *Usage*

<ul>
  <li>Start the Flask server: python app.py</li>
  <li>Open a web browser and go to http://localhost:5000/</li>
  <li>Select the file that you want to encrypt or hash, and click the appropriate button.</li>
  <li>The encrypted or hashed file will be saved in the uploads directory.</li>
</ul>

### *Debugging*

If you encounter any errors, you can enable debug mode by setting the debug flag to True in the app.run() method:

if __name__ == '__main__':
    app.run(debug=True)