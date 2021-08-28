// encrypt on submit
$('#sensitive').submit((event) => {
    event.preventDefault()  // prevents form submission before encryption
    RSAEncrypt()
})

function encryptForm(crypto) {
    switch(window.location.pathname) {
        case '/login/':
            encryptLogin(crypto)
            break
        case '/register/':
            encryptRegistration(crypto)
            break
        case '/user/manage/':
            encryptManage(crypto)
            break
    }
}

function RSAEncrypt() {
    // retrieve public key from server
    const xhttp = new XMLHttpRequest()

    xhttp.open('PUT', `${window.location.origin}/key/`)
    xhttp.setRequestHeader('X-CSRFToken', shortcuts.getCSRFToken())
    
    xhttp.onreadystatechange = () => {
        if(xhttp.readyState == 4) {
            // key retrieved, encrypt credentials
            const crypto = new JSEncrypt()
            crypto.setKey(xhttp.response)
            encryptForm(crypto)

            // submit form
            document.getElementById('sensitive').submit()
        }
    }
    xhttp.send()
}

function encryptLogin(crypto) {
    const password = document.getElementsByName('password')[0]
    password.value = crypto.encrypt(password.value)
}

function encryptRegistration(crypto) {
    const password1 = document.getElementsByName('password1')[0]
    password1.value = crypto.encrypt(password1.value)

    const password2 = document.getElementsByName('password2')[0]
    password2.value = crypto.encrypt(password2.value)
}

function encryptManage(crypto) {
    const oldPassword = document.getElementsByName('old_password')[0]
    oldPassword.value = crypto.encrypt(oldPassword.value)

    const newPassword1 = document.getElementsByName('new_password1')[0]
    newPassword1.value = crypto.encrypt(newPassword1.value)
    
    const newPassword2 = document.getElementsByName('new_password2')[0]
    newPassword2.value = crypto.encrypt(newPassword2.value)
}
