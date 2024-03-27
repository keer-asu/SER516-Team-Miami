function checkInput() {
    var username = document.getElementById('username').value;
    var password = document.getElementById('password').value;
    var loginButton = document.getElementById('loginButton');

    loginButton.disabled = !(username.trim() !== '' && password.trim() !== '');
}

function login() {
    var username = document.getElementById('username').value;
    var password = document.getElementById('password').value;

    alert('Login button clicked!');

    document.getElementById('loginForm').reset();
}
